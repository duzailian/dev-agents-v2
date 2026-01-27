# AI驱动固件智能测试系统

## 快速开始

### 第一步：查看项目指挥部

打开 [docs/PROJECT_COMMAND_CENTER.md](docs/PROJECT_COMMAND_CENTER.md) 了解：
- 项目目标和用户需求
- 技术栈选择
- 6大阶段工作计划
- 当前进度

### 第二步：查看任务拆分

打开 [docs/PHASE_1_TASK_BREAKDOWN.md](docs/PHASE_1_TASK_BREAKDOWN.md) 了解：
- Phase 1的5个小任务
- 每个任务的具体内容
- 执行顺序和进度追踪

### 第三步：执行当前任务

根据进度追踪表，找到下一个待执行的任务，并执行它。

## 文档结构

```text
docs/
├── PROJECT_COMMAND_CENTER.md    # 项目指挥部（首先查看此文件）
├── PHASE_1_TASK_BREAKDOWN.md    # Phase 1任务拆分（然后查看此文件）
├── CLEANUP_LOG.md               # 文档清理日志
├── REQUIREMENTS.md              # 需求规范（已完成）
├── ARCHITECTURE_V2.md           # 系统架构设计（已完成）
├── KNOWLEDGE_SCHEMA.md          # 知识库schema（已完成）
├── AGENT_DESIGN.md              # Agent详细设计（已完成）
├── STATE_MACHINE.md             # 状态机设计（已完成）
├── WORK_PLAN_V2.md              # 工作计划V2（已完成）
├── DETAILED_DESIGN_V2.md        # 详细设计V2（已完成）
├── API_SPEC.md                  # API规范（现有）
├── DIR_STRUCTURE.md             # 目录结构（现有）
├── WORK_PLAN.md                 # 旧工作计划（已过期，仅作参考）
├── PROJECT_PROGRESS.md          # 历史进度记录（如需可参考）
└── TASK_CONTEXT_GUIDE.md        # 任务写作/交付上下文指引
```

## 技术栈

- 多Agent协调：CrewAI
- 状态机：LangGraph
- RAG知识库：LangChain
- 向量数据库：Qdrant
- 执行引擎：CodeAnalyzer、CodeModifier、TestOrchestrator、ResultAnalyzer
- 大模型API：内网已部署的API（优先）

## 获取更多信息

- 项目目标和需求：[PROJECT_COMMAND_CENTER.md](docs/PROJECT_COMMAND_CENTER.md)
- 当前任务详情：[PHASE_1_TASK_BREAKDOWN.md](docs/PHASE_1_TASK_BREAKDOWN.md)
- API规范：[API_SPEC.md](docs/API_SPEC.md)
- 目录结构：[DIR_STRUCTURE.md](docs/DIR_STRUCTURE.md)

最后更新：2026-01-27
