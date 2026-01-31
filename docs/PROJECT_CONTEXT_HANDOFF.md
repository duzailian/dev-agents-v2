# Project Context Handoff - Session Restart
> **Date**: 2026-01-31
> **Reason**: Restarting session to load new plugins.
> **Status**: Phase 2, Task 2-1 (Core Analysis Engine) **COMPLETED**.
> **Next**: Task 2-2 (Security Implementation).

## 1. Current Progress Snapshot

We have just completed **Task 2-1: Core Analysis Engine Implementation**. The codebase is in a stable, committed state.

### Completed Components
1.  **Data Models (`src/models/code.py`)**:
    *   Full implementation of `Issue`, `Location`, `FunctionNode`, `Symbol`, `CallGraph`, `AnalysisReport`.
    *   Aligned 1:1 with `docs/DETAILED_DESIGN_V2.md`.
    *   Added `AnalysisType.AI` for future use.

2.  **Parser (`src/tools/code_analysis/parser.py`)**:
    *   **Status**: REFACTORED.
    *   **History**: Legacy `parser.py` deleted. Old `parsers.py` renamed to `parser.py`.
    *   **Tech Stack**: `tree-sitter==0.21.3` (CRITICAL: Do not upgrade without major refactoring).
    *   **Features**: C/C++ support, AST extraction, function/call/symbol extraction.

3.  **Core Engine (`src/tools/code_analysis/analyzer.py`)**:
    *   **Features**:
        *   Dynamic parser switching (C vs C++).
        *   Symbol Table & Call Graph construction.
        *   Dependency Graph generation.
        *   Static Analysis integration (Async execution).
    *   **Robustness**: Added error handling for single-file failures.

4.  **Static Analysis (`src/tools/code_analysis/static_analyzers.py`)**:
    *   **Protocol**: `StaticAnalyzer` defined.
    *   **Implementations**: `ClangTidyAnalyzer` (Text output), `CppcheckAnalyzer` (XML v2 output).
    *   **State**: Logic implemented and unit-tested with Mocks. Actual binaries (`clang-tidy`, `cppcheck`) are **missing** in the current environment.

### Git Status
*   **Branch**: `main`
*   **Last Commit**: `feat(analysis): integrate static analysis tools (clang-tidy, cppcheck)`
*   **Working Tree**: Clean (ignoring empty scaffolding directories).

## 2. Critical Technical Context (READ THIS)

### ⚠️ Dependency Lock: Tree-Sitter
*   **Version**: We are strictly pinned to **`tree-sitter==0.21.3`**.
*   **Reason**: Newer versions (0.22+) changed the `Query.captures()` API and `Language()` constructor significantly. The current implementation in `parser.py` relies on the 0.21.x behavior.
*   **Bindings**: `tree-sitter-c==0.21.4`, `tree-sitter-cpp==0.21.0`.

### ⚠️ Environment Limitations
*   **Platform**: Windows.
*   **Python**: Use `./venv/Scripts/python` and `./venv/Scripts/pytest`.
*   **Missing Tools**: `clang-tidy` and `cppcheck` are NOT installed in the path. Integration tests for these must remain mocked until we move to a target environment (e.g., Docker/Linux).

## 3. Immediate Next Steps (Task 2-2)

**Goal**: Implement Security Layer (`SecretFilter` & `SecurityScanner`).

1.  **SecretFilter Implementation**:
    *   **File**: `src/security/secret_filter.py`
    *   **Design**: Regex-based pattern matching (API keys, passwords, IPs).
    *   **Role**: Sanitize logs and AI prompts *before* they leave the system.

2.  **SecurityScanner Implementation**:
    *   **File**: `src/security/scanner.py`
    *   **Design**: SAST wrapper (BANDIT for Python, potentially others).
    *   **Role**: Check generated code for vulnerabilities before execution.

3.  **Sandbox Interface**:
    *   **File**: `src/infrastructure/sandbox/docker_manager.py` (or similar).
    *   **Role**: Define the interface for isolating execution (Phase 2 requirement).

## 4. Verification Commands

To verify the current state after restart:

```bash
# 1. Verify Parser & Analyzer Logic
./venv/Scripts/pytest tests/test_parser.py tests/test_analyzer.py tests/test_code_analyzer.py

# 2. Verify Static Analysis Logic (Mocks)
./venv/Scripts/pytest tests/test_static_analyzers.py

# 3. Check installed versions
./venv/Scripts/pip list | grep tree-sitter
```
