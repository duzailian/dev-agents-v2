# 项目上下文交接文档 (PROJECT_CONTEXT_HANDOFF)

> 文档版本：v1.0
> 创建日期：2026-01-30
> 目的：为新会话提供无缝继续工作所需的完整上下文

---

## 1. 项目当前状态

### 1.1 总体进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1 | ✅ 已完成 | 架构设计与需求分析 |
| Phase 2 | 🔄 进行中 | 核心模块实现 |
| 文档质量改进 | 🔄 进行中 | P0已完成，P1待修复 |

### 1.2 文档质量改进进度

| 优先级 | 问题 | 状态 |
|--------|------|------|
| P0-1 | DETAILED_DESIGN_V2.md 补充核心引擎设计 | ✅ 已完成（2513行） |
| P0-2 | API_SPEC.md 重写为OpenAPI 3.0规范 | ✅ 已完成（1746行） |
| P1-1 | REQUIREMENTS.md 补充TR/KR章节 | ✅ 已完成（865行） |
| P1-2 | AGENT_DESIGN.md 扩展KBAgent章节 | ✅ 已完成 |
| P1-3 | PHASE_2_TASK_BREAKDOWN.md 添加POC任务 | ✅ 已完成 |
| P1-4 | STATE_MACHINE.md 合并重复定义 | ✅ 已完成 |

---

## 2. 待修复P1问题详情

### 2.1 P1-2: AGENT_DESIGN.md KBAgent章节扩展

**文件路径**: `D:\workspace\dev-agents-v2\docs\AGENT_DESIGN.md`

**问题描述**:
- KBAgent章节仅约30行（第265-293行附近）
- 其他Agent（CodeAgent、TestAgent、AnalysisAgent）章节均有50+行详细设计
- 缺少RAG检索流程详细设计
- 缺少知识沉淀触发机制
- 缺少与其他Agent的交互协议

**修复方案**:
在KBAgent章节添加以下内容：

```markdown
#### 4.4.3 RAG检索流程

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG检索流程                               │
├─────────────────────────────────────────────────────────────┤
│  1. 接收查询请求（来自其他Agent或用户）                        │
│  2. 查询预处理（分词、实体提取、意图识别）                      │
│  3. 向量化查询（使用Embedding模型）                           │
│  4. Qdrant向量检索（TopK + 阈值过滤）                         │
│  5. 混合检索（关键词 + 语义 + 产品线过滤）                     │
│  6. 结果重排序（基于相关性和时效性）                           │
│  7. 上下文构建（格式化为LLM可理解的上下文）                     │
│  8. 返回检索结果                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 4.4.4 知识沉淀机制

**触发条件**:
- 任务成功完成（next_action == "finish" 且 all_passed == True）
- 人工标记为有价值的失败案例
- 达到可配置的沉淀阈值（如连续3次相似修复）

**沉淀内容**:
- 输入：代码diff、问题描述、环境配置
- 过程：修改建议、测试计划、迭代历史
- 输出：最终修复、根因分析、经验总结

#### 4.4.5 与其他Agent的交互协议

| 交互方向 | 触发时机 | 数据内容 |
|----------|----------|----------|
| CodeAgent → KBAgent | 代码分析前 | 查询相似问题和历史修复 |
| TestAgent → KBAgent | 测试失败时 | 查询相似失败模式 |
| AnalysisAgent → KBAgent | 根因分析时 | 查询历史根因和修复建议 |
| KBAgent → 所有Agent | 任务完成后 | 沉淀知识单元，更新向量索引 |
```

**预计新增行数**: 40-50行

---

### 2.2 P1-3: PHASE_2_TASK_BREAKDOWN.md 添加POC任务

**文件路径**: `D:\workspace\dev-agents-v2\docs\PHASE_2_TASK_BREAKDOWN.md`

**问题描述**:
- 当前任务从2-1开始，缺少2-0 POC验证任务
- 未包含LangGraph集成验证
- 未包含Tree-sitter集成验证
- 未包含Qdrant部署验证

**修复方案**:
在任务2-1之前添加任务2-0章节：

```markdown
## 任务2-0：技术POC验证

**任务描述**：
在正式开发前，对关键技术组件进行概念验证，确保技术方案可行

**预计时间**：1-2天

**验证项目**：

### 2-0-1 LangGraph集成验证
- 目标：验证LangGraph状态机可正确控制多Agent工作流
- 验证内容：
  - StateGraph创建和节点添加
  - 条件边和状态转移
  - 状态持久化和恢复
  - 与LangChain Agent的集成
- 成功标准：
  - 能够定义包含4个节点的工作流
  - 状态转移逻辑正确执行
  - 循环控制机制生效

### 2-0-2 Tree-sitter集成验证
- 目标：验证Tree-sitter能够正确解析C代码
- 验证内容：
  - tree-sitter-c语言包安装
  - AST生成和遍历
  - 函数定义提取
  - 符号表构建
- 成功标准：
  - 能够解析标准C11代码
  - 正确提取函数签名和调用关系
  - 性能满足要求（<1秒/1000行）

### 2-0-3 Qdrant部署验证
- 目标：验证Qdrant向量数据库可正常部署和使用
- 验证内容：
  - Docker容器部署
  - Collection创建和配置
  - 向量插入和检索
  - 元数据过滤查询
- 成功标准：
  - 容器稳定运行
  - 检索延迟<100ms
  - 支持产品线标签过滤

**完成标准**：
- [ ] 所有POC验证通过
- [ ] 编写POC验证报告（docs/poc_report.md）
- [ ] 记录发现的问题和解决方案
```

**预计新增行数**: 50-60行

---

### 2.3 P1-4: STATE_MACHINE.md 合并重复定义

**文件路径**: `D:\workspace\dev-agents-v2\docs\STATE_MACHINE.md`

**问题描述**:
- 5.19节（约第345-945行）定义了ConvergenceCriteria，使用pass_rate/improvement_rate算法
- 第6节（约第961-1615行）再次定义ConvergenceCriteria，使用numpy实现，结构不同
- 两处定义存在细微差异，可能导致实现混淆

**修复方案**:

1. **保留第6节作为规范定义**（更完整、有numpy实现）

2. **修改5.19节为引用**，替换为：

```markdown
### 5.19 收敛判断 (Convergence Check)

> 详细的收敛判断算法和实现请参见第6节"收敛判断详细设计"。

**核心概念**:
- 收敛判断用于决定迭代循环是否应该终止
- 基于测试通过率、改进率、迭代次数等多维度指标
- 支持5种收敛类型：SUCCESS、FAILURE、PLATEAUED、TIMEOUT、CONVERGED_WITH_IMPROVEMENT

**触发时机**:
- 每次迭代完成后，在RESULT_ANALYSIS状态中调用
- 由AnalysisAgent的decide_action工具执行

**与决策引擎的关系**:
收敛判断结果直接影响next_action的选择：
- converged=True + type=SUCCESS → next_action="finish"
- converged=True + type=FAILURE → next_action="escalate"
- converged=True + type=PLATEAUED → 根据ExecutionMode决定
- converged=False → next_action="continue"
```

**预计修改**: 删除约50行重复内容，保留10-15行引用说明

---

## 3. 新会话继续工作指南

### 3.1 快速启动命令

在新会话中，发送以下消息即可无缝继续：

```
请阅读 docs/PROJECT_CONTEXT_HANDOFF.md，继续完成P1文档修复任务。
待修复项目：
1. P1-2: AGENT_DESIGN.md KBAgent章节扩展
2. P1-3: PHASE_2_TASK_BREAKDOWN.md 添加POC任务
3. P1-4: STATE_MACHINE.md 合并重复定义

修复完成后更新本交接文档的状态。
```

### 3.2 修复顺序建议

1. **P1-3** (PHASE_2_TASK_BREAKDOWN.md) - 最简单，独立添加新章节
2. **P1-2** (AGENT_DESIGN.md) - 中等难度，扩展现有章节
3. **P1-4** (STATE_MACHINE.md) - 需要仔细对比两处定义，确保不丢失信息

### 3.3 验收标准

参考 `WORK_PLAN_V2.md` 第12.8节的P1级验收标准：
- [ ] AGENT_DESIGN.md KBAgent章节扩展至与其他Agent同等详细程度
- [ ] PHASE_2_TASK_BREAKDOWN.md 包含POC验证任务
- [ ] STATE_MACHINE.md 无重复定义

---

## 4. 关键文件索引

| 文件 | 路径 | 用途 |
|------|------|------|
| 工作计划 | `docs/WORK_PLAN_V2.md` | 第12章包含完整的文档改进计划 |
| Agent设计 | `docs/AGENT_DESIGN.md` | P1-2修复目标 |
| 任务分解 | `docs/PHASE_2_TASK_BREAKDOWN.md` | P1-3修复目标 |
| 状态机设计 | `docs/STATE_MACHINE.md` | P1-4修复目标 |
| 详细设计 | `docs/DETAILED_DESIGN_V2.md` | 参考：核心引擎设计规格 |
| 需求规范 | `docs/REQUIREMENTS.md` | 参考：完整需求列表 |
| API规范 | `docs/API_SPEC.md` | 参考：OpenAPI 3.0规范 |

---

## 5. 技术架构快速参考

### 5.1 核心技术栈

- **状态机与编排**: LangGraph
- **Agent运行时**: LangChain
- **向量数据库**: Qdrant
- **关系数据库**: PostgreSQL
- **代码解析**: Tree-sitter (C/C++)

### 5.2 四大核心Agent

1. **CodeAgent** - 代码分析与修改
2. **TestAgent** - 测试执行与控制
3. **AnalysisAgent** - 结果分析与决策
4. **KBAgent** - 知识库管理

### 5.3 四大核心引擎

1. **CodeAnalyzer** - Tree-sitter AST解析、静态分析
2. **CodeModifier** - 补丁生成、安全检查、回滚
3. **TestOrchestrator** - QEMU/Board适配器、测试执行
4. **ResultAnalyzer** - 日志解析、根因分析、决策生成

---

**文档版本**: v1.0
**最后更新**: 2026-01-30
**状态**: P1修复已完成
