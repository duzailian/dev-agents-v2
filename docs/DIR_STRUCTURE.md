# Project Directory Structure

```text
dev-agents-v2/
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # System architecture design
│   ├── DETAILED_DESIGN.md       # Detailed module and API design
│   ├── WORK_PLAN.md             # Phased development roadmap
│   ├── PROJECT_PROGRESS.md      # Task tracking and status
│   └── API_SPEC.md              # OpenAPI/AsyncAPI specifications
├── src/                         # Source Code
│   ├── api/                     # FastAPI controllers and routes
│   ├── agents/                  # AutoGen agents and orchestrator logic
│   ├── executor/                # Execution engines (QEMU, Board, BMC)
│   ├── knowledge/               # Qdrant integration and RAG logic
│   ├── models/                  # Pydantic models and DB schemas
│   ├── tools/                   # Tool functions for agents (CodeAnalayzer, etc.)
│   ├── config/                  # Configuration loading and validation
│   └── utils/                   # Shared utilities (logging, hashing)
├── tests/                       # Unit and integration tests
├── scripts/                     # Helper scripts (setup, ingestion)
├── docker/                      # Dockerfiles and docker-compose
├── config/                      # YAML configuration files
├── requirements.txt             # Python dependencies
├── README.md                    # Project overview
├── setup.py                     # Package installation script
└── structure.txt                # Flat file description of structure
```
