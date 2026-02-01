# Project Directory Structure

> 文档版本：v2.0
> 
> 更新日期：2026-01-31
> 
> 说明：本文档描述项目的实际目录结构，与代码库保持同步。

## 实际目录结构

```text
dev-agents-v2/
├── docs/                                          # Documentation
│   ├── PROJECT_COMMAND_CENTER.md                  # 项目指挥中心（必须首先查看）
│   ├── PHASE_2_TASK_BREAKDOWN.md                  # Phase 2任务分解
│   ├── REQUIREMENTS.md                            # 需求规范
│   ├── ARCHITECTURE_V2.md                         # 系统架构设计V2
│   ├── KNOWLEDGE_SCHEMA.md                        # 知识库Schema
│   ├── AGENT_DESIGN.md                            # Agent详细设计
│   ├── STATE_MACHINE.md                           # 状态机设计
│   ├── WORK_PLAN_V2.md                            # 工作计划V2
│   ├── DETAILED_DESIGN_V2.md                      # 详细设计V2
│   ├── API_SPEC.md                                # API规范
│   ├── CONFIG_MANAGEMENT.md                       # 配置管理设计
│   ├── ADR.md                                     # 架构决策记录
│   ├── DIR_STRUCTURE.md                           # 本文档
│   ├── poc_report.md                              # POC验证报告
│   ├── SESSION_HANDOFF.md                         # 会话交接指南
│   ├── PROJECT_CONTEXT_HANDOFF.md                 # Session重启文档
│   └── plans/                                     # 计划文档目录
│       └── 2026-01-31-security-implementation.md  # 安全实现计划
│
├── src/                                           # Source code
│   ├── agents/                                    # Agent层（LangGraph节点）
│   │   ├── __init__.py                            # 模块导出
│   │   ├── base_agent.py                          # BaseAgent抽象基类
│   │   ├── code_agent.py                          # CodeAgent（代码分析与修改）
│   │   ├── test_agent.py                          # TestAgent（测试执行）
│   │   ├── analysis_agent.py                      # AnalysisAgent（结果分析）
│   │   └── kb_agent.py                            # KBAgent（知识库管理）
│   │
│   ├── tools/                                     # 核心引擎层
│   │   ├── __init__.py
│   │   ├── code_analysis/                         # 代码分析引擎
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py                        # CodeAnalyzer主类
│   │   │   ├── parser.py                          # Tree-sitter解析器
│   │   │   ├── symbol_table.py                    # 符号表
│   │   │   ├── call_graph.py                      # 调用图
│   │   │   └── static_analyzers.py                # 静态分析器
│   │   │
│   │   ├── code_modification/                     # 代码修改引擎
│   │   │   ├── __init__.py
│   │   │   ├── modifier.py                        # CodeModifier（补丁应用）
│   │   │   ├── patch_generator.py                 # 补丁生成器
│   │   │   └── safety_checker.py                  # 安全检查器
│   │   │
│   │   ├── test_orchestration/                    # 测试编排引擎
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py                    # TestOrchestrator
│   │   │   ├── environment_manager.py             # 环境管理器
│   │   │   └── models.py                          # 数据模型
│   │   │
│   │   └── result_analysis/                       # 结果分析引擎
│   │       ├── __init__.py
│   │       ├── analyzer.py                        # ResultAnalyzer
│   │       ├── log_parser.py                      # 日志解析器
│   │       ├── decision_engine.py                 # 决策引擎
│   │       └── models.py                          # 数据模型
│   │
│   ├── models/                                    # 数据模型层
│   │   ├── __init__.py
│   │   └── code.py                                # 代码分析相关模型
│   │
│   ├── security/                                  # 安全层
│   │   ├── __init__.py
│   │   └── secret_filter.py                       # 敏感信息过滤
│   │
│   ├── api/                                       # API层（待实现）
│   ├── executor/                                  # 执行引擎层（待实现）
│   ├── knowledge/                                 # 知识库层（待实现）
│   ├── config/                                    # 配置层（待实现）
│   └── utils/                                     # 工具层（待实现）
│
├── tests/                                         # 测试代码
│   ├── __init__.py
│   ├── test_analyzer.py                           # CodeAnalyzer测试
│   ├── test_code_analyzer.py                      # 代码分析集成测试
│   ├── test_parser.py                             # Parser测试
│   ├── test_call_graph.py                         # 调用图测试
│   ├── test_symbol_table.py                       # 符号表测试
│   ├── test_modifier.py                           # CodeModifier测试
│   ├── test_static_analyzers.py                   # 静态分析器测试
│   ├── test_safety_checker.py                     # 安全检查器测试
│   └── test_secret_filter.py                      # Secret过滤测试
│
├── .github/                                       # CI/CD配置
│   └── workflows/
│       └── document-check.yml                     # 文档版本检查
│
├── requirements.txt                               # Python依赖
├── README.md                                      # 项目概述
├── CLAUDE.md                                      # Claude Code指导文件
├── USER_GUIDE.md                                  # 用户指南
└── pyproject.toml                                 # 项目配置
```

## 目录说明

### 已实现模块 (Phase 2)

| 模块 | 状态 | 说明 |
|------|------|------|
| agents/ | ✅ 完成 | 4个Agent实现（BaseAgent, CodeAgent, TestAgent, AnalysisAgent, KBAgent） |
| tools/code_analysis | ✅ 完成 | CodeAnalyzer, TreeSitterParser, SymbolTable, CallGraph |
| tools/code_modification | ✅ 完成 | CodeModifier, PatchGenerator, SafetyChecker |
| tools/test_orchestration | ✅ 完成 | TestOrchestrator, EnvironmentManager |
| tools/result_analysis | ✅ 完成 | ResultAnalyzer, LogParser, DecisionEngine |
| models/ | ✅ 完成 | Code Models |
| security/ | ✅ 完成 | SecretFilter |

### 待实现模块 (Phase 3+)

| 模块 | 优先级 | 说明 |
|------|--------|------|
| api/ | P1 | FastAPI REST API服务 |
| executor/ | P1 | QEMU/Board/BMC执行引擎 |
| knowledge/ | P1 | Qdrant + PostgreSQL知识库 |
| config/ | P2 | 配置加载和验证 |
| utils/ | P2 | 共享工具函数 |

## 注意事项

1. **Tree-sitter兼容性**: parser.py使用tree-sitter 0.21.3，某些API（如QueryCursor）与新版有差异
2. **Windows路径问题**: tree-sitter-c在Windows上可能存在解析问题
3. **Agent集成**: LangGraph状态机集成待实现（Phase 2.5）

## 相关文档

- [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) - 系统架构设计
- [DETAILED_DESIGN_V2.md](DETAILED_DESIGN_V2.md) - 详细设计规格
- [AGENT_DESIGN.md](AGENT_DESIGN.md) - Agent详细设计
```
