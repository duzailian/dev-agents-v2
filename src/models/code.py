from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class WorkflowAction(Enum):
    """工作流动作枚举 - 标准化 next_action 字段的可能值

    用于确保状态机中 next_action 字段的一致性和类型安全。
    与 STATE_MACHINE.md 中定义的状态转移规则对应。
    """
    # 分析阶段动作
    ANALYZE = "analyze"              # 分析代码/日志/错误
    GENERATE_PATCH = "generate_patch"  # 生成补丁

    # 继续控制动作
    CONTINUE = "continue"            # 继续下一次迭代
    FINISH = "finish"                # 任务成功完成
    FAILURE = "failure"              # 任务失败终止
    ESCALATE = "escalate"            # 升级/人工介入

    # 补丁相关动作
    REVIEW_PATCH = "review_patch"    # 审查生成的补丁
    APPLY_PATCH = "apply_patch"      # 应用补丁

    # 恢复动作
    RETRY = "retry"                  # 重试当前操作
    ROLLBACK = "rollback"            # 回滚更改

    # 测试动作
    RUN_TEST = "run_test"            # 执行测试
    SETUP_ENV = "setup_env"          # 设置测试环境

    # 知识库动作
    RETRIEVE_KNOWLEDGE = "retrieve_knowledge"  # 检索知识库
    CAPTURE_KNOWLEDGE = "capture_knowledge"    # 沉淀知识


class WorkflowState(Enum):
    """工作流状态枚举 - LangGraph 节点名称的标准化

    用于编译时验证状态机节点名称的正确性。
    值对应 src/orchestrator/graph.py 中定义的节点名称。

    与 STATE_MACHINE.md 中的 UPPER_SNAKE_CASE 状态名对应：
    - snake_case: code_analysis (本枚举)
    - UPPER_SNAKE_CASE: CODE_ANALYSIS (设计文档)
    """

    # 核心流程状态
    INITIALIZE = "initialize"              # 初始化
    CODE_ANALYSIS = "code_analysis"        # 代码分析
    PATCH_GENERATION = "patch_generation"  # 补丁生成
    PATCH_APPLICATION = "patch_application"  # 补丁应用
    BUILD_SETUP = "build_setup"            # 构建准备
    BUILD_RUN = "build_run"                # 构建执行
    TEST_SETUP = "test_setup"              # 测试准备
    TEST_EXECUTION = "test_execution"      # 测试执行
    RESULT_COLLECTION = "result_collection"  # 结果采集
    RESULT_ANALYSIS = "result_analysis"    # 结果分析
    CONVERGENCE_CHECK = "convergence_check"  # 收敛检查

    # 知识库状态
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # 知识检索
    KNOWLEDGE_CAPTURE = "knowledge_capture"      # 知识沉淀

    # 错误恢复
    ERROR_RECOVERY = "error_recovery"      # 错误恢复

    # 终止状态
    SUCCESS = "success"                    # 成功完成
    FAILURE = "failure"                    # 失败终止
    ESCALATE = "escalate"                  # 升级/人工介入


class AnalysisType(Enum):
    """分析类型枚举"""
    STRUCTURE = "structure"      # 结构分析
    DEPENDENCY = "dependency"    # 依赖分析
    METRICS = "metrics"          # 度量分析
    STATIC = "static"            # 静态检查
    SEMANTIC = "semantic"        # 语义分析
    AI = "ai"                    # AI分析
    FULL = "full"                # 完整分析

class IssueSeverity(Enum):
    """问题严重性 - 映射到字符串"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

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
