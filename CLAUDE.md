# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Driven Firmware Intelligent Testing System (AI驱动固件智能测试系统) - A multi-agent AI system that automates firmware testing by modifying C code, executing tests (QEMU/target boards), analyzing results, and iterating based on feedback.

**Current Status**: Phase 1 (Architecture & Design) completed. Phase 2 (Core Module Implementation) in progress. Source code in `src/` is planned but not yet implemented.

## Tech Stack

- **Multi-Agent Coordination**: CrewAI
- **State Machine**: LangGraph
- **RAG Knowledge Base**: LangChain + Qdrant
- **API Framework**: FastAPI
- **Execution Engines**: CodeAnalyzer, CodeModifier, TestOrchestrator, ResultAnalyzer

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Run tests
pytest

# Run single test
pytest tests/path/to/test_file.py::test_function_name

# Run API server (once implemented)
uvicorn api.main:app --reload
```

## Architecture

The system follows a layered architecture with four main execution engines:

1. **CodeAnalyzer** - Analyzes firmware C code using tree-sitter
2. **CodeModifier** - Applies AI-suggested code modifications
3. **TestOrchestrator** - Manages test execution on QEMU or target boards (BMC, Raspberry Pi)
4. **ResultAnalyzer** - Analyzes test results and decides whether to continue iteration

Multi-agent workflow is coordinated by CrewAI with LangGraph managing state transitions.

## Key Documentation

Start with `docs/PROJECT_COMMAND_CENTER.md` for project status and next steps.

| Document | Purpose |
|----------|---------|
| `docs/PROJECT_COMMAND_CENTER.md` | Project status, progress tracking, session handoff |
| `docs/DETAILED_DESIGN_V2.md` | Comprehensive detailed design |
| `docs/ARCHITECTURE_V2.md` | System architecture |
| `docs/AGENT_DESIGN.md` | Agent specifications |
| `docs/STATE_MACHINE.md` | State machine design |
| `docs/KNOWLEDGE_SCHEMA.md` | RAG knowledge base schema |
| `docs/PHASE_2_TASK_BREAKDOWN.md` | Current phase task breakdown |

## Planned Source Structure

```
src/
├── api/          # FastAPI REST endpoints
├── agents/       # CrewAI agent definitions
├── executor/     # Test environment adapters (QEMU, target boards)
├── knowledge/    # RAG and Qdrant integration
├── models/       # Domain models
├── tools/        # Agent tool implementations
├── config/       # Configuration handlers
└── utils/        # Shared utilities
```

## Development Notes

- Documentation is primarily in Chinese
- Internal LLM API is prioritized over external APIs
- Supports multiple test environments: QEMU, BMC, Raspberry Pi, Windows scripts
- Knowledge base supports product-line differentiation via tagging
