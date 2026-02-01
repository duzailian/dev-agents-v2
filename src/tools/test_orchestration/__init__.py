"""
Test Orchestration Module

Provides test execution orchestration for firmware testing:
- Environment management (QEMU, Board, BMC)
- Test execution and scheduling
- Artifact collection
- Resource pooling
"""

from .orchestrator import TestOrchestrator
from .environment_manager import EnvironmentManager
from .models import (
    TestCase,
    TestPlan,
    TestResult,
    TestResults,
    TestStatus,
    Artifact,
    Environment,
    EnvironmentType,
    EnvironmentStatus,
    OrchestratorConfig,
    QEMUConfig,
    BoardConfig,
    BMCConfig,
)

__all__ = [
    "TestOrchestrator",
    "EnvironmentManager",
    "EnvironmentType",
    "EnvironmentStatus",
    "TestCase",
    "TestPlan",
    "TestResult",
    "TestResults",
    "TestStatus",
    "Artifact",
    "Environment",
    "OrchestratorConfig",
    "QEMUConfig",
    "BoardConfig",
    "BMCConfig",
]
