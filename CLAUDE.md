# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Driven Firmware Intelligent Testing System** (AI驱动固件智能测试系统)
A multi-agent system that automates firmware testing by iterating through C code modification, test execution (QEMU/Target), and result analysis.

- **Current Status**: Phase 2 (Core Module Implementation) starting. Architecture/Design (Phase 1) is complete.
- **Primary Language**: Python (Orchestration/Agents), C (Target Firmware).
- **Documentation Language**: Chinese (Main), English (Code comments/Protocol).

## Critical Protocol: Project Command Center

**ALWAYS** start your session by reading `docs/PROJECT_COMMAND_CENTER.md`.
This file is the single source of truth for project status, active tasks, and context handoff.

## Tech Stack & Architecture

The system uses a **LangGraph-driven** architecture (Note: CrewAI orchestration was removed in V2).

- **Orchestration**: LangGraph (State Machine & Workflow Control)
- **Agent Runtime**: LangChain Agents
- **Knowledge Base**: LangChain + Qdrant (RAG)
- **Database**: PostgreSQL (Metadata), Qdrant (Vector)
- **Execution Engines**:
  - `CodeAnalyzer`: Tree-sitter based C analysis
  - `CodeModifier`: AI-driven code patching
  - `TestOrchestrator`: QEMU/BMC/Board runner
  - `ResultAnalyzer`: Test log analysis
- **Security**: SecretFilter, SAST (Semgrep), Docker Sandbox

## Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

### Development (Planned)
```bash
# Run tests (when implemented)
pytest

# Run a specific test
pytest tests/path/to/test_file.py::test_function_name

# Run the API server (FastAPI)
uvicorn api.main:app --reload
```

## Directory Structure

```text
.
├── config/              # Configuration files
├── docs/                # Documentation (See Key Documentation below)
├── src/ (Planned)
│   ├── api/             # FastAPI endpoints
│   ├── agents/          # Agent definitions (LangChain)
│   ├── graph/           # LangGraph state machine definitions
│   ├── executor/        # QEMU/Board adapters
│   ├── knowledge/       # RAG system
│   └── security/        # SecretFilter & Sandbox logic
└── tests/ (Planned)     # Unit and Integration tests
```

## Key Documentation

| File | Description |
|------|-------------|
| `docs/PROJECT_COMMAND_CENTER.md` | **Read First**. Status, tasks, and handoff. |
| `docs/ARCHITECTURE_V2.md` | System architecture (Layers 1-7). |
| `docs/DETAILED_DESIGN_V2.md` | Implementation details. |
| `docs/PHASE_2_TASK_BREAKDOWN.md` | Tasks for the current implementation phase. |

## Development Guidelines

1.  **Architecture Alignment**: Follow `ARCHITECTURE_V2.md` strictly. Use LangGraph for flow control, not CrewAI.
2.  **Security First**: All code execution must happen in sandboxes. No secrets in logs.
3.  **Documentation**: Update documentation in `docs/` when design changes.
4.  **Testing**: Write tests for all new modules.
