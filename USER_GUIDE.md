# 项目开发指引与架构落地方案 (USER_GUIDE.md)

> **文档版本**：v1.0
> **创建日期**：2026-01-30
> **目标用户**：PC/服务器CPU芯片原厂固件开发工程师
> **用途**：作为跨Session开发任务的上下文指引和架构参考

---

## 1. 需求覆盖与设计状态

本项目（Dev-Agents V2）已完成详细架构设计，**完美覆盖了用户提出的19点核心需求**。

### 1.1 核心需求满足情况

| 需求点 | 解决方案/设计模块 | 状态 |
| :--- | :--- | :--- |
| **闭环自愈 (改代码->测试->分析)** | **LangGraph 状态机** (Layer 6) 定义了完整的自动化闭环流程。 | ✅ 设计完成 |
| **知识库与经验沉淀** | **KBAgent** + **Qdrant**，采用 `KnowledgeUnit` 结构化存储经验。 | ✅ 设计完成 |
| **模型策略 (API -> 微调)** | 架构解耦 **Model Provider**，支持配置切换，数据结构支持微调数据导出。 | ✅ 设计完成 |
| **多环境支持 (QEMU/板卡)** | **TestEnvAdapter** (Layer 3) 抽象层，统一 QEMU、BMC、Windows 接口。 | ✅ 设计完成 |
| **产品线差异化** | **知识库标签体系** (`product_line`) 实现分产品线检索与通用检索降级。 | ✅ 设计完成 |
| **外部集成 (Redmine/GitLab)** | **Service Layer** (Layer 4) 定义了标准集成接口。 | ✅ 设计完成 |
| **文档导入 (PDF/Word/Excel)** | **DocumentProcessor** 模块支持多格式解析与知识提取。 | ✅ 设计完成 |

### 1.2 当前项目进度

*   **Phase 1 (架构与设计)**：🟢 **100% 完成**
    *   输出：需求规范、架构设计、Agent设计、状态机设计、知识库Schema。
*   **Phase 2 (核心模块实现)**：🟡 **启动中 (0%)**
    *   目标：实现 CodeAnalyzer, CodeModifier, TestOrchestrator, ResultAnalyzer。
*   **Phase 3 (知识库系统)**：⚪ 待开始
*   **Phase 4 (多Agent集成)**：⚪ 待开始

---

## 2. 架构设计概览

采用 **7层分层架构**，确保模块化与可维护性。

```mermaid
graph TD
    User[用户/CLI/CI] --> L7_App

    subgraph "Layer 7: 应用层"
        L7_App[CLI / API / Claude Skills]
    end

    subgraph "Layer 6: 编排层 (LangGraph)"
        SM[状态机 (State Machine)]
        SM -->|调度| Agents
    end

    subgraph "Layer 5: 智能体层 (Agents)"
        CodeAgent[CodeAgent<br/>代码专家]
        TestAgent[TestAgent<br/>测试专家]
        AnalysisAgent[AnalysisAgent<br/>分析专家]
        KBAgent[KBAgent<br/>知识专家]
    end

    subgraph "Layer 4: 核心引擎层 (Engines)"
        Analyzer[CodeAnalyzer<br/>Tree-sitter]
        Modifier[CodeModifier<br/>Patch Gen]
        Orchestrator[TestOrchestrator<br/>QEMU/Board]
        ResAnalyzer[ResultAnalyzer<br/>Log Analysis]
    end

    subgraph "Layer 3: 适配层 (Adapters)"
        EnvAdapter[环境适配器]
        GitLabAdapter[GitLab集成]
        RedmineAdapter[Redmine集成]
    end

    subgraph "Layer 2: 数据层 (Data)"
        Qdrant[(向量库)]
        PG[(关系库)]
        FS[文件系统]
    end

    Agents --> Analyzer
    Agents --> Modifier
    Agents --> Orchestrator
    Agents --> ResAnalyzer

    Orchestrator --> EnvAdapter
    KBAgent --> Qdrant
```

---

## 3. 下一步开发计划 (Phase 2)

请在新的 Session 中按照以下顺序执行开发任务：

### 任务 2-1：核心分析引擎 (CodeAnalyzer)
*   **目标**：实现 C 代码的解析与理解能力。
*   **文件**：`src/tools/code_analysis/analyzer.py`
*   **关键点**：集成 Tree-sitter，实现函数提取、依赖分析。

### 任务 2-2：代码修改引擎 (CodeModifier)
*   **目标**：实现基于 LLM 建议的代码修改与 Patch 生成。
*   **文件**：`src/tools/code_modification/modifier.py`
*   **关键点**：Patch 生成、安全检查、应用与回滚。

### 任务 2-3：测试编排器 (TestOrchestrator)
*   **目标**：实现测试环境的生命周期管理。
*   **文件**：`src/executor/orchestrator.py`
*   **关键点**：QEMU 启动/停止，日志收集接口。

### 任务 2-4：结果分析器 (ResultAnalyzer)
*   **目标**：实现测试日志的智能分析。
*   **文件**：`src/tools/result_analysis/analyzer.py`
*   **关键点**：错误模式匹配，根因推断。

---

## 4. 关键文档索引

*   **项目总控与进度**：`docs/PROJECT_COMMAND_CENTER.md`
*   **详细架构定义**：`docs/ARCHITECTURE_V2.md`
*   **Agent 详细设计**：`docs/AGENT_DESIGN.md`
*   **状态机逻辑**：`docs/STATE_MACHINE.md`
*   **Phase 2 任务详单**：`docs/PHASE_2_TASK_BREAKDOWN.md`

---

**使用说明**：
在开启新的 Claude Session 时，请告知助手：“**请查看 USER_GUIDE.md 和 docs/PROJECT_COMMAND_CENTER.md，并开始 Phase 2 的任务 2-1 开发工作。**”
