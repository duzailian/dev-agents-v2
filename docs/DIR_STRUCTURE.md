# Project Directory Structure

```text
dev-agents-v2/
├── docs/                        # Documentation
│   ├── PROJECT_COMMAND_CENTER.md
│   ├── PHASE_1_TASK_BREAKDOWN.md
│   ├── PHASE_2_TASK_BREAKDOWN.md
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE_V2.md
│   ├── KNOWLEDGE_SCHEMA.md
│   ├── AGENT_DESIGN.md
│   ├── STATE_MACHINE.md
│   ├── WORK_PLAN_V2.md
│   ├── DETAILED_DESIGN_V2.md
│   ├── API_SPEC.md
│   ├── DIR_STRUCTURE.md
│   ├── WORK_PLAN.md
│   ├── PROJECT_PROGRESS.md
│   └── CLEANUP_LOG.md
├── src/                         # Source code (planned; not yet in repo)
│   ├── api/                     # FastAPI controllers and routes
│   ├── agents/                  # CrewAI agents and orchestrator logic
│   ├── executor/                # Execution engines (QEMU, Board, BMC)
│   ├── knowledge/               # Qdrant integration and RAG logic
│   ├── models/                  # Pydantic models and DB schemas
│   ├── tools/                   # Tool functions for agents (CodeAnalyzer, etc.)
│   ├── config/                  # Configuration loading and validation
│   └── utils/                   # Shared utilities (logging, hashing)
├── tests/                       # Unit and integration tests (planned)
├── scripts/                     # Helper scripts (planned)
├── docker/                      # Dockerfiles and docker-compose (planned)
├── config/                      # YAML configuration files
├── requirements.txt             # Python dependencies
├── README.md                    # Project overview
├── setup.py                     # Package installation script
└── structure.txt                # Flat file description of structure
```
