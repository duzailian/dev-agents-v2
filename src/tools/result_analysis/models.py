"""
Result Analysis Data Models

Defines all data classes for test result analysis and decision-making.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class FailureCategory(Enum):
    """失败分类"""
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    ASSERTION_FAILURE = "assertion_failure"
    TIMEOUT = "timeout"
    CRASH = "crash"
    MEMORY_ERROR = "memory_error"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """决策动作类型"""
    CONTINUE = "continue"       # 继续当前修复策略
    MODIFY_APPROACH = "modify"  # 调整修复策略
    RETRY = "retry"             # 重试测试
    ESCALATE = "escalate"       # 升级人工介入
    FINISH = "finish"           # 完成任务


@dataclass
class ResultAnalyzerConfig:
    """分析器配置"""
    llm_model: str = "gpt-4"
    confidence_threshold: float = 0.8
    max_history_depth: int = 10
    enable_ai_analysis: bool = True
    pattern_db_path: Optional[str] = None


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str = ""
    level: str = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR", "FATAL"
    source: str = ""
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Failure:
    """失败信息"""
    failure_id: str = ""
    test_id: str = ""
    category: FailureCategory = FailureCategory.UNKNOWN
    message: str = ""
    stack_trace: Optional[str] = None
    location: Optional[str] = None
    related_logs: List[LogEntry] = field(default_factory=list)

    def __post_init__(self):
        if not self.failure_id:
            self.failure_id = f"fail_{uuid.uuid4().hex[:8]}"


@dataclass
class RootCauseReport:
    """根因分析报告"""
    failure_id: str = ""
    root_cause: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    suggested_fix: str = ""
    related_knowledge: List[str] = field(default_factory=list)


@dataclass
class Decision:
    """决策结果"""
    action: ActionType = ActionType.CONTINUE
    confidence: float = 0.0
    rationale: str = ""
    suggested_changes: List[str] = field(default_factory=list)
    additional_tests: List[str] = field(default_factory=list)


@dataclass
class ConvergenceStatus:
    """收敛状态"""
    converged: bool = False
    iteration: int = 0
    pass_rate: float = 0.0
    trend: str = "stable"  # "improving", "stable", "degrading"
    remaining_failures: int = 0
    summary: str = ""


@dataclass
class AnalysisReport:
    """分析报告"""
    report_id: str = ""
    timestamp: str = ""
    test_run_id: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: List[Failure] = field(default_factory=list)
    root_cause_reports: List[RootCauseReport] = field(default_factory=list)
    decision: Optional[Decision] = None
    convergence: Optional[ConvergenceStatus] = None
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.report_id:
            self.report_id = f"report_{uuid.uuid4().hex[:8]}"
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_tests if self.total_tests > 0 else 0.0

    def generate_summary(self) -> str:
        """生成报告摘要"""
        rate = self.pass_rate * 100
        return (
            f"Tests: {self.total_tests} | Passed: {self.passed} | "
            f"Failed: {self.failed} | Skipped: {self.skipped}\n"
            f"Pass Rate: {rate:.1f}%\n"
            f"Failures: {len(self.failures)} identified"
        )
