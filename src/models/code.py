from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class IssueType(Enum):
    """问题类型"""
    MEMORY_LEAK = "memory_leak"
    NULL_POINTER = "null_pointer"
    BUFFER_OVERFLOW = "buffer_overflow"
    RACE_CONDITION = "race_condition"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ISSUE = "performance_issue"
    CODE_SMELL = "code_smell"
    STYLE_VIOLATION = "style_violation"
    COMPILATION_ERROR = "compilation_error"
    UNKNOWN = "unknown"

class IssueSeverity(Enum):
    """问题严重性"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class CodeLocation:
    """代码位置"""
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function_name: Optional[str] = None

@dataclass
class CodeIssue:
    """代码问题"""
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: IssueType = IssueType.UNKNOWN
    severity: IssueSeverity = IssueSeverity.INFO
    location: Optional[CodeLocation] = None
    title: str = ""
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    confidence: float = 0.0

@dataclass
class CodeMetrics:
    """代码度量"""
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    function_count: int = 0
    class_count: int = 0
    comment_ratio: float = 0.0
    test_coverage: Optional[float] = None

@dataclass
class CodeAnalysis:
    """代码分析结果"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_files: List[str] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    metrics: Optional[CodeMetrics] = None
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
