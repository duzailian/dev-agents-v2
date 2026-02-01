"""
Result Analyzer

Main analyzer for test results, providing:
- Multi-format log parsing
- Error pattern matching
- Root cause analysis
- Decision recommendation
- Convergence detection
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .models import (
    FailureCategory,
    ActionType,
    ResultAnalyzerConfig,
    LogEntry,
    Failure,
    RootCauseReport,
    Decision,
    ConvergenceStatus,
    AnalysisReport,
)
from .log_parser import LogParser
from .decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class PatternMatcher:
    """错误模式匹配器"""

    # 内置错误模式库
    BUILTIN_PATTERNS = {
        FailureCategory.MEMORY_ERROR: [
            r'segmentation fault',
            r'segfault',
            r'double free',
            r'heap-buffer-overflow',
            r'use-after-free',
            r'memory leak',
            r'invalid write',
            r'invalid read',
        ],
        FailureCategory.ASSERTION_FAILURE: [
            r'assertion.*failed',
            r'assert\s*\(.*\)\s*failed',
            r'ASSERT_.*failed',
            r'assertion failed',
            r'Test.*failed',
            r'test.*FAILED',
        ],
        FailureCategory.COMPILATION_ERROR: [
            r'error:.*undefined reference',
            r'error:.*undeclared',
            r'fatal error:.*no such file',
            r'cannot find',
            r'undefined symbol',
            r'linker error',
        ],
        FailureCategory.TIMEOUT: [
            r'timeout',
            r'timed out',
            r'watchdog.*expired',
            r'execution timed out',
        ],
        FailureCategory.CRASH: [
            r'kernel panic',
            r'oops',
            r'BUG:',
            r'core dumped',
            r'segmentation fault',
            r'aborted',
            r'crashed',
        ],
        FailureCategory.RUNTIME_ERROR: [
            r'runtime error',
            r'unhandled exception',
            r'floating point exception',
            r'division by zero',
        ],
    }

    def __init__(self, pattern_db_path: Optional[str] = None):
        self.patterns = self.BUILTIN_PATTERNS.copy()
        if pattern_db_path:
            self._load_custom_patterns(pattern_db_path)

    def _load_custom_patterns(self, pattern_db_path: str):
        """加载自定义模式"""
        try:
            path = Path(pattern_db_path)
            if path.exists():
                import json
                custom = json.loads(path.read_text())
                for category, patterns in custom.items():
                    try:
                        cat = FailureCategory(category)
                        if cat not in self.patterns:
                            self.patterns[cat] = []
                        self.patterns[cat].extend(patterns)
                    except ValueError:
                        logger.warning(f"Unknown failure category in pattern DB: {category}")
        except Exception as e:
            logger.error(f"Failed to load custom patterns: {e}")

    def classify(self, message: str) -> Tuple[FailureCategory, float]:
        """
        对错误信息进行分类

        Args:
            message: 错误消息

        Returns:
            Tuple[FailureCategory, float]: (分类, 置信度)
        """
        if not message:
            return (FailureCategory.UNKNOWN, 0.0)

        best_match = (FailureCategory.UNKNOWN, 0.0)
        message_lower = message.lower()

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # 计算匹配分数
                    score = len(pattern) / len(message) if message else 0
                    # 对更长的模式给予更高分数
                    score = min(score * 1.5, 1.0)
                    if score > best_match[1]:
                        best_match = (category, score)

        return best_match

    def find_similar(self, message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查找相似失败模式"""
        results = []
        category, score = self.classify(message)

        if category != FailureCategory.UNKNOWN:
            results.append({
                'category': category.value,
                'confidence': score,
                'type': 'pattern_match'
            })

        return results[:limit]


class RootCauseAnalyzer:
    """根因分析器"""

    # 常见根因模式
    ROOT_CAUSE_PATTERNS = {
        'null_pointer': {
            'patterns': [r'null pointer', r'NULL', r'nullptr', r'segfault.*0x0'],
            'causes': [
                'Uninitialized pointer',
                'Pointer freed but still used',
                'API returned NULL on error'
            ]
        },
        'buffer_overflow': {
            'patterns': [r'buffer overflow', r'out of bounds', r'invalid write'],
            'causes': [
                'Array index out of bounds',
                'String buffer not properly sized',
                'Copy without length check'
            ]
        },
        'race_condition': {
            'patterns': [r'race condition', r'concurrent', r'thread.*safe'],
            'causes': [
                'Unprotected shared resource access',
                'Lock ordering issue',
                'Missing synchronization'
            ]
        },
        'resource_leak': {
            'patterns': [r'memory leak', r'resource.*leak', r'not freed'],
            'causes': [
                'Missing cleanup in error path',
                'Exception before cleanup',
                'Dynamic allocation without deallocation'
            ]
        }
    }

    def __init__(self, config: ResultAnalyzerConfig):
        self.config = config

    def analyze(
        self,
        failure: Failure,
        code_context: Optional[str] = None
    ) -> RootCauseReport:
        """
        分析失败根因

        Args:
            failure: 失败信息
            code_context: 相关代码上下文

        Returns:
            RootCauseReport: 根因分析报告
        """
        evidence = []
        suggested_fix = ""

        # 模式匹配分析
        category, confidence = self._analyze_category(failure)

        # 基于类别进行根因分析
        if failure.category == FailureCategory.MEMORY_ERROR:
            evidence, suggested_fix = self._analyze_memory_issue(failure)
        elif failure.category == FailureCategory.COMPILATION_ERROR:
            evidence, suggested_fix = self._analyze_compilation_issue(failure)
        elif failure.category == FailureCategory.ASSERTION_FAILURE:
            evidence, suggested_fix = self._analyze_assertion_issue(failure)
        elif failure.category == FailureCategory.TIMEOUT:
            evidence, suggested_fix = self._analyze_timeout_issue(failure)
        elif failure.category == FailureCategory.CRASH:
            evidence, suggested_fix = self._analyze_crash_issue(failure)
        else:
            evidence = [f"Failure category: {failure.category.value}"]
            suggested_fix = "Review code for potential issues in the affected area"

        root_cause = self._synthesize_root_cause(failure, evidence)

        return RootCauseReport(
            failure_id=failure.failure_id,
            root_cause=root_cause,
            confidence=confidence,
            evidence=evidence,
            suggested_fix=suggested_fix
        )

    def _analyze_category(self, failure: Failure) -> Tuple[FailureCategory, float]:
        """分析失败类别"""
        matcher = PatternMatcher()
        return matcher.classify(failure.message)

    def _analyze_memory_issue(self, failure: Failure) -> Tuple[List[str], str]:
        """分析内存相关问题"""
        evidence = ["Memory error detected in test output"]
        causes = self.ROOT_CAUSE_PATTERNS.get('null_pointer', {}).get('causes', [])

        if 'segfault' in failure.message.lower():
            evidence.append("Segmentation fault indicates memory access violation")
            if causes:
                evidence.append(f"Possible cause: {causes[0]}")

        return evidence, "Review memory allocation and pointer usage. Add null checks."

    def _analyze_compilation_issue(self, failure: Failure) -> Tuple[List[str], str]:
        """分析编译问题"""
        evidence = ["Compilation failed"]
        msg = failure.message.lower()

        if 'undefined reference' in msg:
            evidence.append("Linker cannot find symbol definition")
            return evidence, "Ensure all required files are compiled and linked. Check library dependencies."

        if 'undeclared' in msg:
            evidence.append("Variable or function used without declaration")
            return evidence, "Add missing include or forward declaration."

        return evidence, "Fix compilation errors before proceeding."

    def _analyze_assertion_issue(self, failure: Failure) -> Tuple[List[str], str]:
        """分析断言失败"""
        evidence = ["Assertion failed during test execution"]
        msg = failure.message

        evidence.append(f"Assertion message: {msg[:100]}")

        return evidence, "Review assertion conditions. Verify expected behavior matches implementation."

    def _analyze_timeout_issue(self, failure: Failure) -> Tuple[List[str], str]:
        """分析超时问题"""
        evidence = ["Test execution timed out"]

        if 'watchdog' in failure.message.lower():
            evidence.append("Watchdog timer expired - system hung")

        return evidence, "Check for infinite loops. Review performance of affected code paths."

    def _analyze_crash_issue(self, failure: Failure) -> Tuple[List[str], str]:
        """分析崩溃问题"""
        evidence = ["System/application crashed"]
        msg = failure.message.lower()

        if 'kernel panic' in msg:
            evidence.append("Kernel panic - critical system error")
            return evidence, "Review kernel code for critical paths. Check hardware compatibility."

        if 'core dumped' in msg:
            evidence.append("Core dump generated - application crashed")
            return evidence, "Analyze core dump to identify crash location. Check for null pointers."

        return evidence, "Review crash logs and stack trace for root cause."

    def _synthesize_root_cause(self, failure: Failure, evidence: List[str]) -> str:
        """综合根因分析"""
        if not evidence:
            return "Unknown root cause"

        # 提取关键信息
        key_points = evidence[:3]  # 取前3条证据

        return f"Root cause analysis based on {len(evidence)} evidence points: {'; '.join(key_points)}"


class ResultAnalyzer:
    """
    结果分析引擎主类

    负责分析测试结果并生成决策，支持：
    - 多格式日志解析
    - 错误模式识别
    - AI辅助根因分析
    - 决策建议生成
    - 收敛性判断
    """

    def __init__(self, config: Optional[ResultAnalyzerConfig] = None):
        """
        初始化分析器

        Args:
            config: 分析器配置（可选，使用默认配置）
        """
        self.config = config or ResultAnalyzerConfig()
        self.log_parser = LogParser()
        self.pattern_matcher = PatternMatcher(self.config.pattern_db_path)
        self.root_cause_analyzer = RootCauseAnalyzer(self.config)
        self.decision_engine = DecisionEngine(self.config)

        logger.info(f"ResultAnalyzer initialized with config: {self.config}")

    def analyze_results(
        self,
        test_run_id: str,
        total_tests: int,
        passed: int,
        failed: int,
        skipped: int,
        test_outputs: Optional[Dict[str, str]] = None,
        iteration: int = 0,
        history: Optional[List[AnalysisReport]] = None
    ) -> AnalysisReport:
        """
        分析测试结果

        Args:
            test_run_id: 测试运行ID
            total_tests: 总测试数
            passed: 通过数
            failed: 失败数
            skipped: 跳过数
            test_outputs: 测试输出字典 {test_id: output}
            iteration: 当前迭代次数
            history: 历史分析报告

        Returns:
            AnalysisReport: 分析报告
        """
        # 解析测试输出，识别失败
        failures = self._identify_failures(test_outputs, failed)

        # 生成根因报告
        root_cause_reports = []
        for failure in failures:
            report = self.root_cause_analyzer.analyze(failure)
            root_cause_reports.append(report)

        # 创建分析报告
        report = AnalysisReport(
            test_run_id=test_run_id,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            failures=failures,
            root_cause_reports=root_cause_reports
        )
        report.summary = report.generate_summary()

        # 生成决策
        history = history or []
        decision = self.decision_engine.evaluate(report, history, iteration)
        report.decision = decision

        # 检查收敛性
        convergence = self.decision_engine._check_convergence(report, history, iteration)
        report.convergence = convergence

        # 添加建议
        report.recommendations = self._generate_recommendations(report, decision)

        return report

    def parse_logs(self, log_paths: List[str]) -> List[LogEntry]:
        """
        解析日志文件

        Args:
            log_paths: 日志文件路径列表

        Returns:
            List[LogEntry]: 解析后的日志条目
        """
        all_entries = []

        for path in log_paths:
            try:
                p = Path(path)
                if p.exists():
                    content = p.read_text()
                    entries = self.log_parser.parse(content)
                    all_entries.extend(entries)
                    logger.info(f"Parsed {len(entries)} entries from {path}")
            except Exception as e:
                logger.error(f"Failed to parse log {path}: {e}")

        return all_entries

    def identify_failures_from_logs(
        self,
        logs: List[LogEntry],
        test_mapping: Optional[Dict[str, str]] = None
    ) -> List[Failure]:
        """从日志识别失败"""
        failures = []
        error_entries = self.log_parser.extract_errors(logs)

        for entry in error_entries:
            category, confidence = self.pattern_matcher.classify(entry.message)

            failure = Failure(
                test_id=test_mapping.get(entry.source, entry.source) if test_mapping else entry.source,
                category=category,
                message=entry.message,
                stack_trace=entry.context.get('stack_trace'),
                location=entry.context.get('location'),
                related_logs=[entry]
            )
            failures.append(failure)

        return failures

    def _identify_failures(
        self,
        test_outputs: Optional[Dict[str, str]],
        expected_count: int
    ) -> List[Failure]:
        """识别测试失败"""
        failures = []

        if not test_outputs:
            # 如果没有输出但有失败数，生成通用失败
            for i in range(expected_count):
                failures.append(Failure(
                    test_id=f"test_{i}",
                    category=FailureCategory.UNKNOWN,
                    message="Test execution failed (no output captured)"
                ))
            return failures

        for test_id, output in test_outputs.items():
            if not output:
                failures.append(Failure(
                    test_id=test_id,
                    category=FailureCategory.UNKNOWN,
                    message="No output from test"
                ))
                continue

            # 分析输出
            category, confidence = self.pattern_matcher.classify(output)

            if category != FailureCategory.UNKNOWN or 'fail' in output.lower():
                failures.append(Failure(
                    test_id=test_id,
                    category=category,
                    message=output[:500] if len(output) > 500 else output
                ))

        return failures

    def _generate_recommendations(
        self,
        report: AnalysisReport,
        decision: Decision
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if decision.action == ActionType.MODIFY_APPROACH:
            recommendations.append("Current fix strategy may need adjustment")
            recommendations.extend(decision.suggested_changes)

        if decision.action == ActionType.ESCALATE:
            recommendations.append("Human review recommended")
            recommendations.append("Manual debugging may be required")

        if report.convergence and not report.convergence.converged:
            if report.convergence.trend == 'degrading':
                recommendations.append("Consider rolling back recent changes")

        # 基于失败类型添加建议
        failure_types = {}
        for failure in report.failures:
            cat = failure.category.value
            failure_types[cat] = failure_types.get(cat, 0) + 1

        for cat, count in failure_types.items():
            if cat == FailureCategory.MEMORY_ERROR.value:
                recommendations.append("Consider using memory sanitizers (ASan, MSan)")
            elif cat == FailureCategory.COMPILATION_ERROR.value:
                recommendations.append("Ensure build system is correctly configured")

        return recommendations

    def check_convergence(
        self,
        history: List[AnalysisReport]
    ) -> ConvergenceStatus:
        """检查收敛性"""
        if not history:
            return ConvergenceStatus(converged=False, iteration=0, pass_rate=0.0)

        current = history[-1]
        return self.decision_engine._check_convergence(current, history, len(history))
