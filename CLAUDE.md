# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Driven Firmware Intelligent Testing System**
A multi-agent system that automates firmware testing through iterative C code modification, test execution (QEMU/Target), and result analysis.

- **Orchestration**: LangGraph (State Machine)
- **Languages**: Python (Agents/Orchestration), C (Target Firmware)
- **Status**: Phase 2 (Core Module Implementation)

## Commands

### Setup & Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install project in editable mode
pip install -e .
```

### Running the Application
```bash
# Run the API server (FastAPI)
uvicorn api.main:app --reload

# Or via the installed CLI entry point
firmware-agent
```

### Testing
```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_analyzer.py
```

## Architecture

The system follows a **7-Layer Architecture** managed by LangGraph:

1.  **Application**: CLI/WebUI (`src/api`)
2.  **Orchestration**: LangGraph State Machine (`src/orchestrator/graph.py`)
3.  **Agents**: Specialized LangChain agents (`src/agents`)
    *   `CodeAgent`: Modifies C code
    *   `TestAgent`: Runs tests
    *   `AnalysisAgent`: Analyzes results
    *   `KBAgent`: Manages knowledge base
4.  **Security**: Safety layer (`src/security`) including `SecretFilter`
5.  **Engines**: Core logic (`src/tools`)
    *   `code_analysis`: Tree-sitter parsers
    *   `code_modification`: Git-based patching
    *   `test_orchestration`: Environment management
6.  **Knowledge**: RAG/Vector DB
7.  **Infrastructure**: Docker/QEMU

## Code Structure

- `src/agents/`: Agent implementations (Analysis, Code, KB, Test)
- `src/orchestrator/`: LangGraph workflow definitions
- `src/security/`: Security filters and safety checks
- `src/tools/`: Core functional engines
- `src/models/`: Shared Pydantic data models (`code.py`)
- `docs/`: Project documentation (Refer to `PROJECT_COMMAND_CENTER.md` for status)

## Guidelines

- **Orchestration**: All workflow logic resides in `src/orchestrator`. Do not implement state management in individual agents.
- **Safety**: File modifications should go through `CodeModifier` which uses `git apply` for safety.
- **Async**: Core engines use `async/await` patterns.
- **Documentation**: Always check `docs/PROJECT_COMMAND_CENTER.md` for the latest task status before starting work.
