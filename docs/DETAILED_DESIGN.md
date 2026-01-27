# AI-Driven Firmware Intelligent Testing System - Detailed Design

## Table of Contents
1. [Core Modules Detailed Design](#1-core-modules-detailed-design)
    1.1 [CodeAnalyzer 详细设计](#11-codeanalyzer-详细设计)
        1.1.1 [功能概述](#111-功能概述)
        1.1.2 [实现细节深度解析](#112-实现细节深度解析)
        1.1.3 [核心 API 规范定义](#113-核心-api-规范定义)
        1.1.4 [核心数据结构详解](#114-核心数据结构详解)
        1.1.5 [符号表管理策略深度说明](#115-符号表管理策略深度说明)
        1.1.6 [圈复杂度计算详细算法](#116-圈复杂度计算详细算法)
        1.1.7 [实现备注与限制](#117-实现备注与限制)
    1.2 [CodeModifier 详细设计](#12-codemodifier-详细设计)
        1.2.1 [功能概述](#121-功能概述)
        1.2.2 [修改建议生成流程详细说明](#122-修改建议生成流程详细说明)
        1.2.3 [验证和安全检查机制详细说明](#123-验证和安全检查机制详细说明)
        1.2.4 [代码补丁生成详细说明](#124-代码补丁生成详细说明)
        1.2.5 [补丁冲突解决策略](#125-补丁冲突解决策略)
        1.2.6 [修改历史管理详细说明](#126-修改历史管理详细说明)
        1.2.7 [核心 API 详细定义](#127-核心-api-详细定义)
        1.2.8 [核心数据结构详解](#128-核心数据结构详解)
        1.2.9 [验证逻辑深度说明](#129-验证逻辑深度说明)
        1.2.10 [异常处理与边缘情况](#1210-异常处理与边缘情况)
    1.3 [TestOrchestrator 详细设计](#13-testorchestrator-详细设计)
        1.3.1 [功能概述](#131-功能概述)
        1.3.2 [多环境测试执行流程详细说明](#132-多环境测试执行流程详细说明)
        1.3.3 [环境抽象层设计详细说明](#133-环境抽象层设计详细说明)
        1.3.4 [测试配置管理详细说明](#134-测试配置管理详细说明)
        1.3.5 [日志采集和标准化详细说明](#135-日志采集和标准化详细说明)
        1.3.6 [测试结果格式标准化](#136-测试结果格式标准化)
        1.3.7 [核心 API 详细定义](#137-核心-api-详细定义)
    1.4 [ResultAnalyzer 详细设计](#14-resultanalyzer-详细设计)
        1.4.1 [功能概述](#141-功能概述)
        1.4.2 [日志解析规则引擎详细说明](#142-日志解析规则引擎详细说明)
        1.4.3 [错误分类系统详细说明](#143-错误分类系统详细说明)
        1.4.4 [根因分析详细说明](#144-根因分析详细说明)
        1.4.5 [经验知识提取详细说明](#145-经验知识提取详细说明)
        1.4.6 [核心 API 详细定义](#146-核心-api-详细定义)
        1.4.7 [数据结构详细定义](#147-数据结构详细定义)
        1.4.8 [设计决策补充](#148-设计决策补充)
2. [Data Models](#2-data-models)
    2.1 [Code Modification Record](#21-code-modification-record)
    2.2 [Test Execution Record](#22-test-execution-record)
    2.3 [Knowledge Unit](#23-knowledge-unit)
3. [API and Interface Design](#3-api-and-interface-design)
    3.1 [Agent Communication](#31-agent-communication)
    3.2 [Knowledge Query Interface](#32-knowledge-query-interface)
    3.3 [Test Execution Interface](#33-test-execution-interface)
4. [Configuration and Strategies](#4-configuration-and-strategies)
    4.1 [Agent Configuration](#41-agent-configuration)
    4.2 [Retrieval Strategy](#42-retrieval-strategy)
5. [Security and Reliability](#5-security-and-reliability)
    5.1 [Sandbox Execution](#51-sandbox-execution)
    5.2 [Code Integrity](#52-code-integrity)
6. [Conclusion](#6-conclusion)

## 1. Core Modules Detailed Design

### 1.1 CodeAnalyzer 详细设计

#### 1.1.1 功能概述
CodeAnalyzer 是本系统的底层核心模块，专门针对 C 语言（特别是嵌入式固件中常见的 C 代码）提供深度的静态分析能力。它不仅仅是一个简单的代码解析器，更是一个能够理解代码逻辑结构、识别调用路径并评估代码质量的综合引擎。其核心目标是为下游的 AI 代理（Agent）提供高度结构化的上下文信息，使其能够基于客观事实而非单纯的文本匹配来生成代码建议。

主要核心功能点涵盖：
- **全语法树（AST）解析**：基于 C99/C11 标准，将源码转换为可操作的对象模型。
- **精细化符号提取**：从顶层作用域到底层局部块，全面抓取函数、变量、宏、结构体定义。
- **全局依赖建模**：构建跨文件的依赖关系，识别头文件包含链和外部引用。
- **多维度复杂度评估**：提供定量指标，量化代码的逻辑复杂度，为风险评估提供依据。
- **控制流分析**：构建函数内部的控制流图（CFG），识别不可达代码和循环结构。
- **数据流分析**：追踪变量的生命周期和定义-使用（Def-Use）链。
- **代码规范性检查**：初步检查代码是否符合特定的嵌入式 C 编程规范。

#### 1.1.2 实现细节深度解析

##### 1. AST 解析架构与策略
*   **解析引擎选型**：
    CodeAnalyzer 选定 `pycparser` 作为核心解析引擎。
    *   *选择理由*：`pycparser` 能够精确处理 C 语言的声明语法，支持预处理后的代码流，且其生成的 AST 节点与 C 语言规范一一对应。相比于 `tree-sitter`，它在处理 C 语言类型定义（typedef）和符号识别方面更加严谨，适合需要深度语义分析的场景。
*   **AST 节点遍历机制**：
    采用增强的 **Visitor 设计模式**。通过继承 `c_ast.NodeVisitor`，我们实现了对不同控制流语句的定向拦截：
    *   `visit_FuncDef`: 捕获函数定义。记录函数名、起始行、结束行，并递归分析函数体。
    *   `visit_Decl`: 捕获变量和函数的声明。识别 `static`, `extern` 等存储修饰符。
    *   `visit_If`, `visit_For`, `visit_While`, `visit_DoWhile`: 捕获循环和条件分支，用于复杂度计算。
    *   `visit_Switch`, `visit_Case`, `visit_Default`: 捕获多分支结构。
    *   `visit_FuncCall`: 捕获函数调用，记录被调函数名和实参列表。
    *   `visit_ID`, `visit_StructRef`, `visit_ArrayRef`: 识别变量引用和成员访问。
    *   `visit_TypeDecl`, `visit_Typedef`, `visit_Enum`, `visit_Struct`, `visit_Union`: 捕获自定义数据类型。
*   **鲁棒性处理：不完整代码分析**：
    固件开发中，由于特定硬件头文件的缺失，常会导致解析中断。我们采用了以下策略：
    1.  **预处理器模拟**：自动模拟常见的宏定义（如 `__attribute__`, `__inline`, `__asm__`, `__volatile__`）以减少解析错误。
    2.  **分块解析**：当整体解析失败时，系统将代码按函数块进行分割，尝试逐个解析，并记录失败的行号和原因。
    3.  **宽容模式**：在遇到无法识别的语法节点时，记录错误位置并尝试通过简单的正则表达式跳过该片段，继续后续分析。
    4.  **头文件插桩**：对于缺失的头文件，自动生成包含空函数原型和基本类型定义的占位头文件。

##### 2. 符号表管理机制 (Symbol Table Management)
符号表是连接 AST 节点与语义信息的桥梁。
*   **层级化作用域 (Scoped Symbol Tables)**：
    *   **Level 0 (Global Scope)**: 存储全局变量、全局函数原型、全局宏定义、结构体定义。
    *   **Level 1 (File Static Scope)**: 存储 `static` 修饰的文件私有变量和函数。
    *   **Level 2+ (Local Scope)**: 对应函数体内部的代码块（Compound Statement）。处理变量遮蔽（Shadowing）逻辑。每次遇到 `{` 增加一层，遇到 `}` 减少一层。
*   **符号生命周期追踪**：
    记录符号的定义位置、作用域范围、首次使用位置及最后一次使用位置。
*   **符号冲突处理**：
    在同一作用域内发现重复定义时，标记为错误；在嵌套作用域中发现重名时，按照“就近原则”映射。

##### 3. 调用图 (Call Graph) 构建算法
调用图是分析 Bug 传播路径和评估修改影响范围的关键。
*   **直接调用追踪**：
    遍历函数体内的 `FuncCall` 节点，建立主调函数到被调函数的边。
*   **间接调用分析 (Indirect Calls)**：
    对于通过函数指针进行的调用（例如 `ops->read()`），CodeAnalyzer 会检索符号表查找该指针可能的赋值点。若无法确定，则标记为 `PotentialIndirectCall`。
*   **递归调用识别**：
    利用深度优先搜索 (DFS) 和拓扑排序识别图中的环路。递归函数在固件中通常被限制使用，分析器会对其进行高亮警告。

##### 4. 自动化数据流分析
*   **Def-Use 链 (Definition-Use Chain)**：
    为函数内的每个变量构建定义-使用链。
    *   *算法逻辑*：
        1. 识别所有赋值语句（Definition）。
        2. 识别所有读取语句（Use）。
        3. 检查是否存在“定义后从未被使用”或“使用前未被定义（赋值）”的路径。
*   **简单的变量追踪**：
    分析变量在函数调用间的传递。识别是否通过指针传递了局部变量地址（悬挂指针风险）。

##### 5. 复杂度指标计算模型
*   **圈复杂度 (Cyclomatic Complexity, M)**：
    $M = E - N + 2P$，在 AST 层面的简化计算：$1 + \sum(\text{分支节点})$。
    *   判定节点：`if`, `while`, `for`, `case`, `&&`, `||`, `? :`。
*   **LOC 统计**：
    *   SLOC (Source Lines of Code): 除去注释和空行的代码行。
    *   CLOC (Comment Lines of Code): 注释行。
    *   BLOC (Blank Lines of Code): 空行。
*   **函数度量**：
    *   参数个数。
    *   最大嵌套深度。
    *   函数长度（行数）。

##### 6. 工业级缓存策略
为了支持拥有数万个源文件的固件工程：
*   **持久化方案**：使用 `pickle` 或 `msgpack` 将解析后的符号表和依赖图序列化到 `.analyzer_cache` 目录。
*   **缓存 Key**：`SHA256(filepath + file_mtime + compiler_config)`。
*   **失效策略**：若文件修改时间发生变化，或其包含的任何头文件发生变化，则强制重新解析。

#### 1.1.3 核心 API 规范定义

```python
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class SymbolScope(Enum):
    GLOBAL = "global"
    STATIC = "static"
    LOCAL = "local"
    EXTERN = "extern"

@dataclass
class Position:
    """位置信息"""
    line: int
    column: int
    filepath: str

class CodeAnalyzer:
    """
    CodeAnalyzer 类负责执行 C 代码的详细解析和深度静态分析。
    """

    def __init__(self, include_paths: List[str] = None, defines: Dict[str, str] = None):
        """
        初始化分析器。
        :param include_paths: 头文件搜索路径列表
        :param defines: 预定义的宏及其值
        """
        self.include_paths = include_paths or []
        self.defines = defines or {}
        self.global_symbol_table = {}
        self.dependency_graph = DependencyGraph()

    def parse_file(self, filepath: str) -> Any:
        """
        解析指定文件并生成 AST。
        :param filepath: 目标文件路径
        :return: pycparser.c_ast.FileAST 对象
        """
        pass

    def extract_functions(self, ast: Any) -> List['FunctionInfo']:
        """
        从 AST 中提取所有函数的信息。
        :param ast: AST 根节点
        :return: FunctionInfo 对象列表
        """
        pass

    def extract_globals(self, ast: Any) -> List['GlobalVarInfo']:
        """
        从 AST 中提取所有全局变量的信息。
        :param ast: AST 根节点
        :return: GlobalVarInfo 对象列表
        """
        pass

    def extract_macros(self, filepath: str) -> List['MacroInfo']:
        """
        提取文件中的宏定义，包括常量宏和函数式宏。
        :param filepath: 文件路径
        :return: MacroInfo 对象列表
        """
        pass

    def analyze_dependencies(self) -> 'DependencyGraph':
        """
        基于当前项目状态构建完整的依赖图。
        :return: DependencyGraph 对象
        """
        pass

    def calculate_complexity(self, func_name: str) -> 'ComplexityMetrics':
        """
        计算指定函数的复杂度指标。
        :param func_name: 函数名
        :return: ComplexityMetrics 对象
        """
        pass

    def get_function_signature(self, func_name: str) -> 'FunctionSignature':
        """
        获取函数的完整签名。
        :param func_name: 函数名
        :return: FunctionSignature 对象
        """
        pass

    def find_symbol_definition(self, symbol_name: str, context_pos: Position) -> Optional[Position]:
        """
        根据上下文位置查找符号的定义位置。
        :param symbol_name: 符号名
        :param context_pos: 当前上下文位置
        :return: 定义位置的 Position 对象
        """
        pass

    def get_call_stack_to(self, target_func: str) -> List[List[str]]:
        """
        获取到达目标函数的所有可能调用路径。
        :param target_func: 目标函数名
        :return: 调用路径列表
        """
        pass
```

#### 1.1.4 核心数据结构详解

```python
@dataclass
class Argument:
    """函数参数描述"""
    name: str                           # 参数名
    type: str                           # 参数类型
    pos: Position                       # 定义位置

class FunctionSignature:
    """函数接口签名"""
    name: str                           # 函数名
    return_type: str                    # 返回值类型
    arguments: List[Argument]           # 参数对象列表
    is_static: bool                     # 是否为静态函数
    is_inline: bool                     # 是否为内联函数
    attributes: List[str]               # 特殊属性如 __attribute__

class FunctionInfo:
    """函数的全量分析信息"""
    name: str                           # 函数名
    signature: FunctionSignature        # 签名对象
    parameters: List[Argument]          # 参数列表 (冗余存储，便于访问)
    return_type: str                   # 返回类型
    start_line: int                    # 起始行号
    end_line: int                      # 结束行号
    file_path: str                     # 所属文件
    cyclomatic_complexity: int         # 圈复杂度
    called_functions: List[str]        # 内部调用的函数名列表
    called_by: List[str]               # 被哪些函数调用
    local_variables: List['LocalVar']  # 局部变量列表
    max_nesting_depth: int             # 最大嵌套深度
    has_recursion: bool                # 是否递归
    is_definition: bool                # 是否为完整定义（而非原型声明）
    docstring: str                     # 函数上方的注释内容

@dataclass
class LocalVar:
    """局部变量描述"""
    name: str
    type: str
    scope_level: int
    definition_pos: Position

class GlobalVarInfo:
    """全局变量详细信息"""
    name: str                          # 变量名
    type: str                          # 数据类型
    initial_value: Optional[str]       # 初始值字符串
    scope: SymbolScope                 # 作用域
    is_const: bool                     # 是否为常量
    is_volatile: bool                  # 是否为易变变量
    used_by_functions: List[str]       # 访问此变量的函数名
    definition_pos: Position           # 定义位置

class MacroInfo:
    """预处理宏信息"""
    name: str                          # 宏名
    is_function_like: bool             # 是否带参数
    params: List[str]                  # 参数名列表（若有）
    body: str                          # 宏展开内容
    definition_line: int               # 定义行号
    filepath: str                      # 定义文件

class DependencyGraph:
    """项目依赖关系图"""
    nodes: Dict[str, 'Node']           # 节点映射
    edges: List['Edge']                # 边列表

@dataclass
class Node:
    """图节点"""
    id: str
    type: str                          # 'function', 'variable', 'file'
    data: Any

@dataclass
class Edge:
    """图边"""
    source: str
    target: str
    type: str                          # 'call', 'reference', 'include'

class ComplexityMetrics:
    """复杂度度量报告"""
    function_name: str
    cyclomatic_complexity: int         # 圈复杂度
    sloc: int                          # 代码行数
    cloc: int                          # 注释行数
    param_count: int                   # 参数数量
    nesting_depth: int                 # 嵌套深度
    decision_points: int               # 决策点数
```

#### 1.1.5 符号表管理策略深度说明
符号表管理是静态分析的核心挑战之一，CodeAnalyzer 采用了以下高级策略：
- **符号重命名处理**：在固件代码中，常常使用 `#define` 重新定义库函数名。CodeAnalyzer 在预处理阶段会解析这些定义，确保在符号表中记录的是其最终的链接名称。
- **结构体成员追踪**：对于 `struct` 和 `union`，符号表不仅记录类型名，还记录其内部成员的偏移、类型及访问频率。这对于 AI 识别“由于结构体成员未对齐导致的 Bug”至关重要。
- **匿名作用域处理**：对于 C 代码中的匿名代码块（如 `if (cond) { int x; }`），分析器会自动生成唯一的标识符（如 `_anon_block_1`）来管理其生命周期。

#### 1.1.6 圈复杂度计算详细算法
本模块实现的圈复杂度计算遵循以下步骤：
1. **控制流节点识别**: 遍历函数 AST，识别所有条件判断节点（`If`, `While`, `For`, `DoWhile`, `Switch`, `Case`）。
2. **逻辑运算符累加**: 在 C 语言中，`&&` 和 `||` 会导致短路求值，实质上增加了执行路径。因此，每个逻辑运算符节点在圈复杂度计算中均计为 +1。
3. **判定点统计**: $P = \text{控制流节点数} + \text{逻辑运算符数}$。
4. **最终结果**: $M = P + 1$。

#### 1.1.7 实现备注与限制
- **内联汇编 (Inline Assembly)**: CodeAnalyzer 目前仅能识别汇编块的范围，无法解析汇编内部的指令逻辑。
- **动态宏扩展**: 对于依赖于复杂预处理器递归的宏，解析器可能仅记录展开后的最终形态，而丢失中间过程。

---

### 1.2 CodeModifier 详细设计

#### 1.2.1 功能概述
CodeModifier 是闭环自动化修复系统的“执行手”。它接收来自分析阶段的故障诊断结果，并将其转化为安全、可验证且高质量的代码变更。其核心逻辑是：**“基于 AI 建议，执行工业级验证”**。

主要核心功能：
- **修改建议生成**：针对特定 Bug 生成修复方案。
- **自动化验证流水线**：涵盖语法、规范、编译、符号、接口五层检查。
- **补丁管理**：生成标准 Unified Diff。
- **修改历史记录与回滚**：确保每一笔改动均可审计且可逆。

#### 1.2.2 修改建议生成流程详细说明

##### 1. 输入阶段 (Input Phase)
CodeModifier 自动聚合以下数据包：
*   **目标代码块**：需要修改的函数及其上下游代码。
*   **诊断信息**：包括编译错误、Lint 警告或动态测试失败的 Log（含堆栈）。
*   **语义上下文**：通过 CodeAnalyzer 获取的全局变量定义、相关函数签名。
*   **环境标签**：如产品线名称、芯片型号。

##### 2. Prompt 工程详细说明
*   **System Prompt**：定义 AI 角色为“资深固件安全专家”。设定约束：“禁止引入外部库”、“保持代码缩进为 4 空格”、“遵循 MISRA C 安全规范”。
*   **Context 补充**：
    *   *Example*: "The function `dev_write` uses global `g_lock`. Ensure you release it before returning."
*   **Specific Requirements**：
    *   "Do not change the function signature."
    *   "Use `MEM_ALLOC` instead of `malloc`."
    *   "Ensure all return paths are handled correctly."

##### 3. LLM API 调用
*   **模型选择**：默认使用 GPT-4 或 Claude 3.5。
*   **重试机制**：如果 AI 生成的代码在语法检查阶段失败，系统会自动将解析错误反馈给 AI，要求其重修。
*   **并行建议**：同时请求 3 个不同的建议，并根据验证结果挑选最优的一个。

##### 4. 输出处理 (Post-processing)
*   **提取代码**：从 Markdown 回复中精准切取 ` ```c ` 块。
*   **格式化**：调用 `clang-format -i --style=file` 对生成代码进行格式归一化。

#### 1.2.3 验证和安全检查机制详细说明

1.  **语法检查 (Syntax Check)**：
    使用 `pycparser` 重新解析修改后的文件。任何 Parse Error 都会触发 AI 重写。
2.  **静态分析 (Lint Check)**：
    集成 `cppcheck`。检查项包括：变量未初始化、内存泄漏、数组越界、空指针解引用。
3.  **编译检查 (Compile Check)**：
    - 在配置好的 Docker 编译环境中执行编译命令。
    - **严格模式**：开启 `-Werror`，将所有警告视为错误。
4.  **符号表检查 (Symbol Check)**：
    验证新增代码引用的所有外部符号是否已在符号表中定义。
5.  **签名检查 (Signature Check)**：
    确保被标记为“禁止修改接口”的函数签名完全一致。

#### 1.2.4 代码补丁生成详细说明
*   **格式**：Unified Diff 格式（`diff -u`）。
*   **上下文行数**：默认保留 3 行上下文。

#### 1.2.5 补丁冲突解决策略
在多 Agent 并发场景下，CodeModifier 采用以下冲突解决机制：
1. **基于 Git 的三路合并**: 优先尝试利用 `git merge` 或 `git cherry-pick` 解决冲突。
2. **模糊匹配 (Fuzzing)**: 允许 `patch` 工具在行号微调的情况下应用补丁。
3. **重分析策略**: 如果补丁应用彻底失败，系统将重新运行 CodeAnalyzer 刷新上下文，并重新请求 AI 生成针对最新源码版本的修改建议。

#### 1.2.6 修改历史管理详细说明
*   **数据结构 (ModificationRecord)**：包含 ID、文件名、Git Commit Hash、修改前后快照、AI 推理过程、验证状态。
*   **回滚机制**：提供 `rollback(record_id)` API。系统通过 `git checkout` 或应用反向补丁恢复文件。

#### 1.2.7 核心 API 详细定义

```python
from datetime import datetime
from typing import List, Dict, Optional, Any

class CodeModifier:
    """
    CodeModifier 类负责协调 AI 生成修改建议并执行严格的验证流程。
    """

    def suggest_modifications(
        self, 
        code: str, 
        error_log: str, 
        context: Dict[str, Any], 
        constraints: Dict[str, Any]
    ) -> List['ModificationSuggestion']:
        """
        向 LLM 请求修复建议。
        """
        pass

    def validate_modification(
        self, 
        file_path: str, 
        modified_content: str
    ) -> 'ValidationResult':
        """
        执行语法、静态、编译、符号、接口五级验证。
        """
        pass

    def apply_modification(self, file_path: str, modification: 'ModificationSuggestion') -> bool:
        """
        将建议应用到物理文件并持久化记录。
        """
        pass

    def generate_patch(self, original_text: str, modified_text: str, filename: str) -> str:
        """
        计算并返回两个版本之间的 Unified Diff。
        """
        pass

    def rollback_to_version(self, file_path: str, version_id: str) -> bool:
        """
        执行回退操作。
        """
        pass

    def get_modification_history(self, file_path: str) -> List['ModificationRecord']:
        """
        获取该文件的所有修改足迹。
        """
        pass
```

#### 1.2.8 核心数据结构详解

```python
@dataclass
class ModificationSuggestion:
    """AI 生成的修改建议"""
    id: str                            # 建议 ID
    original_code: str                 # 修改前的代码块
    suggested_code: str                # AI 建议的代码块
    reasoning: str                     # AI 的逻辑推理
    affected_functions: List[str]      # 涉及的函数名
    confidence: float                  # 0.0 - 1.0 的置信度
    risks: List[str]                   # 潜在风险点

@dataclass
class CheckResult:
    """单项检查的结果"""
    passed: bool
    details: str                       # 错误输出或警告信息
    duration: float                    # 检查耗时

@dataclass
class ValidationResult:
    """综合验证报告"""
    is_valid: bool                     # 最终是否通过
    syntax_ok: CheckResult
    lint_ok: CheckResult
    compile_ok: CheckResult
    symbol_ok: CheckResult
    signature_ok: CheckResult
    errors: List[str]

@dataclass
class ModificationRecord:
    """持久化存储的修改记录"""
    record_id: str
    file_path: str
    base_commit: str                   # 基础 Git 哈希
    timestamp: datetime
    diff: str                          # 保存的 Diff 内容
    reasoning: str                     # AI 推理
    validation_report: dict            # 详细验证快照
    applied: bool                      # 是否当前已生效
```

#### 1.2.9 验证逻辑深度说明
验证逻辑是 CodeModifier 的灵魂。本模块实现了以下高级验证算法：
- **控制流等价性初步分析**：在某些重构任务中，利用 AST 比较工具确保除了目标逻辑外，核心控制流未发生非预期改变。
- **交叉编译矩阵验证**：针对跨平台固件，CodeModifier 可以在多个 Docker 容器中并行编译，确保修改的可移植性。

#### 1.2.10 异常处理与边缘情况
- **编译器 OOM**: 监控编译容器资源，自动调整内存配额。
- **AI 死循环生成**: 设置最大生成 Token 限制，防止模型失控。

### 1.3 TestOrchestrator 详细设计

#### 1.3.1 功能概述
TestOrchestrator 是系统的测试执行核心，负责管理各种异构测试环境、调度测试任务、监控执行状态并汇总原始测试数据。它屏蔽了底层硬件和仿真环境的差异，为上层 Agent 提供统一的测试接口。

核心功能深度扩展：
- **测试框架适配**：通过驱动插件支持 pytest、Robot Framework、CUnit、Google Test、LTP (Linux Test Project) 等。
- **多环境执行调度**：统一管理 QEMU 模拟器、物理目标板、BMC (via IPMI/Redfish)、树莓派以及 Windows 宿主机。
- **环境隔离与复位**：确保每个测试用例都在干净、确定的环境中执行，支持自动快照回滚。
- **全栈日志采集**：实时流式采集串口、系统 syslog、内核 dmesg、应用 stdout 以及硬件传感器（如功耗、温度）日志。
- **结果标准化处理**：将不同框架的输出（JUnit XML, TAP, JSON）统一转换为系统内置的 `TestResult` 模型。

#### 1.3.2 多环境测试执行流程详细说明

##### 1. QEMU 环境测试执行流程
QEMU 是固件开发中最常用的仿真环境，其执行流程如下：
- **初始化阶段**：
    - 根据配置（架构如 aarch64, 机器类型如 virt, 内存大小）启动 QEMU 进程。
    - 加载指定的固件镜像（Flash/ROM）和内核镜像。
    - 配置后端网络（如 TAP 设备或用户态 SLIRP）并映射调试端口（如 GDB, SSH）。
- **部署阶段**：
    - 检查 Guest 系统就绪状态（通常通过等待特定的串口输出或 SSH 服务响应）。
    - 使用 `scp` 或通过 `virtio-fs` 将测试脚本及测试产物（二进制文件）同步到虚拟机。
- **执行阶段**：
    - 触发测试脚本运行。
    - 持续监听 stdout 和 stderr，同时通过 QMP (QEMU Machine Protocol) 监控虚拟机 CPU 负载。
- **清理阶段**：
    - 执行关机指令或强制终止 QEMU 进程。
    - 清理临时磁盘镜像及快照文件。
- **结果收集**：解析执行输出，提取退出码和关键错误标记。

##### 2. 目标板环境（Target Board）测试执行流程
物理板卡测试涉及复杂的硬件操作：
- **锁定资源**：在硬件资源池中申请并独占目标板卡及其关联的 PDU 端口。
- **固件烧写**：
    - 建立 SSH 或串口连接。
    - 利用 TFTP、NFS 或供应商特定的烧录工具（如 OpenOCD）将编译产物刷入非易失性存储。
- **电源管理**：通过 IPMI 或 PDU API 执行电源循环（Power Cycle），确保硬件状态彻底重置。
- **日志采集开启**：启动串口服务器（Terminal Server）的录制功能，开始监听 Serial Console。
- **执行与验证**：在目标板执行测试，并根据串口输出实时判定系统是否发生 Kernel Panic。
- **清理与回收**：复位硬件到基准状态，解锁资源。

##### 3. 树莓派（Raspberry Pi）环境测试执行流程
- **SSH 认证**：建立远程 shell 会话。
- **环境自检**：安装缺失的库依赖，检查 GPIO 映射表是否冲突。
- **部署与执行**：上传测试套件并赋予执行权限，调用指定命令。
- **硬件遥测**：利用内置传感器接口采集执行期间的 CPU 温度、核心电压。
- **资源清理**：还原 GPIO 引脚状态，清理 `/tmp/test_*` 临时工作区。

##### 4. Windows 环境测试执行流程
针对宿主机相关的工具链或驱动测试：
- **WinRM 建立**：初始化 Windows 远程管理服务连接。
- **配置注入**：自动设置测试所需的环境变量（PATH, SystemDrive）。
- **PowerShell 执行**：利用脚本化的方式触发执行，捕获完整的进程树信息。
- **日志聚合**：不仅收集脚本输出，还同步查询 Event Log（事件查看器）中的异常。
- **进程树清理**：测试结束后强制终止所有派生出的子进程。

##### 5. BMC 环境（Baseboard Management Controller）测试执行流程
- **管理通道建立**：连接 IPMI 接口或 Redfish REST API 端点。
- **带外控制**：执行远程重启、查询传感器列表。
- **固件升级测试**：验证 BMC 自身的升级逻辑及对主板固件的控制能力。
- **SEL 日志审计**：获取 System Event Log，解析其中包含的硬件故障信息。

#### 1.3.3 环境抽象层设计详细说明

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# 基础环境接口（Abstract Base Class）
class BaseTestEnvironment(ABC):
    """
    所有测试环境的基类，定义了环境生命周期的核心契约。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False
        self.logs = {}
        self.env_id = config.get("id", "default_env")
    
    @abstractmethod
    def init(self) -> bool:
        """初始化环境：启动虚拟机、建立 SSH 或重置硬件"""
        pass
    
    @abstractmethod
    def deploy(self, test_script: str, assets: List[str] = None) -> bool:
        """部署阶段：文件传输和执行权限设置"""
        pass
    
    @abstractmethod
    def execute(self, command: str, timeout: int = 300) -> 'TestResult':
        """执行阶段：触发测试逻辑并监控执行状态"""
        pass
    
    @abstractmethod
    def collect_logs(self) -> Dict[str, str]:
        """结果采集：汇总多源日志"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理阶段：销毁实例、释放锁定、清理现场"""
        pass

# QEMU环境实现示例
class QEMUEnvironment(BaseTestEnvironment):
    """QEMU虚拟机环境的具体实现"""
    
    def init(self) -> bool:
        # 1. 组装 QEMU 命令行参数 (arch, drive, netdev)
        # 2. 启动子进程并记录 PID
        # 3. 等待 SSH 端口就绪
        return True
    
    def deploy(self, test_script: str, assets: List[str] = None) -> bool:
        # 使用 scp 将脚本拷贝到 Guest OS 内部
        return True
    
    def execute(self, command: str, timeout: int = 300) -> 'TestResult':
        # 通过 SSH 远程调用并流式返回结果
        pass

# 目标板实现示例
class TargetBoardEnvironment(BaseTestEnvironment):
    """物理板卡环境实现"""
    
    def init(self) -> bool:
        # 1. 通过 IPMI 发送电源重置信号
        # 2. 监听串口直到进入登录提示符
        return True

    def collect_logs(self) -> Dict[str, str]:
        # 采集串口历史数据 + BMC SEL
        pass
```

#### 1.3.4 测试配置管理详细说明

##### 1. YAML 格式的测试配置
系统采用声明式配置，确保测试过程的可描述性和可控性。

```yaml
test_suite:
  name: "Memory Allocation Stress Tests"
  environment: "qemu"
  product_line: "arm_tf_v2"
  timeout: 600
  
  # 全局环境变量
  env_vars:
    MALLOC_PERTURB_: 165
    DEBUG_MODE: "1"
     
  test_cases:
    - id: "TC_MALLOC_001"
      name: "test_malloc_basic"
      type: "unit"
      script: "tests/test_malloc_basic.sh"
      expected_exit_code: 0
      # 断言逻辑
      assertions:
        - "allocated_memory > 0"
        - "return_ptr != NULL"
       
    - id: "TC_MALLOC_002"
      name: "test_malloc_stress"
      type: "stress"
      script: "tests/test_malloc_stress.sh"
      parameters:
        iterations: 1000
        block_size: 4096
      condition: "mem_size >= 512M" # 基于环境属性的条件运行
```

##### 2. 参数化与变量注入
- **维度过滤**：允许根据产品线 (SoC, Firmware Version) 动态选择不同的编译器标志或测试库。
- **Secrets 管理**：测试所需的认证令牌和 SSH 私钥通过加密的 Vault 注入。

##### 3. 动态生成测试
- **影响范围分析**：TestOrchestrator 接收来自 CodeAnalyzer 的修改函数列表，自动从案例库中匹配引用了这些函数的测试用例。
- **自动探索**：在缺乏现成用例时，基于 LLM 的建议自动生成简单的冒烟测试脚本。

#### 1.3.5 日志采集和标准化详细说明

##### 1. 日志源矩阵
- **stdout/stderr**: 测试脚本的直接输出。
- **系统日志**: `/var/log/syslog`, `/var/log/auth.log`, dmesg 内核缓冲区。
- **硬件指标**: CPU 使用率、IO 等待、内存压力指标 (Pressure Stall Information)。
- **外部通道**: 串口服务器 (Serial Console Server) 录制的原始字符流。

##### 2. 标准化格式 (LogEntry)
```python
from datetime import datetime
from dataclasses import dataclass

@dataclass
class LogEntry:
    timestamp: datetime          # 统一转换为 ISO 8601 UTC 时间
    level: str                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source: str                  # 标识来源: 'serial', 'dmesg', 'app_out'
    message: str                 # 清洗掉 ANSI 控制符后的原始文本
    context: dict                # 包含 host_id, pid 等元数据
```

#### 1.3.6 测试结果格式标准化
所有测试产出最终汇聚为 `TestResult` 对象，作为后续分析的输入。

```python
class TestResult:
    def __init__(self):
        self.test_id = ""                 # 任务唯一 ID
        self.test_name = ""               # 测试用例名称
        self.environment = ""             # 执行环境类型
        self.product_line = ""            # 目标产品线
        self.status = "PENDING"           # PASSED, FAILED, TIMEOUT, ERROR
        self.duration = 0.0               # 总耗时
        self.start_time = None
        self.end_time = None
        
        # 详细数据
        self.logs = {}                    # { 'stdout': '...', 'dmesg': '...' }
        self.assertions = []              # 存储 AssertionResult 列表
        self.errors = []                  # 捕获的异常信息列表
        self.metrics = {}                 # { 'avg_cpu': 15.5, 'peak_mem': 1024 }
        
        # 版本溯源
        self.code_version = ""            # Git Commit Hash
        self.config_id = ""               # 使用的配置文件版本
```

#### 1.3.7 核心 API 详细定义

```python
class TestOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        """加载环境拓扑配置和认证凭据"""
        pass
    
    def run_test_suite(self, suite_config: Dict[str, Any]) -> 'TestSuiteResult':
        """
        全自动化运行入口：
        1. 环境预检与锁定
        2. 部署资源
        3. 循环执行用例并实时监控
        4. 结果采集与标准化
        5. 资源释放
        """
        pass
    
    def run_single_test(self, case_id: str, env_id: str) -> TestResult:
        """针对特定环境运行单个测试案例"""
        pass
    
    def get_environment_health(self) -> Dict[str, Any]:
        """获取当前所有在线测试节点的状态报告"""
        pass
```

---

### 1.4 ResultAnalyzer 详细设计

#### 1.4.1 功能概述
ResultAnalyzer 是系统的故障诊断中心。它接收 TestOrchestrator 提供的标准化结果，通过语义分析、模式匹配和差分对比，挖掘失败背后的深层次原因。其核心价值在于将海量的、非结构化的文本日志转化为精准的“修复指令”。

核心能力：
- **日志语义化解析**：识别日志中的时间序列、模块分层和因果关系。
- **故障特征提取**：提取崩溃堆栈 (Stack Trace)、内存地址和寄存器快照。
- **多维度根因分析 (RCA)**：结合代码变更和历史数据，锁定故障发生的源头文件。
- **自动化经验沉淀**：将经过人工确认的修复案例转化为知识向量。

#### 1.4.2 日志解析规则引擎详细说明

##### 1. 正则模式库
系统内置了专门针对 C/C++ 嵌入式开发的故障模式库。

```python
class LogPattern:
    name: str                      # 唯一标识
    regex: str                     # 捕获正则
    error_type: str                # 映射到错误分类
    severity: str                  # 预警级别
    action_hint: str               # 给 AI 代理的操作提示

# 模式库示例
ERROR_PATTERNS = [
    LogPattern(
        name="segfault",
        regex=r"Segmentation fault \(SIGSEGV\) at 0x([0-9a-f]+)",
        error_type="SyntaxError",
        severity="CRITICAL",
        action_hint="Check for null pointer dereference or out-of-bounds access."
    ),
    LogPattern(
        name="double_free",
        regex=r"double free or corruption",
        error_type="ResourceError",
        severity="HIGH",
        action_hint="Investigate memory management logic in the affected block."
    ),
    LogPattern(
        name="stack_overflow",
        regex=r"stack smashing detected",
        error_type="SyntaxError",
        severity="CRITICAL",
        action_hint="Verify buffer sizes and recursion depth."
    )
]
```

##### 2. 多行日志识别与聚合
- **堆栈帧提取**：识别 `at <func_name> (<file>:<line>)` 格式的行并构建完整的调用链路。
- **上下文回溯**：在检测到错误点时，自动向前保留 100 行 `DEBUG` 日志，以便分析故障前夕的系统状态。

#### 1.4.3 错误分类系统详细说明

错误被严格划分为以下分类，以指导后续的 Agent 策略：
- **SYNTAX_ERROR (语法/运行时基本错误)**: 如段错误、指令异常、非法访问。
- **LOGIC_ERROR (逻辑错误)**: 结果不符预期、业务断言失败。
- **RESOURCE_ERROR (资源相关)**: 内存泄漏、FD (文件描述符) 耗尽、死锁。
- **TIMEOUT_ERROR (超时)**: 进程由于锁定或死循环未能退出。
- **ENVIRONMENT_ERROR (环境问题)**: 硬件掉线、依赖缺失、网络波动。

#### 1.4.4 根因分析详细说明

##### 1. 链式回溯
- **代码映射**：将日志中的函数名与 `CodeAnalyzer` 生成的符号表关联。
- **路径搜索**：基于 CFG (控制流图) 判断修改点是否在报错点的调用路径上。

##### 2. 差分对比分析
- **历史对齐**：选取同用例最近一次成功的运行日志作为“基准线”。
- **差异提取**：利用 `diff` 算法提取失败日志中独有的输出行，排除掉正常的系统底噪日志。

##### 3. RCA 报告结构
```python
class RootCauseAnalysis:
    def __init__(self):
        self.primary_reason = ""           # 核心原因摘要
        self.suspected_files = []          # 嫌疑文件列表
        self.evidence_snippets = []        # 证据片段
        self.confidence_score = 0.0        # 置信度 (0.0-1.0)
        self.is_regression = False         # 是否为回归问题
```

#### 1.4.5 经验知识提取详细说明
每当一个失败的测试在代码修改后转为成功，ResultAnalyzer 会自动提取“修复对”。

- **特征计算**：对失败日志进行脱敏处理，提取其指纹。
- **存储方案**：将（故障指纹, 修复 Patch, 开发者备注）存入向量数据库，供未来遇到相似问题时进行 RAG (检索增强生成) 检索。

#### 1.4.6 核心 API 详细定义

```python
class ResultAnalyzer:
    def __init__(self, pattern_db_path: Optional[str] = None):
        """加载自定义模式库"""
        pass
    
    def analyze_failure(self, result: TestResult) -> RootCauseAnalysis:
        """
        主分析入口：
        1. 模式匹配识别直接错误
        2. 提取堆栈信息
        3. 执行差分分析
        4. 输出根因分析报告
        """
        pass
    
    def parse_raw_logs(self, raw_text: str) -> List[LogEntry]:
        """将非结构化流解析为结构化 LogEntry 列表"""
        pass
    
    def compare_runs(self, run_a: TestResult, run_b: TestResult) -> 'RunComparison':
        """对比两次运行的日志和指标差异"""
        pass
```

#### 1.4.7 数据结构详细定义

```python
class StructuredLogs:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.entries: List[LogEntry] = []
        self.error_blocks: List[str] = []

class CallFrame:
    def __init__(self):
        self.function_name = ""
        self.file_name = ""
        self.line_no = 0
        self.address = "0x0"
```

#### 1.4.8 设计决策补充
1. **为什么先使用规则引擎？**
   - **效率**：处理 GB 级别的串口日志时，正则过滤比调用大模型便宜且快速。
   - **确定性**：对于已知的 Assert 输出，规则能提供 100% 准确的分类。
2. **多源数据融合**：
   - 分析不仅看 `stdout`，必须结合硬件监控指标。例如：如果日志报错 `timeout` 同时指标显示 CPU 100%，则极大可能是死循环。
3. **闭环反馈机制**：
   - ResultAnalyzer 的输出直接作为 CodeModifier 的 Input Prompt 的一部分，实现真正的自愈闭环。

---

## 2. Data Models

### 2.1 Code Modification Record
```json
{
  "record_id": "uuid",
  "commit_hash": "string",
  "file_path": "string",
  "change_diff": "string",
  "reasoning": "string",
  "affected_files": ["string"],
  "validation_status": {
    "syntax": "PASS/FAIL",
    "compile": "PASS/FAIL",
    "lint": "PASS/FAIL",
    "symbol": "PASS/FAIL",
    "signature": "PASS/FAIL"
  },
  "timestamp": "iso-datetime",
  "applied": "boolean"
}
```

### 2.2 Test Execution Record
```json
{
  "test_id": "string",
  "environment": {
    "type": "QEMU/BMC/Board",
    "config": {
      "image": "path/to/img",
      "mem": "512M",
      "arch": "arm/riscv"
    }
  },
  "logs": "string",
  "result": "PASS/FAIL/ERROR",
  "duration": "float",
  "coverage_report": "path/to/report",
  "artifacts": ["path1", "path2"]
}
```

### 2.3 Knowledge Unit
```json
{
  "id": "uuid",
  "type": "Experience/Log/Doc",
  "tags": {
    "product_line": "SoC_A",
    "component": "Kernel",
    "error_type": "NULL_PTR",
    "severity": "HIGH"
  },
  "content": "string",
  "vector": [0.1, 0.2, "..."],
  "source": "Redmine #1234",
  "created_at": "iso-datetime"
}
```

## 3. API and Interface Design

### 3.1 Agent Communication
-   **Transport**: Internal message bus (RabbitMQ) or gRPC for high-performance RPC.
-   **Format**: Protocol Buffers or OpenAI-compatible tool call JSON format.

### 3.2 Knowledge Query Interface
- `query_similar_issues(error_log: str, tags: dict, top_k: int) -> List[KnowledgeUnit]`
- `add_knowledge_unit(unit: KnowledgeUnit) -> bool`

### 3.3 Test Execution Interface
- `run_suite(suite_id: str, env_profile: str) -> JobID`
- `cancel_job(job_id: str) -> bool`
- `get_job_logs(job_id: str) -> str`

## 4. Configuration and Strategies

### 4.1 Agent Configuration
- `model_name`: "gpt-4-turbo" or "claude-3-5-sonnet"
- `temperature`: 0.1 (low for code generation tasks)
- `max_retries`: 3 (number of times to retry on validation failure)
- `timeout_sec`: 60 (LLM API timeout)

### 4.2 Retrieval Strategy
- **Hybrid Search**: Combining keyword match (Elasticsearch BM25) and vector similarity (FAISS/Milvus).
- **Weighting**: `Total_Score = 0.4 * BM25 + 0.6 * Vector_Sim`.

## 5. Security and Reliability

### 5.1 Sandbox Execution
- **Isolation**: All build and test processes are isolated in Docker containers.
- **Resource Constraints**: CPU (max 4 cores), RAM (max 8GB), Disk IO (max 100MB/s) limits.
- **Network**: No external network access during test execution.

### 5.2 Code Integrity
- **Signatures**: Digital signatures for all patches generated by CodeModifier.
- **Human-in-the-Loop**: Mandatory manual approval flag for critical system files (e.g., bootloader, kernel core).
- **Rollback Consistency**: Atomic rollback ensuring the entire project is returned to the baseline commit.

## 6. Conclusion
The detailed design of CodeAnalyzer and CodeModifier provides a robust foundation for an AI-driven firmware testing and fixing system. By combining deep static analysis with a multi-layered validation pipeline, the system ensures that AI-generated fixes are not only logically sound but also meet industrial quality standards.
