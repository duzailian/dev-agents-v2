from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class AnalysisType(Enum):
    """分析类型枚举"""
    STRUCTURE = "structure"      # 结构分析
    DEPENDENCY = "dependency"    # 依赖分析
    METRICS = "metrics"          # 度量分析
    STATIC = "static"            # 静态检查
    SEMANTIC = "semantic"        # 语义分析
    FULL = "full"                # 完整分析

class IssueSeverity(Enum):
    """问题严重性 - 映射到字符串"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Location:
    """代码位置"""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

@dataclass
class Issue:
    """静态分析问题"""
    rule_id: str
    severity: str  # "error", "warning", "info"
    message: str
    location: Location
    fix_suggestion: Optional[str] = None
    category: str = "general"

@dataclass
class CodeMetrics:
    """代码度量"""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    function_count: int = 0
    max_nesting_depth: int = 0
    maintainability_index: float = 0.0

@dataclass
class FunctionNode:
    """函数节点"""
    name: str
    location: Location
    return_type: str
    parameters: List[Dict[str, str]]
    body_start: int
    body_end: int
    complexity: int = 0
    is_static: bool = False
    is_inline: bool = False
    docstring: Optional[str] = None

@dataclass
class Symbol:
    """符号定义"""
    name: str
    kind: str  # "function", "variable", "type", "macro"
    location: Location
    scope: str
    type_info: Optional[str] = None

@dataclass
class DependencyGraph:
    """依赖关系图"""
    nodes: List[str] = field(default_factory=list)                      # 文件/模块列表
    edges: List[Dict[str, str]] = field(default_factory=list)           # 依赖边 {"from": ..., "to": ..., "type": ...}
    include_map: Dict[str, List[str]] = field(default_factory=dict)     # 头文件包含映射

@dataclass
class FileAnalysis:
    """单文件分析结果"""
    file_path: str
    language: str
    functions: List[FunctionNode] = field(default_factory=list)
    symbols: List[Symbol] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    metrics: Optional[CodeMetrics] = None
    issues: List[Issue] = field(default_factory=list)
    ast_hash: str = ""  # AST哈希用于缓存

@dataclass
class AnalysisReport:
    """分析报告"""
    task_id: str
    timestamp: str
    files_analyzed: List[str] = field(default_factory=list)
    file_analyses: List[FileAnalysis] = field(default_factory=list)
    dependency_graph: Optional[DependencyGraph] = None
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    summary: str = ""
    suggestions: List[str] = field(default_factory=list)

@dataclass
class AnalyzerConfig:
    """分析器配置"""
    languages: List[str] = field(default_factory=lambda: ["c", "cpp"])
    include_paths: List[str] = field(default_factory=list)
    compiler_flags: List[str] = field(default_factory=list)
    static_analyzers: List[str] = field(default_factory=list)
    llm_model: str = "gpt-4"
    llm_timeout: int = 60
    max_file_size: int = 1048576
    enable_caching: bool = True
