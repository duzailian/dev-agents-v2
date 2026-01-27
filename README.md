# AI-Driven Firmware Intelligent Testing System (dev-agents-v2)

An advanced multi-agent system designed for automated firmware testing, bug analysis, and code modification.

## Key Features
-   **Multi-Agent Orchestration**: Specialized agents for code analysis, testing, and knowledge retrieval.
-   **Firmware Specialized KB**: Product-line aware RAG for debugging experience.
-   **Execution Abstraction**: Support for QEMU, BMC, and physical target boards.
-   **CI/CD & Issue Tracking**: Deep integration with GitLab and Redmine.

## Documentation
-   [Architecture Design](docs/ARCHITECTURE.md)
-   [Detailed Design](docs/DETAILED_DESIGN.md)
-   [Work Plan](docs/WORK_PLAN.md)
-   [Directory Structure](docs/DIR_STRUCTURE.md)

## Quick Start
1.  Install dependencies: `pip install -r requirements.txt`
2.  Configure the system: `cp config/example.yaml config/config.yaml`
3.  Run the API: `uvicorn src.api.main:app --reload`

## License
Apache-2.0
