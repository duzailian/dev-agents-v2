# AI驱动固件智能测试系统 - 项目指挥部

> 项目指挥部文件用于记录所有关键信息，确保跨session无缝衔接
> 每次session开始时，首先阅读此文件了解项目现状

## 📋 项目基本信息

**项目名称**：AI驱动的智能化固件测试系统  
**用户身份**：PC/服务器CPU芯片原厂固件开发工程师  
**项目目标**：建立一套能自动修改C代码→启动测试→获取结果→决策循环的AI智能体系统  
**仓库**：dev-agents-v2  
**GitHub**: https://github.com/duzailian/dev-agents-v2

## 🎯 用户的18点核心需求

### 核心功能需求
1. 自动修改C语言代码（基于AI建议）
2. 启动测试（QEMU或目标板）
3. 获取测试结果
4. 根据结果反馈自动决策是否继续循环

### 测试环境需求
- 支持QEMU环境
- 支持目标板（BMC、树莓派、Windows脚本）

### 知识库需求
- 结构化输出修改→测试→分析的经验数据
- 产品线差异化支持（不同标签优先检索）
- 文档导入和对话接口
- Redmine集成

### 工程实践需求
- 充分模块化设计
- 详尽的代码注释和文档
- 利用开源工具加速
- Claude Code Skills可选集成
- GitLab CI集成
- Agent优先的实现策略

## 🔧 推荐Tech Stack

```
多Agent协调：CrewAI
状态机：LangGraph
RAG知识库：LangChain
向量数据库：Qdrant
执行引擎：CodeAnalyzer、CodeModifier、TestOrchestrator、ResultAnalyzer
API：内网大模型API（优先）
```

## 📊 工作计划（6大阶段）

| Phase | 任务 | 状态 | 预计时间 |
|-------|------|------|--------|
| **1** | 架构设计与需求分析 | 🔄 进行中 | 5-7天 |
| **2** | 核心模块实现 | ⏳ 待开始 | 7-10天 |
| **3** | RAG知识库系统 | ⏳ 待开始 | 5-7天 |
| **4** | Multi-Agent系统 | ⏳ 待开始 | 5-7天 |
| **5** | 集成与优化 | ⏳ 待开始 | 4-6天 |
| **6** | 测试与部署 | ⏳ 待开始 | 3-5天 |

## 🎯 Phase 1 目标（架构设计与需求分析）

需要输出7个关键文档：
1. ✅ ARCHITECTURE_V2.md - 系统架构设计
2. ✅ REQUIREMENTS.md - 需求规范
3. ✅ KNOWLEDGE_SCHEMA.md - 知识库数据结构
4. ✅ AGENT_DESIGN.md - Agent详细设计
5. ✅ STATE_MACHINE.md - 状态机设计
6. ✅ WORK_PLAN_V2.md - 分阶段工作计划
7. ✅ DETAILED_DESIGN_V2.md - 融合详细设计

> 注：上述7个文档为本阶段计划产出；当前PR仅创建“指挥部/拆分清单”两个入口文件。

## 📋 Phase 1 的任务拆分（小粒度）

由于任务太大导致无法自动执行，拆分为以下小任务：

### 任务1-1：需求分析和REQUIREMENTS.md
- 输出：docs/REQUIREMENTS.md ✅
- 内容：18点需求的详细规范（含验收条件/优先级/追溯）
- 预计行数：400-500行（已完成：约480行）

### 任务1-2：知识库Schema设计和KNOWLEDGE_SCHEMA.md ✅
- 输出：docs/KNOWLEDGE_SCHEMA.md ✅
- 内容：KnowledgeUnit数据模型、产品线标签、Qdrant配置、PostgreSQL schema、查询示例
- 预计行数：300-400行（实际输出：400+行）
- 完成时间：2026-01-27

### 任务1-3：系统架构设计和ARCHITECTURE_V2.md ✅
- 输出：docs/ARCHITECTURE_V2.md ✅
- 内容：分层架构、Agent设计、RAG架构
- 预计行数：500-600行（实际输出：500+行）
- 完成时间：2026-01-27

### 任务1-4：Agent和状态机设计（AGENT_DESIGN.md + STATE_MACHINE.md）
- 输出：AGENT_DESIGN.md、STATE_MACHINE.md
- 内容：4个Agent详细设计、状态转移图、循环控制
- 预计行数：600-700行

### 任务1-5：工作计划和汇总（WORK_PLAN_V2.md + DETAILED_DESIGN_V2.md）
- 输出：WORK_PLAN_V2.md、DETAILED_DESIGN_V2.md
- 内容：6阶段工作计划、融合详细设计
- 预计行数：700-800行

## 📊 当前进度

**总体完成度**：约 40%（已完成任务1-1、1-2、1-3）

```
✅ 已完成：
- 项目规划和需求澄清
- Tech Stack评估和确认
- 任务1-1：docs/REQUIREMENTS.md（需求规范）
- 任务1-2：docs/KNOWLEDGE_SCHEMA.md（知识库数据结构设计）
- 任务1-3：docs/ARCHITECTURE_V2.md（系统架构设计）

🔄 进行中：
- Phase 1 架构设计与需求分析（准备进入任务1-4）

⏳ 待开始：
- Phase 2-6 的所有工作
- 任务1-4：Agent和状态机设计
- 任务1-5：工作计划和融合设计
```

## 🔗 关键文档链接

**项目文档**：
- docs/ARCHITECTURE_V2.md （待创建）
- docs/REQUIREMENTS.md ✅
- docs/KNOWLEDGE_SCHEMA.md （待创建）
- docs/AGENT_DESIGN.md （待创建）
- docs/STATE_MACHINE.md （待创建）
- docs/WORK_PLAN_V2.md （待创建）
- docs/DETAILED_DESIGN_V2.md （待创建）

**进度追踪**：
- docs/PROJECT_COMMAND_CENTER.md （本文件）
- docs/PHASE_1_TASK_BREAKDOWN.md
- docs/DETAILED_DESIGN_PROGRESS.md （旧的）

## 🚀 下次session的快速开始

1. 首先打开本文件（PROJECT_COMMAND_CENTER.md）
2. 查看"当前进度"和"工作计划（6大阶段）"
3. 找到对应的小任务（任务1-1、1-2等）
4. 执行下一个未完成的任务

例如：
- 如果任务1-1已完成 ✅，则执行任务1-2
- 如果任务1-2已完成 ✅，则执行任务1-3
- 等等...

## 📌 重要注意事项

1. **任务要拆分小** - 每个任务必须是可独立完成的、内容清晰的
2. **进度要更新** - 每完成一个任务，立即更新本文件的"当前进度"
3. **文档要详尽** - 所有关键信息都要写入文档，不依赖对话历史
4. **跨session接力** - 新session时只需查看本文件和相关输出文档

## 📝 版本历史

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-01-27 | v1.0 | 创建项目指挥部，完成Phase 1任务拆分规划 |

---

**最后更新**：2026-01-27  
**维护者**：AI Agent  
**下次更新时间**：完成任务1-3后
