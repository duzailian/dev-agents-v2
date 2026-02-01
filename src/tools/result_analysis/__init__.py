"""
Result Analysis Module

Provides test result analysis and decision-making capabilities:
- Multi-format log parsing
- Error pattern matching
- Root cause analysis
- Decision recommendation
- Convergence detection
"""

from .analyzer import ResultAnalyzer
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

__all__ = [
    "ResultAnalyzer",
    "FailureCategory",
    "ActionType",
    "ResultAnalyzerConfig",
    "LogEntry",
    "Failure",
    "RootCauseReport",
    "Decision",
    "ConvergenceStatus",
    "AnalysisReport",
]
