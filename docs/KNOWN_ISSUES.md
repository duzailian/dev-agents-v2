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
