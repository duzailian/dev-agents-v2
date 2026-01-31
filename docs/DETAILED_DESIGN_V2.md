# AI驱动固件智能测试系统 — 详细设计 (DETAILED_DESIGN)

> 文档版本：v2.0
>
> 目标：定义系统核心模块的详细实现设计，包括类结构、接口规范、数据流和算法描述。
>
> **相关文档**：
> - Agent详细设计：[AGENT_DESIGN.md](AGENT_DESIGN.md)
> - 状态机设计：[STATE_MACHINE.md](STATE_MACHINE.md)
> - 系统架构：[ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)
> - 知识库Schema：[KNOWLEDGE_SCHEMA.md](KNOWLEDGE_SCHEMA.md)

---

## 1. 核心引擎详细设计 (Core Engines)

本章节定义四个核心引擎的详细设计规格，这些引擎是Agent节点的底层能力提供者。

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer (LangGraph)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │CodeAgent │  │TestAgent │  │Analysis  │  │ KBAgent  │        │
│  │  Node    │  │  Node    │  │  Agent   │  │  Node    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Engine Layer (Core Tools)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Code    │  │  Test    │  │  Result  │  │Knowledge │        │
│  │ Analyzer │  │Orchestr. │  │ Analyzer │  │  Base    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1.1 CodeAnalyzer (代码分析引擎)

**模块位置**：`src/tools/code_analysis/`

#### 1.1.1 职责定义

CodeAnalyzer负责对C/C++源代码进行静态分析，提取代码结构、依赖关系和潜在问题。

**核心职责**：
- 基于Tree-sitter解析C/C++代码生成AST
- 提取函数定义、变量声明、类型定义
- 构建符号表和调用图
- 集成静态分析工具（clang-tidy、cppcheck）
- 计算代码复杂度指标
- 提供AI辅助的代码理解能力

#### 1.1.2 类图设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        CodeAnalyzer                              │
├─────────────────────────────────────────────────────────────────┤
│ - config: AnalyzerConfig                                        │
│ - parser: TreeSitterParser                                      │
│ - symbol_table: SymbolTable                                     │
│ - call_graph: CallGraph                                         │
│ - static_analyzers: List[StaticAnalyzer]                        │
│ - llm_client: LLMClient                                         │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: AnalyzerConfig)                              │
│ + analyze_files(file_paths: List[str]) -> AnalysisReport        │
│ + analyze_single_file(file_path: str) -> FileAnalysis           │
│ + get_function_definitions(file_path: str) -> List[FunctionNode]│
│ + get_dependencies(file_path: str) -> DependencyGraph           │
│ + find_references(symbol: str, scope: str) -> List[Location]    │
│ + compute_metrics(file_path: str) -> CodeMetrics                │
│ + run_static_analysis(file_paths: List[str]) -> List[Issue]     │
│ + ai_understand_code(code_snippet: str, query: str) -> str      │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ TreeSitterParser│  │   SymbolTable   │  │   CallGraph     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ - language: Lang│  │ - symbols: Dict │  │ - nodes: Dict   │
│ - parser: Parser│  │ - scopes: Stack │  │ - edges: List   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + parse(code)   │  │ + add_symbol()  │  │ + add_call()    │
│ + get_ast()     │  │ + lookup()      │  │ + get_callers() │
│ + query(pattern)│  │ + get_scope()   │  │ + get_callees() │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 1.1.3 核心接口定义

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class AnalysisType(Enum):
    """分析类型枚举"""
    STRUCTURE = "structure"      # 结构分析
    DEPENDENCY = "dependency"    # 依赖分析
    METRICS = "metrics"          # 度量分析
    STATIC = "static"            # 静态检查
    SEMANTIC = "semantic"        # 语义分析
    FULL = "full"                # 完整分析

@dataclass
class AnalyzerConfig:
    """分析器配置"""
    languages: List[str] = None          # 支持的语言 ["c", "cpp"]
    include_paths: List[str] = None      # 头文件搜索路径
    compiler_flags: List[str] = None     # 编译器标志
    static_analyzers: List[str] = None   # 静态分析工具 ["clang-tidy", "cppcheck"]
    llm_model: str = "gpt-4"             # LLM模型
    llm_timeout: int = 60                # LLM超时时间
    max_file_size: int = 1048576         # 最大文件大小 (1MB)
    enable_caching: bool = True          # 启用缓存

@dataclass
class Location:
    """代码位置"""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

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
    lines_of_code: int
    lines_of_comments: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    function_count: int
    max_nesting_depth: int
    maintainability_index: float

@dataclass
class DependencyGraph:
    """依赖关系图"""
    nodes: List[str]                      # 文件/模块列表
    edges: List[Dict[str, str]]           # 依赖边 {"from": ..., "to": ..., "type": ...}
    include_map: Dict[str, List[str]]     # 头文件包含映射

@dataclass
class FileAnalysis:
    """单文件分析结果"""
    file_path: str
    language: str
    functions: List[FunctionNode]
    symbols: List[Symbol]
    includes: List[str]
    metrics: CodeMetrics
    issues: List[Issue]
    ast_hash: str  # AST哈希用于缓存

@dataclass
class AnalysisReport:
    """分析报告"""
    task_id: str
    timestamp: str
    files_analyzed: List[str]
    file_analyses: List[FileAnalysis]
    dependency_graph: DependencyGraph
    call_graph: Dict[str, List[str]]
    total_issues: int
    issues_by_severity: Dict[str, int]
    summary: str
    suggestions: List[str]


class CodeAnalyzer:
    """
    代码分析引擎主类

    基于Tree-sitter实现C/C++代码的静态分析，支持：
    - AST解析和遍历
    - 符号表构建
    - 调用图生成
    - 静态分析工具集成
    - AI辅助代码理解
    """

    def __init__(self, config: AnalyzerConfig):
        """
        初始化分析器

        Args:
            config: 分析器配置
        """
        self.config = config
        self.parser = self._init_parser()
        self.symbol_table = SymbolTable()
        self.call_graph = CallGraph()
        self.static_analyzers = self._init_static_analyzers()
        self.llm_client = self._init_llm_client()
        self._cache = {} if config.enable_caching else None

    def analyze_files(
        self,
        file_paths: List[str],
        analysis_type: AnalysisType = AnalysisType.FULL
    ) -> AnalysisReport:
        """
        分析多个文件

        Args:
            file_paths: 文件路径列表
            analysis_type: 分析类型

        Returns:
            AnalysisReport: 完整分析报告
        """
        pass

    def analyze_single_file(self, file_path: str) -> FileAnalysis:
        """
        分析单个文件

        Args:
            file_path: 文件路径

        Returns:
            FileAnalysis: 文件分析结果
        """
        pass

    def get_function_definitions(self, file_path: str) -> List[FunctionNode]:
        """
        提取文件中的函数定义

        Args:
            file_path: 文件路径

        Returns:
            List[FunctionNode]: 函数节点列表
        """
        pass

    def get_dependencies(self, file_path: str) -> DependencyGraph:
        """
        获取文件的依赖关系

        Args:
            file_path: 文件路径

        Returns:
            DependencyGraph: 依赖关系图
        """
        pass

    def find_references(
        self,
        symbol: str,
        scope: Optional[str] = None
    ) -> List[Location]:
        """
        查找符号的所有引用

        Args:
            symbol: 符号名称
            scope: 搜索范围（可选）

        Returns:
            List[Location]: 引用位置列表
        """
        pass

    def compute_metrics(self, file_path: str) -> CodeMetrics:
        """
        计算代码度量指标

        Args:
            file_path: 文件路径

        Returns:
            CodeMetrics: 代码度量结果
        """
        pass

    def run_static_analysis(self, file_paths: List[str]) -> List[Issue]:
        """
        运行静态分析工具

        Args:
            file_paths: 文件路径列表

        Returns:
            List[Issue]: 发现的问题列表
        """
        pass

    def ai_understand_code(
        self,
        code_snippet: str,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        使用AI理解代码

        Args:
            code_snippet: 代码片段
            query: 用户查询
            context: 额外上下文

        Returns:
            str: AI生成的解释
        """
        pass
```

#### 1.1.4 Tree-sitter集成

```python
class TreeSitterParser:
    """Tree-sitter解析器封装"""

    LANGUAGE_MAP = {
        "c": "tree-sitter-c",
        "cpp": "tree-sitter-cpp",
    }

    # C语言函数定义查询模式
    C_FUNCTION_QUERY = """
    (function_definition
      type: (_) @return_type
      declarator: (function_declarator
        declarator: (identifier) @name
        parameters: (parameter_list) @params)
      body: (compound_statement) @body) @function
    """

    # C语言函数调用查询模式
    C_CALL_QUERY = """
    (call_expression
      function: (identifier) @callee
      arguments: (argument_list) @args) @call
    """

    def __init__(self, language: str = "c"):
        """初始化解析器"""
        import tree_sitter_c as tsc
        from tree_sitter import Language, Parser

        self.language = Language(tsc.language())
        self.parser = Parser(self.language)
        self._queries = self._compile_queries()

    def parse(self, code: str) -> 'Tree':
        """解析代码生成AST"""
        return self.parser.parse(bytes(code, "utf8"))

    def query(self, tree: 'Tree', pattern: str) -> List[Dict]:
        """执行查询模式"""
        query = self.language.query(pattern)
        captures = query.captures(tree.root_node)
        return self._process_captures(captures)

    def extract_functions(self, tree: 'Tree') -> List[FunctionNode]:
        """提取函数定义"""
        results = self.query(tree, self.C_FUNCTION_QUERY)
        return [self._to_function_node(r) for r in results]

    def extract_calls(self, tree: 'Tree') -> List[Dict]:
        """提取函数调用"""
        return self.query(tree, self.C_CALL_QUERY)
```

#### 1.1.5 静态分析工具集成

```python
class StaticAnalyzerInterface(ABC):
    """静态分析器抽象接口"""

    @abstractmethod
    def analyze(self, file_paths: List[str]) -> List[Issue]:
        """执行分析"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """获取工具版本"""
        pass


class ClangTidyAnalyzer(StaticAnalyzerInterface):
    """clang-tidy集成"""

    DEFAULT_CHECKS = [
        "bugprone-*",
        "cert-*",
        "clang-analyzer-*",
        "modernize-*",
        "performance-*",
        "readability-*",
    ]

    def __init__(self, config: Dict[str, Any]):
        self.binary_path = config.get("binary_path", "clang-tidy")
        self.checks = config.get("checks", self.DEFAULT_CHECKS)
        self.compile_commands_dir = config.get("compile_commands_dir")

    def analyze(self, file_paths: List[str]) -> List[Issue]:
        """运行clang-tidy分析"""
        cmd = [
            self.binary_path,
            f"--checks={','.join(self.checks)}",
            "--export-fixes=-",
            "--format=json",
        ]
        if self.compile_commands_dir:
            cmd.append(f"-p={self.compile_commands_dir}")
        cmd.extend(file_paths)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_output(result.stdout)


class CppcheckAnalyzer(StaticAnalyzerInterface):
    """cppcheck集成"""

    def __init__(self, config: Dict[str, Any]):
        self.binary_path = config.get("binary_path", "cppcheck")
        self.std = config.get("std", "c11")
        self.enable = config.get("enable", ["all"])

    def analyze(self, file_paths: List[str]) -> List[Issue]:
        """运行cppcheck分析"""
        cmd = [
            self.binary_path,
            f"--std={self.std}",
            f"--enable={','.join(self.enable)}",
            "--template={file}:{line}:{column}: {severity}: {message} [{id}]",
            "--xml",
        ]
        cmd.extend(file_paths)

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self._parse_xml_output(result.stderr)
```

#### 1.1.6 代码度量算法

```python
class MetricsCalculator:
    """代码度量计算器"""

    def calculate_cyclomatic_complexity(self, ast_node) -> int:
        """
        计算圈复杂度

        算法：M = E - N + 2P
        - E: 边数（控制流图中的边）
        - N: 节点数
        - P: 连通分量数（通常为1）

        简化计算：统计决策点数量 + 1
        决策点：if, else if, for, while, case, &&, ||, ?:
        """
        decision_points = 0

        # 遍历AST统计决策点
        decision_node_types = [
            'if_statement',
            'for_statement',
            'while_statement',
            'do_statement',
            'case_statement',
            'conditional_expression',  # ?:
        ]

        for node in self._walk(ast_node):
            if node.type in decision_node_types:
                decision_points += 1
            # 统计逻辑运算符
            if node.type == 'binary_expression':
                op = self._get_operator(node)
                if op in ['&&', '||']:
                    decision_points += 1

        return decision_points + 1

    def calculate_cognitive_complexity(self, ast_node) -> int:
        """
        计算认知复杂度

        规则：
        1. 控制流结构增加复杂度（if, for, while等）
        2. 嵌套增加额外复杂度
        3. 某些结构打断线性流程
        """
        complexity = 0
        nesting_level = 0

        for node in self._walk(ast_node):
            if self._is_nesting_increment(node):
                nesting_level += 1
                complexity += nesting_level
            elif self._is_complexity_increment(node):
                complexity += 1
            elif self._is_nesting_decrement(node):
                nesting_level = max(0, nesting_level - 1)

        return complexity

    def calculate_maintainability_index(
        self,
        loc: int,
        cyclomatic: int,
        halstead_volume: float
    ) -> float:
        """
        计算可维护性指数

        公式：MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(L)
        - V: Halstead Volume
        - G: Cyclomatic Complexity
        - L: Lines of Code

        返回值范围：0-100（越高越好）
        """
        import math

        mi = 171 - 5.2 * math.log(halstead_volume + 1) \
             - 0.23 * cyclomatic \
             - 16.2 * math.log(loc + 1)

        # 归一化到0-100
        return max(0, min(100, mi * 100 / 171))
```

---

### 1.2 CodeModifier (代码修改引擎)

**模块位置**：`src/tools/code_modification/`

#### 1.2.1 职责定义

CodeModifier负责安全地修改C/C++代码，生成和应用补丁。

**核心职责**：
- 接收LLM生成的修改建议
- 生成标准Git Patch格式
- 执行修改前的安全检查
- 原子性地应用补丁
- 支持回滚和恢复

#### 1.2.2 类图设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        CodeModifier                              │
├─────────────────────────────────────────────────────────────────┤
│ - config: ModifierConfig                                        │
│ - patch_generator: PatchGenerator                               │
│ - safety_checker: SafetyChecker                                 │
│ - backup_manager: BackupManager                                 │
│ - git_client: GitClient                                         │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: ModifierConfig)                              │
│ + generate_patch(suggestion: ModifySuggestion) -> Patch         │
│ + apply_patch(patch: Patch, dry_run: bool) -> ApplyResult       │
│ + rollback(patch_id: str) -> bool                               │
│ + validate_modification(patch: Patch) -> ValidationResult       │
│ + create_backup(file_path: str) -> str                          │
│ + restore_backup(backup_id: str) -> bool                        │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ PatchGenerator  │  │  SafetyChecker  │  │  BackupManager  │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + generate()    │  │ + check_syntax()│  │ + create()      │
│ + format_diff() │  │ + check_compile │  │ + restore()     │
│ + parse_patch() │  │ + check_security│  │ + list()        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 1.2.3 核心接口定义

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ModifyStrategy(Enum):
    """修改策略"""
    MINIMAL = "minimal"          # 最小化修改
    FEATURE_ADD = "feature_add"  # 添加功能
    BUG_FIX = "bug_fix"          # Bug修复
    REFACTOR = "refactor"        # 重构
    OPTIMIZE = "optimize"        # 性能优化

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ModifierConfig:
    """修改器配置"""
    workspace_path: str                   # 工作区路径
    backup_dir: str = ".aft_backups"      # 备份目录
    max_backup_count: int = 10            # 最大备份数
    enable_syntax_check: bool = True      # 启用语法检查
    enable_compile_check: bool = True     # 启用编译检查
    enable_security_scan: bool = True     # 启用安全扫描
    compiler_path: str = "gcc"            # 编译器路径
    compiler_flags: List[str] = None      # 编译器标志
    auto_format: bool = True              # 自动格式化
    preserve_comments: bool = True        # 保留注释

@dataclass
class ModifySuggestion:
    """修改建议"""
    file_path: str
    description: str
    strategy: ModifyStrategy
    original_code: str
    modified_code: str
    start_line: int
    end_line: int
    rationale: str
    confidence: float  # 0.0 - 1.0

@dataclass
class Patch:
    """补丁对象"""
    patch_id: str
    file_path: str
    unified_diff: str
    description: str
    strategy: ModifyStrategy
    created_at: str
    applied: bool = False
    backup_id: Optional[str] = None

@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    syntax_ok: bool
    compile_ok: bool
    security_ok: bool
    errors: List[str]
    warnings: List[str]
    risk_level: RiskLevel

@dataclass
class ApplyResult:
    """应用结果"""
    success: bool
    patch_id: str
    backup_id: str
    files_modified: List[str]
    errors: List[str]
    rollback_available: bool


class CodeModifier:
    """
    代码修改引擎主类

    负责安全地修改C/C++代码，支持：
    - 基于LLM建议生成补丁
    - 多层安全验证
    - 原子性修改操作
    - 完整的回滚能力
    """

    def __init__(self, config: ModifierConfig):
        """初始化修改器"""
        self.config = config
        self.patch_generator = PatchGenerator()
        self.safety_checker = SafetyChecker(config)
        self.backup_manager = BackupManager(config.backup_dir)
        self.git_client = GitClient(config.workspace_path)

    def generate_patch(
        self,
        suggestion: ModifySuggestion
    ) -> Patch:
        """
        根据修改建议生成补丁

        Args:
            suggestion: 修改建议

        Returns:
            Patch: 生成的补丁对象
        """
        pass

    def apply_patch(
        self,
        patch: Patch,
        dry_run: bool = False
    ) -> ApplyResult:
        """
        应用补丁

        流程：
        1. 验证补丁
        2. 创建备份
        3. 应用修改
        4. 验证结果
        5. 提交或回滚

        Args:
            patch: 补丁对象
            dry_run: 是否为演练模式

        Returns:
            ApplyResult: 应用结果
        """
        pass

    def rollback(self, patch_id: str) -> bool:
        """
        回滚指定补丁

        Args:
            patch_id: 补丁ID

        Returns:
            bool: 回滚是否成功
        """
        pass

    def validate_modification(self, patch: Patch) -> ValidationResult:
        """
        验证修改的安全性

        检查项：
        1. 语法正确性
        2. 编译通过
        3. 安全扫描
        4. 风险评估

        Args:
            patch: 待验证的补丁

        Returns:
            ValidationResult: 验证结果
        """
        pass
```

#### 1.2.4 补丁生成算法

```python
class PatchGenerator:
    """补丁生成器"""

    def generate_unified_diff(
        self,
        original: str,
        modified: str,
        file_path: str,
        context_lines: int = 3
    ) -> str:
        """
        生成Unified Diff格式补丁

        输出格式：
        --- a/path/to/file.c
        +++ b/path/to/file.c
        @@ -start,count +start,count @@
         context line
        -removed line
        +added line
         context line
        """
        import difflib

        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=context_lines
        )

        return ''.join(diff)

    def parse_patch(self, patch_content: str) -> Dict[str, Any]:
        """解析补丁内容"""
        hunks = []
        current_hunk = None

        for line in patch_content.splitlines():
            if line.startswith('@@'):
                # 解析hunk头
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    current_hunk = {
                        'old_start': int(match.group(1)),
                        'old_count': int(match.group(2) or 1),
                        'new_start': int(match.group(3)),
                        'new_count': int(match.group(4) or 1),
                        'lines': []
                    }
                    hunks.append(current_hunk)
            elif current_hunk is not None:
                current_hunk['lines'].append(line)

        return {'hunks': hunks}
```

#### 1.2.5 安全检查机制

```python
class SafetyChecker:
    """安全检查器"""

    # 危险模式黑名单
    DANGEROUS_PATTERNS = [
        r'system\s*\(',           # system()调用
        r'exec[lv]?[pe]?\s*\(',   # exec系列
        r'popen\s*\(',            # popen()
        r'rm\s+-rf',              # 删除命令
        r'mkfs',                  # 格式化
        r'dd\s+if=',              # dd命令
        r'/dev/sd[a-z]',          # 直接设备访问
    ]

    def __init__(self, config: ModifierConfig):
        self.config = config
        self.compiler_path = config.compiler_path
        self.compiler_flags = config.compiler_flags or ["-Wall", "-Werror"]

    def check_syntax(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        检查语法正确性

        使用gcc -fsyntax-only进行检查
        """
        cmd = [
            self.compiler_path,
            "-fsyntax-only",
            *self.compiler_flags,
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        errors = []
        if result.returncode != 0:
            errors = result.stderr.splitlines()

        return result.returncode == 0, errors

    def check_compile(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        检查编译是否通过

        使用gcc -c进行编译检查
        """
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.o', delete=False) as f:
            output_path = f.name

        try:
            cmd = [
                self.compiler_path,
                "-c",
                *self.compiler_flags,
                "-o", output_path,
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            errors = []
            if result.returncode != 0:
                errors = result.stderr.splitlines()

            return result.returncode == 0, errors
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def check_security(self, code: str) -> Tuple[bool, List[str]]:
        """
        检查安全性问题

        检查是否包含危险模式
        """
        warnings = []

        for pattern in self.DANGEROUS_PATTERNS:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                warnings.append(f"Potentially dangerous pattern found: {pattern}")

        return len(warnings) == 0, warnings

    def assess_risk(self, patch: Patch) -> RiskLevel:
        """
        评估修改风险

        考虑因素：
        - 修改行数
        - 涉及的函数数量
        - 是否涉及内存操作
        - 是否涉及系统调用
        """
        lines_changed = len(patch.unified_diff.splitlines())

        # 高危模式检查
        high_risk_patterns = [
            r'malloc|free|realloc',  # 内存操作
            r'memcpy|memmove|strcpy', # 缓冲区操作
            r'open|close|read|write', # 文件操作
        ]

        risk_score = 0

        # 基于行数
        if lines_changed > 100:
            risk_score += 3
        elif lines_changed > 50:
            risk_score += 2
        elif lines_changed > 20:
            risk_score += 1

        # 基于危险模式
        for pattern in high_risk_patterns:
            if re.search(pattern, patch.unified_diff):
                risk_score += 2

        # 返回风险等级
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
```

---

### 1.3 TestOrchestrator (测试编排引擎)

**模块位置**：`src/executor/`

#### 1.3.1 职责定义

TestOrchestrator负责管理测试环境生命周期和测试执行流程。

**核心职责**：
- 管理多种测试环境（QEMU、目标板、BMC）
- 环境生命周期管理（启动、监控、停止）
- 测试用例调度和执行
- 测试结果和日志收集
- 资源池管理和并发控制

#### 1.3.2 类图设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      TestOrchestrator                            │
├─────────────────────────────────────────────────────────────────┤
│ - config: OrchestratorConfig                                    │
│ - env_manager: EnvironmentManager                               │
│ - test_runner: TestRunner                                       │
│ - artifact_collector: ArtifactCollector                         │
│ - resource_pool: ResourcePool                                   │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: OrchestratorConfig)                          │
│ + setup_environment(env_type: str) -> Environment               │
│ + run_test_plan(plan: TestPlan) -> TestResults                  │
│ + run_single_test(test: TestCase, env: Environment) -> Result   │
│ + collect_artifacts(task_id: str) -> List[Artifact]             │
│ + teardown_environment(env: Environment) -> bool                │
│ + get_environment_status(env_id: str) -> EnvironmentStatus      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EnvironmentManager                           │
├─────────────────────────────────────────────────────────────────┤
│ - adapters: Dict[str, EnvironmentAdapter]                       │
│ - active_envs: Dict[str, Environment]                           │
├─────────────────────────────────────────────────────────────────┤
│ + create_environment(config: EnvConfig) -> Environment          │
│ + destroy_environment(env_id: str) -> bool                      │
│ + get_adapter(env_type: str) -> EnvironmentAdapter              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  QEMUAdapter    │  │  BoardAdapter   │  │   BMCAdapter    │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + start()       │  │ + connect()     │  │ + power_on()    │
│ + stop()        │  │ + execute()     │  │ + power_off()   │
│ + execute()     │  │ + upload()      │  │ + get_console() │
│ + get_serial()  │  │ + download()    │  │ + get_sensors() │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 1.3.3 核心接口定义

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

class EnvironmentType(Enum):
    """环境类型"""
    QEMU = "qemu"
    BOARD = "board"
    BMC = "bmc"
    WINDOWS = "windows"

class EnvironmentStatus(Enum):
    """环境状态"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"

@dataclass
class OrchestratorConfig:
    """编排器配置"""
    workspace_dir: str
    artifact_dir: str
    max_concurrent_tests: int = 2
    default_timeout: int = 300
    retry_count: int = 3
    cleanup_on_finish: bool = True

@dataclass
class QEMUConfig:
    """QEMU环境配置"""
    binary_path: str
    machine: str = "virt"
    cpu: str = "cortex-a57"
    memory: str = "2G"
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None
    disk_path: Optional[str] = None
    network_enabled: bool = True
    serial_enabled: bool = True
    monitor_enabled: bool = True

@dataclass
class BoardConfig:
    """目标板环境配置"""
    ip_address: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None
    connection_timeout: int = 30

@dataclass
class BMCConfig:
    """BMC环境配置"""
    ip_address: str
    port: int = 623
    username: str
    password: str
    interface: str = "lanplus"

@dataclass
class TestCase:
    """测试用例"""
    test_id: str
    name: str
    description: str
    command: str
    expected_output: Optional[str] = None
    timeout: int = 60
    retries: int = 1
    prerequisites: List[str] = None
    tags: List[str] = None

@dataclass
class TestPlan:
    """测试计划"""
    plan_id: str
    name: str
    test_cases: List[TestCase]
    environment_type: EnvironmentType
    environment_config: Dict[str, Any]
    parallel: bool = False
    stop_on_failure: bool = False

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    status: TestStatus
    start_time: str
    end_time: str
    duration: float
    output: str
    error_message: Optional[str] = None
    artifacts: List[str] = None

@dataclass
class TestResults:
    """测试结果集合"""
    plan_id: str
    results: List[TestResult]
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    summary: str

@dataclass
class Artifact:
    """测试产物"""
    artifact_id: str
    name: str
    type: str  # "log", "dump", "screenshot", "report"
    path: str
    size: int
    created_at: str


class EnvironmentAdapter(ABC):
    """环境适配器抽象基类"""

    @abstractmethod
    async def start(self) -> bool:
        """启动环境"""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """停止环境"""
        pass

    @abstractmethod
    async def execute(self, command: str, timeout: int) -> Tuple[int, str, str]:
        """执行命令"""
        pass

    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        pass

    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """下载文件"""
        pass

    @abstractmethod
    def get_status(self) -> EnvironmentStatus:
        """获取状态"""
        pass


class TestOrchestrator:
    """
    测试编排引擎主类

    负责管理测试环境和执行测试，支持：
    - 多环境类型（QEMU、目标板、BMC）
    - 测试用例调度
    - 并发执行控制
    - 产物收集
    """

    def __init__(self, config: OrchestratorConfig):
        """初始化编排器"""
        self.config = config
        self.env_manager = EnvironmentManager()
        self.test_runner = TestRunner(config)
        self.artifact_collector = ArtifactCollector(config.artifact_dir)
        self.resource_pool = ResourcePool(config.max_concurrent_tests)

    async def setup_environment(
        self,
        env_type: EnvironmentType,
        env_config: Dict[str, Any]
    ) -> 'Environment':
        """
        设置测试环境

        Args:
            env_type: 环境类型
            env_config: 环境配置

        Returns:
            Environment: 就绪的环境实例
        """
        pass

    async def run_test_plan(self, plan: TestPlan) -> TestResults:
        """
        执行测试计划

        流程：
        1. 设置环境
        2. 执行测试用例
        3. 收集结果和产物
        4. 清理环境

        Args:
            plan: 测试计划

        Returns:
            TestResults: 测试结果
        """
        pass

    async def run_single_test(
        self,
        test: TestCase,
        env: 'Environment'
    ) -> TestResult:
        """
        执行单个测试用例

        Args:
            test: 测试用例
            env: 测试环境

        Returns:
            TestResult: 测试结果
        """
        pass

    async def collect_artifacts(self, task_id: str) -> List[Artifact]:
        """
        收集测试产物

        Args:
            task_id: 任务ID

        Returns:
            List[Artifact]: 产物列表
        """
        pass

    async def teardown_environment(self, env: 'Environment') -> bool:
        """
        清理测试环境

        Args:
            env: 环境实例

        Returns:
            bool: 是否成功
        """
        pass
```

#### 1.3.4 QEMU适配器实现

```python
class QEMUAdapter(EnvironmentAdapter):
    """QEMU环境适配器"""

    def __init__(self, config: QEMUConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.serial_socket: Optional[str] = None
        self.monitor_socket: Optional[str] = None
        self.status = EnvironmentStatus.STOPPED

    def _build_command(self) -> List[str]:
        """构建QEMU启动命令"""
        cmd = [
            self.config.binary_path,
            "-machine", self.config.machine,
            "-cpu", self.config.cpu,
            "-m", self.config.memory,
            "-nographic",
        ]

        if self.config.kernel_path:
            cmd.extend(["-kernel", self.config.kernel_path])

        if self.config.initrd_path:
            cmd.extend(["-initrd", self.config.initrd_path])

        if self.config.disk_path:
            cmd.extend([
                "-drive",
                f"file={self.config.disk_path},format=raw,if=virtio"
            ])

        if self.config.serial_enabled:
            self.serial_socket = f"/tmp/qemu-serial-{uuid.uuid4().hex}.sock"
            cmd.extend(["-serial", f"unix:{self.serial_socket},server,nowait"])

        if self.config.monitor_enabled:
            self.monitor_socket = f"/tmp/qemu-monitor-{uuid.uuid4().hex}.sock"
            cmd.extend(["-monitor", f"unix:{self.monitor_socket},server,nowait"])

        if self.config.network_enabled:
            cmd.extend([
                "-netdev", "user,id=net0",
                "-device", "virtio-net-device,netdev=net0"
            ])

        return cmd

    async def start(self) -> bool:
        """启动QEMU实例"""
        try:
            self.status = EnvironmentStatus.STARTING
            cmd = self._build_command()

            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 等待启动完成
            await self._wait_for_boot()

            self.status = EnvironmentStatus.RUNNING
            return True

        except Exception as e:
            self.status = EnvironmentStatus.ERROR
            raise EnvironmentError(f"Failed to start QEMU: {e}")

    async def stop(self) -> bool:
        """停止QEMU实例"""
        try:
            self.status = EnvironmentStatus.STOPPING

            if self.process:
                # 发送关机命令
                await self._send_monitor_command("quit")

                # 等待进程结束
                try:
                    await asyncio.wait_for(
                        self.process.wait(),
                        timeout=10
                    )
                except asyncio.TimeoutError:
                    self.process.kill()

            # 清理socket文件
            self._cleanup_sockets()

            self.status = EnvironmentStatus.STOPPED
            return True

        except Exception as e:
            self.status = EnvironmentStatus.ERROR
            return False

    async def execute(
        self,
        command: str,
        timeout: int = 60
    ) -> Tuple[int, str, str]:
        """通过串口执行命令"""
        if self.status != EnvironmentStatus.RUNNING:
            raise EnvironmentError("QEMU is not running")

        reader, writer = await asyncio.open_unix_connection(
            self.serial_socket
        )

        try:
            # 发送命令
            writer.write(f"{command}\n".encode())
            await writer.drain()

            # 读取输出
            output = await asyncio.wait_for(
                self._read_until_prompt(reader),
                timeout=timeout
            )

            return 0, output, ""

        except asyncio.TimeoutError:
            return -1, "", "Command timed out"
        finally:
            writer.close()
            await writer.wait_closed()
```

#### 1.3.5 资源池管理

```python
class ResourcePool:
    """测试资源池管理"""

    def __init__(self, max_concurrent: int):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_resources: Dict[str, 'Resource'] = {}
        self.lock = asyncio.Lock()

    async def acquire(self, resource_type: str) -> 'Resource':
        """获取资源"""
        await self.semaphore.acquire()

        async with self.lock:
            resource_id = str(uuid.uuid4())
            resource = Resource(
                resource_id=resource_id,
                resource_type=resource_type,
                acquired_at=datetime.now().isoformat()
            )
            self.active_resources[resource_id] = resource
            return resource

    async def release(self, resource_id: str) -> bool:
        """释放资源"""
        async with self.lock:
            if resource_id in self.active_resources:
                del self.active_resources[resource_id]
                self.semaphore.release()
                return True
            return False

    def get_utilization(self) -> float:
        """获取资源利用率"""
        active = len(self.active_resources)
        return active / self.max_concurrent if self.max_concurrent > 0 else 0
```

---

### 1.4 ResultAnalyzer (结果分析引擎)

**模块位置**：`src/tools/result_analysis/`

#### 1.4.1 职责定义

ResultAnalyzer负责分析测试结果，执行根因分析，并生成决策建议。

**核心职责**：
- 解析多种格式的测试日志
- 识别错误模式和分类
- 执行根因分析
- 生成决策建议（继续/修复/升级）
- 判断收敛性

#### 1.4.2 类图设计

```
┌─────────────────────────────────────────────────────────────────┐
│                       ResultAnalyzer                             │
├─────────────────────────────────────────────────────────────────┤
│ - config: AnalyzerConfig                                        │
│ - log_parser: LogParser                                         │
│ - pattern_matcher: PatternMatcher                               │
│ - root_cause_analyzer: RootCauseAnalyzer                        │
│ - decision_engine: DecisionEngine                               │
│ - llm_client: LLMClient                                         │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: AnalyzerConfig)                              │
│ + analyze_results(results: TestResults) -> AnalysisReport       │
│ + parse_logs(log_paths: List[str]) -> List[LogEntry]            │
│ + identify_failures(results: TestResults) -> List[Failure]      │
│ + analyze_root_cause(failure: Failure) -> RootCauseReport       │
│ + decide_next_action(report: AnalysisReport) -> Decision        │
│ + check_convergence(history: List[AnalysisReport]) -> bool      │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   LogParser     │  │ PatternMatcher  │  │  DecisionEngine │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ + parse()       │  │ + match()       │  │ + evaluate()    │
│ + extract()     │  │ + classify()    │  │ + recommend()   │
│ + normalize()   │  │ + score()       │  │ + confidence()  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 1.4.3 核心接口定义

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

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
    timestamp: str
    level: str  # "DEBUG", "INFO", "WARNING", "ERROR", "FATAL"
    source: str
    message: str
    context: Dict[str, Any] = None

@dataclass
class Failure:
    """失败信息"""
    failure_id: str
    test_id: str
    category: FailureCategory
    message: str
    stack_trace: Optional[str] = None
    location: Optional[str] = None
    related_logs: List[LogEntry] = None

@dataclass
class RootCauseReport:
    """根因分析报告"""
    failure_id: str
    root_cause: str
    confidence: float
    evidence: List[str]
    suggested_fix: str
    related_knowledge: List[str] = None

@dataclass
class Decision:
    """决策结果"""
    action: ActionType
    confidence: float
    rationale: str
    suggested_changes: List[str] = None
    additional_tests: List[str] = None

@dataclass
class ConvergenceStatus:
    """收敛状态"""
    converged: bool
    iteration: int
    pass_rate: float
    trend: str  # "improving", "stable", "degrading"
    remaining_failures: int


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

    def __init__(self, config: ResultAnalyzerConfig):
        """初始化分析器"""
        self.config = config
        self.log_parser = LogParser()
        self.pattern_matcher = PatternMatcher(config.pattern_db_path)
        self.root_cause_analyzer = RootCauseAnalyzer(config)
        self.decision_engine = DecisionEngine(config)
        self.llm_client = LLMClient(config.llm_model)

    def analyze_results(self, results: TestResults) -> 'AnalysisReport':
        """
        分析测试结果

        流程：
        1. 解析日志
        2. 识别失败
        3. 根因分析
        4. 生成报告

        Args:
            results: 测试结果

        Returns:
            AnalysisReport: 分析报告
        """
        pass

    def parse_logs(self, log_paths: List[str]) -> List[LogEntry]:
        """
        解析日志文件

        支持格式：
        - 标准syslog
        - JSON格式
        - 自定义格式（通过正则配置）

        Args:
            log_paths: 日志文件路径列表

        Returns:
            List[LogEntry]: 解析后的日志条目
        """
        pass

    def identify_failures(self, results: TestResults) -> List[Failure]:
        """
        识别测试失败

        Args:
            results: 测试结果

        Returns:
            List[Failure]: 失败列表
        """
        pass

    def analyze_root_cause(
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
        pass

    def decide_next_action(
        self,
        report: 'AnalysisReport',
        iteration: int
    ) -> Decision:
        """
        决定下一步行动

        Args:
            report: 分析报告
            iteration: 当前迭代次数

        Returns:
            Decision: 决策结果
        """
        pass

    def check_convergence(
        self,
        history: List['AnalysisReport']
    ) -> ConvergenceStatus:
        """
        检查是否收敛

        收敛条件：
        1. 所有测试通过
        2. 达到最大迭代次数
        3. 连续N次无改进

        Args:
            history: 历史分析报告

        Returns:
            ConvergenceStatus: 收敛状态
        """
        pass
```

#### 1.4.4 日志解析器

```python
class LogParser:
    """多格式日志解析器"""

    # 常见日志格式正则
    PATTERNS = {
        'syslog': r'(?P<timestamp>\w+\s+\d+\s+[\d:]+)\s+(?P<host>\S+)\s+(?P<source>\S+):\s+(?P<message>.*)',
        'json': None,  # JSON直接解析
        'kernel': r'\[\s*(?P<timestamp>[\d.]+)\]\s+(?P<message>.*)',
        'gcc': r'(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<level>\w+):\s+(?P<message>.*)',
    }

    def parse(
        self,
        content: str,
        format_hint: Optional[str] = None
    ) -> List[LogEntry]:
        """解析日志内容"""
        if format_hint == 'json':
            return self._parse_json(content)

        # 自动检测格式
        format_type = format_hint or self._detect_format(content)
        pattern = self.PATTERNS.get(format_type)

        if pattern:
            return self._parse_with_regex(content, pattern)
        else:
            return self._parse_generic(content)

    def _detect_format(self, content: str) -> str:
        """自动检测日志格式"""
        first_line = content.split('\n')[0]

        # 检查JSON
        if first_line.strip().startswith('{'):
            return 'json'

        # 检查kernel dmesg格式
        if re.match(r'\[\s*[\d.]+\]', first_line):
            return 'kernel'

        # 检查GCC输出格式
        if re.match(r'\S+:\d+:\d+:', first_line):
            return 'gcc'

        return 'syslog'

    def extract_errors(self, entries: List[LogEntry]) -> List[LogEntry]:
        """提取错误日志"""
        error_levels = {'ERROR', 'FATAL', 'CRITICAL', 'PANIC'}
        return [e for e in entries if e.level.upper() in error_levels]
```

#### 1.4.5 错误模式匹配

```python
class PatternMatcher:
    """错误模式匹配器"""

    # 内置错误模式库
    BUILTIN_PATTERNS = {
        FailureCategory.MEMORY_ERROR: [
            r'segmentation fault',
            r'double free',
            r'heap-buffer-overflow',
            r'use-after-free',
            r'memory leak',
        ],
        FailureCategory.ASSERTION_FAILURE: [
            r'assertion.*failed',
            r'assert\(.*\) failed',
            r'ASSERT_.*failed',
        ],
        FailureCategory.COMPILATION_ERROR: [
            r'error:.*undefined reference',
            r'error:.*undeclared',
            r'fatal error:.*no such file',
        ],
        FailureCategory.TIMEOUT: [
            r'timeout',
            r'timed out',
            r'watchdog.*expired',
        ],
        FailureCategory.CRASH: [
            r'kernel panic',
            r'oops',
            r'BUG:',
            r'core dumped',
        ],
    }

    def __init__(self, pattern_db_path: Optional[str] = None):
        self.patterns = self.BUILTIN_PATTERNS.copy()
        if pattern_db_path:
            self._load_custom_patterns(pattern_db_path)

    def classify(self, message: str) -> Tuple[FailureCategory, float]:
        """
        对错误信息进行分类

        Returns:
            Tuple[FailureCategory, float]: (分类, 置信度)
        """
        best_match = (FailureCategory.UNKNOWN, 0.0)

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    # 计算匹配分数
                    score = len(pattern) / len(message) if message else 0
                    if score > best_match[1]:
                        best_match = (category, min(score * 2, 1.0))

        return best_match

    def find_similar_failures(
        self,
        failure: Failure,
        knowledge_base: 'KnowledgeBase'
    ) -> List[Dict]:
        """从知识库查找相似失败"""
        query = f"{failure.category.value}: {failure.message}"
        return knowledge_base.search(query, limit=5)
```

#### 1.4.6 决策引擎

```python
class DecisionEngine:
    """决策引擎"""

    # 决策规则阈值
    MAX_ITERATIONS = 5
    MIN_PASS_RATE_IMPROVEMENT = 0.05
    CONFIDENCE_THRESHOLD = 0.8

    def __init__(self, config: ResultAnalyzerConfig):
        self.config = config
        self.llm_client = LLMClient(config.llm_model)

    def evaluate(
        self,
        current_report: 'AnalysisReport',
        history: List['AnalysisReport'],
        iteration: int
    ) -> Decision:
        """
        评估并生成决策

        决策逻辑：
        1. 如果全部通过 -> FINISH
        2. 如果达到最大迭代 -> ESCALATE
        3. 如果有改进且置信度高 -> CONTINUE
        4. 如果无改进或置信度低 -> MODIFY_APPROACH
        5. 如果存在可重试的临时失败 -> RETRY
        """
        # 检查是否全部通过
        if current_report.all_passed:
            return Decision(
                action=ActionType.FINISH,
                confidence=1.0,
                rationale="All tests passed"
            )

        # 检查迭代次数
        if iteration >= self.MAX_ITERATIONS:
            return Decision(
                action=ActionType.ESCALATE,
                confidence=0.9,
                rationale=f"Reached maximum iterations ({self.MAX_ITERATIONS})"
            )

        # 检查趋势
        if len(history) >= 2:
            trend = self._calculate_trend(history)

            if trend == "improving":
                return Decision(
                    action=ActionType.CONTINUE,
                    confidence=0.8,
                    rationale="Tests are improving, continue current approach"
                )
            elif trend == "stable" or trend == "degrading":
                return Decision(
                    action=ActionType.MODIFY_APPROACH,
                    confidence=0.7,
                    rationale=f"Tests are {trend}, suggest modifying approach",
                    suggested_changes=self._generate_suggestions(current_report)
                )

        # 默认：继续修复
        return Decision(
            action=ActionType.CONTINUE,
            confidence=0.6,
            rationale="First iteration, continue with current approach"
        )

    def _calculate_trend(self, history: List['AnalysisReport']) -> str:
        """计算测试趋势"""
        if len(history) < 2:
            return "unknown"

        recent = history[-3:] if len(history) >= 3 else history
        pass_rates = [r.pass_rate for r in recent]

        if all(pass_rates[i] < pass_rates[i+1] for i in range(len(pass_rates)-1)):
            return "improving"
        elif all(pass_rates[i] > pass_rates[i+1] for i in range(len(pass_rates)-1)):
            return "degrading"
        else:
            return "stable"
```

---

## 2. 数据模型设计

### 2.1 全局状态模型 (AgentState)

```python
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    """LangGraph全局状态定义"""

    # 任务标识
    task_id: str
    iteration: int
    max_iterations: int

    # 执行模式
    mode: str  # "INTERACTIVE", "CI", "AUTO"

    # 代码上下文
    repo_path: str
    target_files: List[str]
    current_commit: str
    patch_file: Optional[str]

    # 分析结果
    code_analysis: Optional[Dict[str, Any]]

    # 修改建议
    modification_suggestion: Optional[Dict[str, Any]]
    applied_patches: List[str]

    # 测试上下文
    test_plan: Optional[Dict[str, Any]]
    test_environment: str
    test_results: Optional[Dict[str, Any]]

    # 分析结果
    analysis_report: Optional[Dict[str, Any]]
    root_cause: Optional[str]

    # 决策
    next_action: str
    decision_history: List[Dict[str, Any]]

    # 知识库
    retrieved_knowledge: List[Dict[str, Any]]
    knowledge_to_store: List[Dict[str, Any]]

    # 错误处理
    errors: List[str]
    warnings: List[str]

    # 消息历史
    messages: List[str]

    # 人工介入
    human_feedback: Optional[str]
    requires_approval: bool
```

### 2.2 执行记录模型

```python
@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    task_id: str
    iteration: int

    # 时间信息
    started_at: str
    ended_at: Optional[str]
    duration: Optional[float]

    # 输入
    input_files: List[str]
    input_commit: str

    # 过程
    analysis_result: Optional[Dict]
    modification_applied: Optional[Dict]
    test_executed: Optional[Dict]

    # 输出
    output_commit: Optional[str]
    test_results: Optional[Dict]
    analysis_report: Optional[Dict]
    decision: Optional[Dict]

    # 状态
    status: str  # "running", "completed", "failed"
    error_message: Optional[str]

    # 产物
    artifacts: List[str]
```

---

## 3. 数据流设计

### 3.1 完整数据流图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           用户输入 / CI触发                               │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        状态机初始化 (StateGraph)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ AgentState: task_id, repo_path, target_files, iteration=0          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│      CodeAgent Node             │  │       KBAgent Node              │
│  ┌───────────────────────────┐  │  │  ┌───────────────────────────┐  │
│  │    CodeAnalyzer Engine    │  │  │  │   Knowledge Retrieval     │  │
│  │  - AST解析                │  │  │  │  - 相似案例检索           │  │
│  │  - 静态分析               │  │  │  │  - 上下文增强             │  │
│  │  - 依赖分析               │  │  │  │                           │  │
│  └───────────────────────────┘  │  │  └───────────────────────────┘  │
│              │                   │  │              │                  │
│              ▼                   │  │              │                  │
│  ┌───────────────────────────┐  │  │              │                  │
│  │    CodeModifier Engine    │  │  │              │                  │
│  │  - 补丁生成               │  │  │              │                  │
│  │  - 安全检查               │  │  │              │                  │
│  │  - 应用补丁               │  │  │              │                  │
│  └───────────────────────────┘  │  │              │                  │
└────────────────┬────────────────┘  └──────────────┼──────────────────┘
                 │                                   │
                 └─────────────┬─────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  State: patch_file,  │
                    │  code_analysis       │
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         TestAgent Node                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    TestOrchestrator Engine                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │ QEMU Adapter │  │ Board Adapter│  │  BMC Adapter │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  │                            │                                        │ │
│  │                            ▼                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  测试执行 → 结果收集 → 日志归档                              │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────┐
                    │  State: test_results │
                    └──────────┬───────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       AnalysisAgent Node                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    ResultAnalyzer Engine                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │  Log Parser  │  │Pattern Match │  │Decision Eng. │              │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │ │
│  │                            │                                        │ │
│  │                            ▼                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │  根因分析 → 决策生成 → 收敛判断                              │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────┐
                    │  State: next_action, │
                    │  analysis_report     │
                    └──────────┬───────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
               ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ CONTINUE │    │  FINISH  │    │ ESCALATE │
        │  (Loop)  │    │  (End)   │    │ (Human)  │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             │               ▼               ▼
             │    ┌──────────────────────────────────┐
             │    │         KBAgent Node             │
             │    │  ┌────────────────────────────┐  │
             │    │  │    Knowledge Capture       │  │
             │    │  │  - 沉淀成功案例            │  │
             │    │  │  - 更新知识库              │  │
             │    │  └────────────────────────────┘  │
             │    └──────────────────────────────────┘
             │
             └───────────────────────────────────────┐
                                                     │
                                                     ▼
                                            ┌──────────────┐
                                            │ iteration++  │
                                            │ 返回CodeAgent│
                                            └──────────────┘
```

### 3.2 状态转换表

| 当前状态 | 触发条件 | 下一状态 | 动作 |
|----------|----------|----------|------|
| IDLE | 任务创建 | ANALYZING | 初始化状态，调用CodeAgent |
| ANALYZING | 分析完成 | MODIFYING | 生成修改建议 |
| MODIFYING | 补丁生成 | AWAITING_APPROVAL | 等待人工确认（INTERACTIVE模式）|
| MODIFYING | 补丁生成 | TESTING | 自动应用补丁（AUTO/CI模式）|
| AWAITING_APPROVAL | 用户确认 | TESTING | 应用补丁，执行测试 |
| TESTING | 测试完成 | RESULT_ANALYSIS | 分析测试结果 |
| RESULT_ANALYSIS | 全部通过 | SUCCESS | 任务完成 |
| RESULT_ANALYSIS | 存在失败且可修复 | ANALYZING | 继续迭代 |
| RESULT_ANALYSIS | 达到最大迭代 | ESCALATED | 升级人工介入 |
| * | 异常发生 | ERROR | 记录错误，可恢复 |

---

## 4. 集成接口设计

### 4.1 Agent-Engine集成

```python
class AgentEngineIntegration:
    """Agent与Engine的集成层"""

    @staticmethod
    def code_agent_tools() -> List[Tool]:
        """CodeAgent可用的工具"""
        return [
            Tool(
                name="analyze_code",
                description="Analyze C/C++ source files",
                func=lambda params: CodeAnalyzer().analyze_files(params["files"])
            ),
            Tool(
                name="generate_patch",
                description="Generate a patch based on modification suggestion",
                func=lambda params: CodeModifier().generate_patch(params["suggestion"])
            ),
            Tool(
                name="apply_patch",
                description="Apply a patch to the codebase",
                func=lambda params: CodeModifier().apply_patch(params["patch"])
            ),
        ]

    @staticmethod
    def test_agent_tools() -> List[Tool]:
        """TestAgent可用的工具"""
        return [
            Tool(
                name="setup_environment",
                description="Setup test environment (QEMU/Board/BMC)",
                func=lambda params: TestOrchestrator().setup_environment(params["env_type"])
            ),
            Tool(
                name="run_tests",
                description="Execute test plan",
                func=lambda params: TestOrchestrator().run_test_plan(params["plan"])
            ),
            Tool(
                name="collect_artifacts",
                description="Collect test artifacts",
                func=lambda params: TestOrchestrator().collect_artifacts(params["task_id"])
            ),
        ]

    @staticmethod
    def analysis_agent_tools() -> List[Tool]:
        """AnalysisAgent可用的工具"""
        return [
            Tool(
                name="analyze_results",
                description="Analyze test results",
                func=lambda params: ResultAnalyzer().analyze_results(params["results"])
            ),
            Tool(
                name="root_cause_analysis",
                description="Perform root cause analysis on failures",
                func=lambda params: ResultAnalyzer().analyze_root_cause(params["failure"])
            ),
            Tool(
                name="decide_action",
                description="Decide next action based on analysis",
                func=lambda params: ResultAnalyzer().decide_next_action(params["report"])
            ),
        ]
```

### 4.2 LangGraph工作流定义

```python
from langgraph.graph import StateGraph, END

def create_workflow() -> StateGraph:
    """创建LangGraph工作流"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("code_agent", code_agent_node)
    workflow.add_node("test_agent", test_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("kb_agent", kb_agent_node)
    workflow.add_node("human_review", human_review_node)

    # 设置入口
    workflow.set_entry_point("code_agent")

    # 添加边
    workflow.add_edge("code_agent", "test_agent")
    workflow.add_edge("test_agent", "analysis_agent")

    # 条件边
    workflow.add_conditional_edges(
        "analysis_agent",
        decide_next_step,
        {
            "continue": "code_agent",
            "finish": "kb_agent",
            "escalate": "human_review",
        }
    )

    workflow.add_edge("kb_agent", END)
    workflow.add_edge("human_review", END)

    return workflow.compile()


def decide_next_step(state: AgentState) -> str:
    """决策函数：决定下一步"""
    next_action = state.get("next_action", "continue")

    if next_action == "finish":
        return "finish"
    elif next_action == "escalate":
        return "escalate"
    elif state.get("iteration", 0) >= state.get("max_iterations", 5):
        return "escalate"
    else:
        return "continue"
```

---

## 5. 错误处理设计

### 5.1 错误分类

```python
class EngineError(Exception):
    """引擎基础异常"""
    pass

class AnalysisError(EngineError):
    """代码分析异常"""
    pass

class ModificationError(EngineError):
    """代码修改异常"""
    pass

class TestExecutionError(EngineError):
    """测试执行异常"""
    pass

class EnvironmentError(EngineError):
    """环境管理异常"""
    pass

class ResultAnalysisError(EngineError):
    """结果分析异常"""
    pass
```

### 5.2 错误恢复策略

```python
class ErrorRecoveryStrategy:
    """错误恢复策略"""

    STRATEGIES = {
        AnalysisError: "retry_with_fallback",
        ModificationError: "rollback_and_retry",
        TestExecutionError: "restart_environment",
        EnvironmentError: "recreate_environment",
        ResultAnalysisError: "use_default_decision",
    }

    @classmethod
    def recover(cls, error: EngineError, state: AgentState) -> AgentState:
        """执行错误恢复"""
        strategy = cls.STRATEGIES.get(type(error), "escalate")

        if strategy == "retry_with_fallback":
            return cls._retry_with_fallback(error, state)
        elif strategy == "rollback_and_retry":
            return cls._rollback_and_retry(error, state)
        elif strategy == "restart_environment":
            return cls._restart_environment(error, state)
        elif strategy == "recreate_environment":
            return cls._recreate_environment(error, state)
        elif strategy == "use_default_decision":
            return cls._use_default_decision(error, state)
        else:
            return cls._escalate(error, state)
```

---

## 6. 性能优化设计

### 6.1 缓存策略

```python
class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
        self.local_cache = {}

    def cache_analysis(self, file_path: str, ast_hash: str, result: Dict):
        """缓存分析结果"""
        key = f"analysis:{ast_hash}"
        self.redis.setex(key, 3600, json.dumps(result))

    def get_cached_analysis(self, ast_hash: str) -> Optional[Dict]:
        """获取缓存的分析结果"""
        key = f"analysis:{ast_hash}"
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None
```

### 6.2 并发控制

```python
class ConcurrencyManager:
    """并发控制管理器"""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphores = {
            "analysis": asyncio.Semaphore(max_workers),
            "test": asyncio.Semaphore(2),  # 测试资源受限
            "llm": asyncio.Semaphore(5),   # LLM API限制
        }

    async def run_with_limit(
        self,
        resource_type: str,
        coro: Coroutine
    ):
        """带资源限制的执行"""
        async with self.semaphores[resource_type]:
            return await coro
```

---

## 7. 安全设计

### 7.1 沙箱执行

```python
class SandboxExecutor:
    """沙箱执行器"""

    def __init__(self, config: Dict):
        self.docker_client = docker.from_env()
        self.image = config.get("sandbox_image", "aft-sandbox:latest")
        self.timeout = config.get("timeout", 300)

    def execute_in_sandbox(
        self,
        command: str,
        workspace: str
    ) -> Tuple[int, str, str]:
        """在沙箱中执行命令"""
        container = self.docker_client.containers.run(
            self.image,
            command,
            volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
            detach=True,
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=50000,
            network_mode="none",
        )

        try:
            result = container.wait(timeout=self.timeout)
            logs = container.logs()
            return result["StatusCode"], logs.decode(), ""
        finally:
            container.remove(force=True)
```

### 7.2 敏感信息过滤

```python
class SecretFilter:
    """敏感信息过滤器"""

    PATTERNS = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
    ]

    @classmethod
    def filter(cls, text: str) -> str:
        """过滤敏感信息"""
        for pattern in cls.PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        return text
```

---

**文档版本**：v2.0
**更新日期**：2026-01-30
**状态**：已完善核心引擎详细设计
