"""
Decision Engine

Analyzes test results and generates decision recommendations.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .models import (
    FailureCategory,
    ActionType,
    Decision,
    ConvergenceStatus,
    AnalysisReport,
    Failure,
    ResultAnalyzerConfig,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """决策引擎"""

    # 决策规则阈值
    MAX_ITERATIONS = 5
    MIN_PASS_RATE_IMPROVEMENT = 0.05
    CONFIDENCE_THRESHOLD = 0.8

    def __init__(self, config: ResultAnalyzerConfig):
        self.config = config

    def evaluate(
        self,
        current_report: AnalysisReport,
        history: List[AnalysisReport],
        iteration: int
    ) -> Decision:
        """
        评估当前状态并生成决策

        Args:
            current_report: 当前分析报告
            history: 历史报告列表
            iteration: 当前迭代次数

        Returns:
            Decision: 决策结果
        """
        # 检查收敛性
        convergence = self._check_convergence(current_report, history, iteration)

        if convergence.converged:
            return Decision(
                action=ActionType.FINISH,
                confidence=1.0,
                rationale=f"Converged after {iteration} iterations. {convergence.summary}",
                suggested_changes=[],
                additional_tests=[]
            )

        # 分析失败模式
        decision = self._analyze_and_decide(current_report, history, iteration)

        # 添加收敛信息
        decision.confidence = min(decision.confidence, convergence.pass_rate)

        return decision

    def _analyze_and_decide(
        self,
        current_report: AnalysisReport,
        history: List[AnalysisReport],
        iteration: int
    ) -> Decision:
        """分析失败并决定下一步行动"""
        # 获取历史趋势
        trend = self._get_trend(history)

        # 分析失败类型分布
        failure_analysis = self._analyze_failure_types(current_report.failures)

        # 决策逻辑
        if iteration >= self.MAX_ITERATIONS:
            return Decision(
                action=ActionType.ESCALATE,
                confidence=0.9,
                rationale=f"Reached maximum iterations ({self.MAX_ITERATIONS}). Human review needed.",
                suggested_changes=["Manual code review required"],
                additional_tests=["Full regression test suite"]
            )

        if failure_analysis['memory_errors'] > 0:
            return Decision(
                action=ActionType.MODIFY_APPROACH,
                confidence=0.85,
                rationale="Memory errors detected. Consider memory safety fixes.",
                suggested_changes=[
                    "Check for buffer overflows",
                    "Review memory allocation/deallocation",
                    "Consider using static analysis tools"
                ],
                additional_tests=["Valgrind memory check"]
            )

        if failure_analysis['compilation_errors'] > 0:
            return Decision(
                action=ActionType.MODIFY_APPROACH,
                confidence=0.9,
                rationale="Compilation errors found. Fix build issues first.",
                suggested_changes=[
                    "Resolve undefined references",
                    "Fix syntax errors",
                    "Update include paths"
                ],
                additional_tests=["Build verification test"]
            )

        if failure_analysis['assertion_failures'] > 0:
            return Decision(
                action=ActionType.MODIFY_APPROACH,
                confidence=0.8,
                rationale="Assertion failures detected. Review test expectations.",
                suggested_changes=[
                    "Check assertion conditions",
                    "Verify expected behavior",
                    "Update test cases if needed"
                ],
                additional_tests=["Unit tests for affected functions"]
            )

        if trend == 'degrading':
            return Decision(
                action=ActionType.MODIFY_APPROACH,
                confidence=0.75,
                rationale="Pass rate is degrading. Current strategy may be ineffective.",
                suggested_changes=["Re-evaluate the fix approach"],
                additional_tests=["Baseline comparison test"]
            )

        if trend == 'improving':
            return Decision(
                action=ActionType.CONTINUE,
                confidence=0.85,
                rationale="Pass rate is improving. Continue with current strategy.",
                suggested_changes=[],
                additional_tests=["Continue current test plan"]
            )

        # 默认：继续
        return Decision(
            action=ActionType.CONTINUE,
            confidence=0.7,
            rationale="No clear trend. Continuing with current approach.",
            suggested_changes=[],
            additional_tests=[]
        )

    def _analyze_failure_types(self, failures: List[Failure]) -> Dict[str, int]:
        """分析失败类型分布"""
        analysis = {
            'memory_errors': 0,
            'compilation_errors': 0,
            'assertion_failures': 0,
            'runtime_errors': 0,
            'timeout_errors': 0,
            'crashes': 0,
            'unknown': 0
        }

        for failure in failures:
            if failure.category == FailureCategory.MEMORY_ERROR:
                analysis['memory_errors'] += 1
            elif failure.category == FailureCategory.COMPILATION_ERROR:
                analysis['compilation_errors'] += 1
            elif failure.category == FailureCategory.ASSERTION_FAILURE:
                analysis['assertion_failures'] += 1
            elif failure.category == FailureCategory.RUNTIME_ERROR:
                analysis['runtime_errors'] += 1
            elif failure.category == FailureCategory.TIMEOUT:
                analysis['timeout_errors'] += 1
            elif failure.category == FailureCategory.CRASH:
                analysis['crashes'] += 1
            else:
                analysis['unknown'] += 1

        return analysis

    def _get_trend(self, history: List[AnalysisReport]) -> str:
        """获取通过率趋势"""
        if len(history) < 2:
            return 'stable'

        rates = [r.pass_rate for r in history[-5:]]  # 最近5次

        if len(rates) < 2:
            return 'stable'

        # 计算趋势
        recent_avg = sum(rates[-2:]) / 2
        older_avg = sum(rates[:-2]) / len(rates[:-2]) if len(rates) > 2 else rates[0]

        if recent_avg - older_avg > self.MIN_PASS_RATE_IMPROVEMENT:
            return 'improving'
        elif older_avg - recent_avg > self.MIN_PASS_RATE_IMPROVEMENT:
            return 'degrading'
        else:
            return 'stable'

    def _check_convergence(
        self,
        current_report: AnalysisReport,
        history: List[AnalysisReport],
        iteration: int
    ) -> ConvergenceStatus:
        """检查收敛状态"""
        pass_rate = current_report.pass_rate

        # 检查是否所有测试通过
        if pass_rate == 1.0:
            return ConvergenceStatus(
                converged=True,
                iteration=iteration,
                pass_rate=pass_rate,
                trend='stable',
                remaining_failures=0,
                summary="All tests passed. Converged!"
            )

        # 检查是否达到最大迭代次数
        if iteration >= self.MAX_ITERATIONS:
            return ConvergenceStatus(
                converged=False,
                iteration=iteration,
                pass_rate=pass_rate,
                trend=self._get_trend(history),
                remaining_failures=current_report.failed,
                summary=f"Max iterations reached with {current_report.failed} failures remaining"
            )

        # 检查是否连续无改进
        if len(history) >= 3:
            recent_rates = [r.pass_rate for r in history[-3:]]
            if max(recent_rates) - min(recent_rates) < 0.01:
                return ConvergenceStatus(
                    converged=False,
                    iteration=iteration,
                    pass_rate=pass_rate,
                    trend='stable',
                    remaining_failures=current_report.failed,
                    summary=f"No improvement in last 3 iterations. Consider changing strategy."
                )

        # 默认：未收敛
        return ConvergenceStatus(
            converged=False,
            iteration=iteration,
            pass_rate=pass_rate,
            trend=self._get_trend(history),
            remaining_failures=current_report.failed,
            summary=f"Running... {current_report.failed} failures remaining"
        )

    def calculate_confidence(
        self,
        decision: Decision,
        report: AnalysisReport,
        history: List[AnalysisReport]
    ) -> float:
        """计算决策置信度"""
        base_confidence = decision.confidence

        # 根据失败数量调整
        if report.failed == 0:
            return 1.0

        # 根据历史一致性调整
        if len(history) >= 2:
            last_rate = history[-1].pass_rate if history else 0
            current_rate = report.pass_rate
            rate_change = abs(current_rate - last_rate)

            if rate_change < 0.05:
                base_confidence *= 0.9  # 稳定状态，置信度稍低
            else:
                base_confidence *= 1.1  # 有变化，置信度稍高

        return min(1.0, base_confidence)
