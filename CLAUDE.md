# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Driven Firmware Intelligent Testing System** (AI驱动固件智能测试系统)

A multi-agent system that automates firmware testing through iterative C code modification, test execution (QEMU/Target), and result analysis. The core loop: AI suggests code changes → tests run → results analyzed → decisions made → repeat until convergence.

- **Current Status**: Phase 2 (Core Module Implementation)
- **Languages**: Python (orchestration), C (target firmware)
- **Documentation**: Chinese (design docs), English (code/comments)

## Critical: Start Here

**ALWAYS** read `docs/PROJECT_COMMAND_CENTER.md` first. It contains current project status, active tasks, and session handoff context.

## Commands

```bash
# Setup
pip install -r requirements.txt
pip install -e .

# Run all tests
pytest

# Run specific test file or test
pytest tests/test_analyzer.py
pytest tests/test_analyzer.py::test_function_name

# Run API server
uvicorn api.main:app --reload
```

## Architecture Overview

**7-Layer Architecture** (LangGraph as sole orchestration layer):

```
Layer 7: Application (CLI, REST API, WebUI)
Layer 6: Orchestration (LangGraph state machine, SecretFilter)
Layer 5: Agents (CodeAgent, TestAgent, AnalysisAgent, KBAgent)
Layer 4.5: Security (SAST scanning, sandbox isolation)
Layer 4: Engines (CodeAnalyzer, CodeModifier, TestOrchestrator, ResultAnalyzer)
Layer 3: Knowledge (RAG with Qdrant vectors + PostgreSQL metadata)
Layer 2: Infrastructure (QEMU, target boards, Docker)
Layer 1: Data (code repos, test artifacts, logs)
```

**Key Components**:

- `src/tools/code_analysis/`: Tree-sitter based C/C++ parser and analyzer. `CodeAnalyzer` orchestrates parsing, static analysis, and AI analysis into unified `CodeAnalysis` results.
- `src/tools/code_modification/`: Git-based patch application via `CodeModifier`. Uses `git apply` for safe patch operations with conflict detection.
- `src/models/code.py`: Core data models (`CodeAnalysis`, `CodeIssue`, `CodeMetrics`, `IssueType`, `IssueSeverity`).
- `src/agents/`: LangChain agent implementations for each specialized role.

**Execution Modes**: INTERACTIVE (human approval), CI (auto with safety limits), AUTO (fully autonomous).

## Key Documentation

| File | Purpose |
|------|---------|
| `docs/PROJECT_COMMAND_CENTER.md` | **Read first**. Status, tasks, handoff. |
| `docs/ARCHITECTURE_V2.md` | Full 7-layer architecture design |
| `docs/DETAILED_DESIGN_V2.md` | Implementation specs, API contracts |
| `docs/AGENT_DESIGN.md` | Agent roles, tools, rejection policies |
| `docs/STATE_MACHINE.md` | LangGraph state transitions, convergence logic |

## Development Rules

1. **LangGraph Only**: All workflow orchestration through LangGraph. No secondary orchestration frameworks.
2. **Security**: Code execution in Docker sandboxes. Use SecretFilter for all logs. SAST scanning before patch application.
3. **Async Pattern**: Engines use `async/await`. See `CodeAnalyzer.analyze_file()` for the pattern.
4. **Protocol Types**: Use Python `Protocol` for dependency injection (e.g., `StaticAnalyzer`, `AIAnalyzer` protocols in analyzer.py).
