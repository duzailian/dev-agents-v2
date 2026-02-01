# Known Issues and Risks

This document records known issues, architectural risks, and technical debt identified during the V2.0 design audit (February 2026). It serves as a reference for future development and mitigation planning.

## 1. High Priority Risks

### 1.1 State Machine Complexity & Error Recovery
*   **Description:** The LangGraph state machine (`STATE_MACHINE.md`) defines sophisticated error recovery loops (e.g., `MAX_RETRIES`, convergence logic). Implementing all edge cases (network timeouts, QEMU hangs, compilation failures) in the initial pass is high-risk.
*   **Impact:** Potential for infinite loops or "zombie" states where the agent gets stuck.
*   **Mitigation Strategy:**
    *   Start with a "Happy Path" implementation (v0.1).
    *   Add error edges incrementally.
    *   Implement a global "Watchdog" timer in the Orchestrator to kill stuck sessions.

### 1.2 Hardware/Software Abstraction Leaks
*   **Description:** The `TestOrchestrator` attempts to abstract `QEMU` and `Target Board` behind a unified interface. However, physical hardware has unique failure modes (serial port noise, power cycling delays) that QEMU does not.
*   **Impact:** Tests passing in QEMU might fail on hardware due to timing/environment, causing "flaky" agent behavior.
*   **Mitigation Strategy:**
    *   Enforce a "Simulation First" policy: Code must pass QEMU before touching hardware.
    *   Implement hardware-specific "Health Checks" in the `TestAgent` before running tests.

## 2. Design Inconsistencies

### 2.1 API Authentication Unification
*   **Location:** `docs/API_SPEC.md`
*   **Issue:** The specification mentions both "API Key" and "JWT" strategies in different contexts.
*   **Recommendation:**
    *   Standardize on **JWT (OAuth2)** for user/frontend interaction.
    *   Use **API Keys** strictly for machine-to-machine (CI/CD) integration.
    *   Update `API_SPEC.md` to explicitly define which endpoints use which scheme.

### 2.2 State Definition Inconsistencies 🔴 CRITICAL
*   **Location:** `docs/AGENT_DESIGN.md`, `src/agents/base_agent.py`, `docs/STATE_MACHINE.md`
*   **Issue:** State field naming is inconsistent across design documents and code implementation.
*   **Status:** ✅ FIXED (2026-02-01)

| Location | Field Name | Previous Status | Current Status |
|----------|------------|-----------------|----------------|
| `AGENT_DESIGN.md:78` | `patch_file` | ❌ Outdated | ✅ Fixed to `patch_content` |
| `STATE_MACHINE.md:69` | `patch_plan` | ⚠️ Design only | ✅ Documented as `patch_content` |
| `src/agents/base_agent.py:28` | `patch_content` | ✅ Current (code) | ✅ Still current |

*   **Fix Applied:**
    *   Updated `AGENT_DESIGN.md:78` and `AGENT_DESIGN.md:160` to use `patch_content`
    *   Added mapping table in `STATE_MACHINE.md` section 3.3

### 2.3 State Machine State Naming Inconsistencies 🔴 CRITICAL
*   **Location:** `docs/STATE_MACHINE.md` vs `src/orchestrator/graph.py`
*   **Issue:** State names in design documents differ from implementation.
*   **Status:** ✅ FIXED (2026-02-01)

| Design (STATE_MACHINE.md) | Implementation (graph.py) | Previous Status | Current Status |
|---------------------------|---------------------------|-----------------|----------------|
| `IDLE`, `INIT` | `initialize` node | ⚠️ Naming style mismatch | ✅ Documented mapping |
| `CODE_ANALYSIS` | `code_analysis` action | ✅ Match (case style only) | ✅ Still matches |
| `PATCH_GENERATION` | `patch_generation` node | ❌ Missing | ✅ Exists |
| `PATCH_APPLY` | `patch_application` node | ❌ Missing | ✅ Exists |
| `CONVERGENCE_CHECK` | `convergence_check` node | ❌ Missing | ✅ Exists |

*   **Fix Applied:**
    *   Added naming convention notice and mapping table in `STATE_MACHINE.md` section 3.3
    *   Documented snake_case (implementation) vs UPPER_SNAKE_CASE (design) correspondence

### 2.4 Missing State Fields 🟠 HIGH
*   **Location:** `docs/STATE_MACHINE.md` vs `src/agents/base_agent.py`
*   **Issue:** STATE_MACHINE.md defines state fields that are missing in implementation.
*   **Status:** ✅ FIXED (2026-02-01)

| Design Field | Previous Code Status | Current Status |
|--------------|---------------------|----------------|
| `goal` | ❌ Missing | ✅ Added to AgentState |
| `repo_snapshot` | ❌ Missing | ✅ Added to AgentState |
| `patch_plan` | ❌ Missing | ✅ Available via `patch_content` |
| `last_build_result` | ❌ Missing | ⏳ Available via `test_results` |
| `last_test_result` | ❌ Missing | ⏳ Available via `test_results` |
| `error_state` | ❌ Missing | ✅ Added to AgentState (Optional) |
| `decision_trace` | ❌ Missing | ✅ Added to AgentState |
| `convergence` | ✅ `converged` field | ✅ Still present |

*   **Fix Applied:**
    *   Added `goal: str` to AgentState
    *   Added `repo_snapshot: Dict[str, Any]` to AgentState
    *   Added `error_state: Optional[Dict[str, Any]]` to AgentState
    *   Added `decision_trace: List[Dict[str, Any]]` to AgentState

### 2.5 Iteration Index Discrepancy 🟠 MEDIUM
*   **Location:** `docs/STATE_MACHINE.md:64` vs code
*   **Issue:** Design says "iteration_index from 1", but code uses "iteration from 0"

| Document | Definition | Code Implementation |
|----------|------------|---------------------|
| STATE_MACHINE.md | `iteration_index`：当前迭代序号（从 1 开始） | `iteration`: 0-based |
| base_agent.py | `iteration: int` (default 0) | 0-based |

*   **Impact:** Off-by-one errors in iteration tracking
*   **Recommendation:** Standardize on 0-based indexing (industry standard)

### 2.6 next_action Naming Chaos 🟠 MEDIUM
*   **Location:** All Agent implementations
*   **Issue:** No unified action naming convention across agents.
*   **Status:** ✅ FIXED (2026-02-01)

| Agent | Previous Actions | Current Status |
|-------|-----------------|----------------|
| CodeAgent | `analyze`, `modify`, `apply_patch`, `error` | ✅ Standardized via WorkflowAction |
| TestAgent | `execute`, `collect_artifacts`, `setup_env`, `error` | ✅ Standardized via WorkflowAction |
| AnalysisAgent | `analyze`, `parse_logs`, `decide`, `error` | ✅ Standardized via WorkflowAction |
| KBAgent | `retrieve`, `capture`, `search`, `error` | ✅ Standardized via WorkflowAction |

*   **Fix Applied:**
    *   Created `WorkflowAction` Enum in `src/models/code.py`
    *   Updated `AgentState.next_action` to `Union[str, WorkflowAction]`
    *   Enum includes: ANALYZE, GENERATE_PATCH, CONTINUE, FINISH, FAILURE, ESCALATE, REVIEW_PATCH, APPLY_PATCH, RETRY, ROLLBACK, RUN_TEST, SETUP_ENV, RETRIEVE_KNOWLEDGE, CAPTURE_KNOWLEDGE

### 2.7 Missing State Enumeration 🟢 LOW
*   **Location:** `src/orchestrator/graph.py`
*   **Issue:** STATE_MACHINE.md defines states but code has no enum for validation.
*   **Status:** ✅ FIXED (2026-02-01)

*   **Fix Applied:**
    *   Created `WorkflowState` Enum in `src/models/code.py`
    *   Includes all LangGraph node names for compile-time validation
    *   Values: INITIALIZE, CODE_ANALYSIS, PATCH_GENERATION, PATCH_APPLICATION, BUILD_SETUP, BUILD_RUN, TEST_SETUP, TEST_EXECUTION, RESULT_COLLECTION, RESULT_ANALYSIS, CONVERGENCE_CHECK, KNOWLEDGE_RETRIEVAL, KNOWLEDGE_CAPTURE, ERROR_RECOVERY, SUCCESS, FAILURE, ESCALATE

## 3. Documentation & Process Issues

### 3.1 Documentation Drift
*   **Issue:** `DETAILED_DESIGN_V2.md` contains extremely granular class diagrams and pseudocode. As the code evolves, keeping this file 100% in sync will be a significant burden.
*   **Recommendation:**
    *   Treat `DETAILED_DESIGN_V2.md` as a "Design Contract".
    *   If code *must* deviate, update the doc first (Documentation Driven Development).
    *   Consider splitting this file into per-module design docs (`docs/design/module_xyz.md`) if it exceeds 2000 lines.

### 3.2 Missing Version Headers 🟢 LOW
*   **Location:** Multiple docs in `docs/` directory
*   **Issue:** Some documents lack version header (`> 文档版本：v2.0`)

| Document | Version Header |
|----------|----------------|
| `docs/ADR.md` | ✅ Present |
| `docs/KNOWN_ISSUES.md` | ✅ Present (English format) |
| `docs/poc_report.md` | ❌ Missing |
| `docs/SESSION_HANDOFF.md` | ❌ Missing |
| `docs/PROJECT_CONTEXT_HANDOFF.md` | ❌ Missing |

*   **Impact:** CI/CD document check workflow may fail
*   **Recommendation:** Add version headers to missing documents

### 3.3 Missing/Archived Files
*   **Status:** Several V1 documents (`API_DESIGN.md`, `WORK_PLAN.md`, `PHASE_1_*.md`) are referenced in old indices but missing from the directory.
*   **Action:** Confirm these were intentionally removed/superseded by V2 docs. Remove references to them from any surviving indices to avoid confusion.

## 3. Documentation & Process Issues

### 3.1 Documentation Drift
*   **Issue:** `DETAILED_DESIGN_V2.md` contains extremely granular class diagrams and pseudocode. As the code evolves, keeping this file 100% in sync will be a significant burden.
*   **Recommendation:**
    *   Treat `DETAILED_DESIGN_V2.md` as a "Design Contract".
    *   If code *must* deviate, update the doc first (Documentation Driven Development).
    *   Consider splitting this file into per-module design docs (`docs/design/module_xyz.md`) if it exceeds 2000 lines.

### 3.2 Missing/Archived Files
*   **Status:** Several V1 documents (`API_DESIGN.md`, `WORK_PLAN.md`, `PHASE_1_*.md`) are referenced in old indices but missing from the directory.
*   **Action:** Confirm these were intentionally removed/superseded by V2 docs. Remove references to them from any surviving indices to avoid confusion.

## 4. Implementation Tasks (from Audit)

### 4.1 Security Implementation ✅ FIXED (2026-02-01)
1.  **SecretFilter Integration:** ✅ Integrated before Agent layer
2.  **IPMI Password Handling:** ✅ Changed from `-P` flag to `IPMI_PASSWORD` environment variable
3.  **SSH Security:** ✅ Changed from `StrictHostKeyChecking=no` to `accept-new` + `UserKnownHostsFile=/dev/null`
4.  **SecretFilter Patterns:** ✅ Extended with 14 additional sensitive field patterns

### 4.2 QEMU/Environment Improvements ✅ FIXED (2026-02-01)
1.  **QEMU Timeout Control:** ✅ Added startup timeout and process health monitoring
2.  **Placeholder Documentation:** ✅ Added TODO comments for all simplified implementations

### 4.3 Integration & Testing ✅ FIXED (2026-02-01)
1.  **Traceability Matrix:** ✅ Created `tests/test_traceability_matrix.py`
2.  **Integration Tests:** ✅ Added FR-25, FR-09, FR-08 tests
3.  **LLM Patch Generation:** ✅ Implemented `_generate_patch_with_llm` in CodeAgent
4.  **Qdrant Integration:** ✅ Implemented `_semantic_search` in KBAgent
5.  **Graph Type Fixes:** ✅ Fixed `should_continue` and `run_workflow` type annotations

## 5. Placeholder Implementations (Technical Debt)

The following components have placeholder/simplified implementations that require full implementation:

| Component | File | Priority | Status | Description |
|-----------|------|----------|--------|-------------|
| `KBAgent._placeholder_search` | `src/agents/kb_agent.py` | P0 | ✅ Replaced | Qdrant + Embedding integration |
| `CodeAgent._generate_patch` | `src/agents/code_agent.py` | P0 | ✅ Replaced | LLM-based patch generation |
| `QEMUAdapter.execute` | `src/tools/test_orchestration/environment_manager.py` | P1 | ⏳ Pending | Serial/SSH command execution |
| `BoardAdapter.start` | `src/tools/test_orchestration/environment_manager.py` | P1 | ⏳ Pending | SSH connection establishment |
| `BMCAdapter.start` | `src/tools/test_orchestration/environment_manager.py` | P1 | ⏳ Pending | IPMI session management |
| `TestOrchestrator._collect_adapter_artifacts` | `src/tools/test_orchestration/orchestrator.py` | P2 | ⏳ Pending | Artifact collection from adapters |
| `CodeAnalyzer._calculate_metrics` | `src/tools/code_analysis/analyzer.py` | P2 | ⏳ Pending | Tree-sitter based complexity |

## 6. Test Coverage Matrix

### Traceability: REQUIREMENTS.md → pytest

| Requirement | Priority | Test Class | Coverage |
|-------------|----------|------------|----------|
| FR-02 | P0 | `TestNFR21_LLMOutputValidation` | ✅ LLM output validation |
| FR-09 | P0 | `TestFR09_IterationLoopControl` | ✅ Iteration control |
| FR-17 | P0 | `TestFR17_DecisionEngine` | ✅ Decision actions |
| FR-25 | P0 | `TestFR25_AutomatedClosedLoopSelfHealing` | ✅ Self-healing loop |
| NFR-01 | P0 | `TestNFR01_SecretsProtection` | ✅ Secret filtering |
| NFR-05 | P0 | `TestNFR05_TimeoutControls` | ✅ Timeout config |
| KR-04 | P0 | `TestKR04_SemanticSearch` | ✅ Vector search |
| KR-07 | P0 | `TestKR07_RAGIntegration` | ✅ RAG context |

## 7. Audit Log

*   **Date:** 2026-02-01
*   **Auditor:** Claude Code (System Architect Agent)
*   **Verdict:** Architecture V2 is sound. Focus shifts to **Implementation Discipline**.

### 2026-02-01 Updates - Complete Fix Round
- ✅ Security fixes: IPMI password exposure, SSH security, SecretFilter patterns
- ✅ QEMU timeout control added
- ✅ Placeholder implementations documented with TODO comments
- ✅ Traceability matrix established (28 P0 requirements mapped)
- ✅ Integration tests for FR-25 (self-healing), FR-09 (iterations)
- ✅ LLM patch generation implemented with API call structure
- ✅ Qdrant semantic search implemented with embedding service
- ✅ Type fixes in graph.py (`should_continue`, `run_workflow`)
- ✅ Updated KNOWN_ISSUES.md with full implementation tracking
- ✅ Fixed design inconsistencies (sections 2.2-2.7)
- ✅ Added WorkflowAction and WorkflowState enums to models
- ✅ Updated AgentState with missing fields (goal, repo_snapshot, error_state, decision_trace)
- ✅ Aligned STATE_MACHINE.md naming with graph.py implementation
