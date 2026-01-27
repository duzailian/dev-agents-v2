# AI-Driven Firmware Intelligent Testing System - Architecture Design

## 1. System Overview
The AI-driven Firmware Intelligent Testing System is designed to automate the lifecycle of firmware testing, bug localization, and fixing using multi-agent orchestration and specialized knowledge management.

### 1.1 Five-Layer Architecture
1.  **API Layer**: Provides external interfaces for CI/CD integration, Redmine issue management, and human-in-the-loop interactions.
2.  **Agent Orchestration Layer**: Orchestrates specialized agents (CodeAgent, TestAgent, etc.) to handle complex tasks using tool calling and reasoning.
3.  **Execution Engine Layer**: Manages the actual testing environments (QEMU, BMC, Target Boards) and handles code analysis and modification.
4.  **Knowledge Management Layer**: Maintains a vectorized database of debugging experience, logs, and documentation with product-line awareness.
5.  **Infrastructure Layer**: Basic services like logging, monitoring, and standard data persistence.

### 1.2 Core Modules
-   **CodeAnalyzer**: Performs AST parsing, dependency analysis, and context extraction.
-   **CodeModifier**: Generates code fix suggestions and applies patches.
-   **TestOrchestrator**: Manages test execution, environment setup, and result collection.
-   **ResultAnalyzer**: Analyzes logs, classifies errors, and extracts root causes.
-   **KnowledgeManager**: Handles knowledge ingestion, RAG retrieval, and vectorization.
-   **ProjectManager**: Integrates with Redmine and GitLab for task and issue tracking.

### 1.3 Data Flow
1.  **Requirement/Issue Input**: An issue is pulled from Redmine or a CI failure is detected in GitLab.
2.  **Analysis**: `CodeAgent` uses `CodeAnalyzer` to understand the relevant code path.
3.  **Knowledge Retrieval**: `KBAgent` queries the knowledge base for similar historical bugs and solutions.
4.  **Fix Generation**: `CodeAgent` generates a fix using `CodeModifier`.
5.  **Verification**: `TestAgent` instructs `TestOrchestrator` to run tests in the appropriate environment (e.g., QEMU).
6.  **Loop**: If tests fail, `AnalysisAgent` uses `ResultAnalyzer` to diagnose, and the process repeats.
7.  **Finalization**: On success, the fix is committed, Redmine is updated, and the experience is stored in the knowledge base.

## 2. Multi-Agent Orchestration
### 2.1 Agent Definitions
-   **CodeAgent**: Responsible for code understanding and editing.
-   **TestAgent**: Responsible for test plan generation and execution management.
-   **AnalysisAgent**: Specialized in log analysis and root cause identification.
-   **KBAgent**: Interface for knowledge base operations.
-   **PMAgent**: Manages external project state (Redmine/GitLab).

### 2.2 Coordination Mechanism
-   **Mechanism**: Hybrid Serial/Parallel execution with conditional branching based on task state.
-   **Function Calling**: Agents use standardized JSON-based tool definitions to interact with the execution engine and knowledge base.
-   **Loop Control**: Maximum iteration limit for the "Modify-Test-Analyze" cycle to prevent infinite loops.

## 3. Multi-Product Line Support
-   **Tagging System**: Dimension-based tags (SoC Type, Firmware Stack, HW Revision).
-   **Priority Retrieval**: Weighted retrieval algorithm prioritizing matches within the same product line.
-   **Abstraction**: Environment abstraction layer to handle differences between ARM TF, UEFI, RTOS, etc.

## 4. Knowledge Base Architecture
-   **Sources**: Debug logs, Redmine history, design docs, code comments.
-   **Vector DB**: Qdrant (Recommended for its performance and metadata filtering capabilities).
-   **RAG Strategy**: Hybrid search (Keyword + Vector) with re-ranking.

## 5. Test Execution Abstraction
-   **Unified Interface**: Standardized API for different testing frameworks (pytest, Robot).
-   **Environment Adapters**: Plugins for QEMU, BMC (via IPMI/Redfish), Physical Boards.
-   **Result Format**: Unified JSON report including logs, coverage, and pass/fail status.

## 6. Integration
-   **Redmine**: Bi-directional sync of issues and status.
-   **GitLab CI**: Triggered by merge requests or scheduled jobs; reports back to the pipeline.
