"""
Test Orchestration Data Models

Defines all data classes for test execution and environment management.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class EnvironmentType(Enum):
    """环境类型"""
    QEMU = "qemu"
    BOARD = "board"
    BMC = "bmc"
    WINDOWS = "windows"
    LINUX = "linux"


class EnvironmentStatus(Enum):
    """环境状态"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


class ArtifactType(Enum):
    """产物类型"""
    LOG = "log"
    DUMP = "dump"
    SCREENSHOT = "screenshot"
    REPORT = "report"
    CORE = "core"
    COVERAGE = "coverage"


@dataclass
class OrchestratorConfig:
    """编排器配置"""
    workspace_dir: str = ""
    artifact_dir: str = ""
    max_concurrent_tests: int = 2
    default_timeout: int = 300
    retry_count: int = 3
    cleanup_on_finish: bool = True


@dataclass
class QEMUConfig:
    """QEMU环境配置"""
    binary_path: str = ""
    machine: str = "virt"
    cpu: str = "cortex-a57"
    memory: str = "2G"
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None
    disk_path: Optional[str] = None
    network_enabled: bool = True
    serial_enabled: bool = True
    monitor_enabled: bool = True


@dataclass
class BoardConfig:
    """目标板环境配置"""
    ip_address: str = ""
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_file: Optional[str] = None
    connection_timeout: int = 30


@dataclass
class BMCConfig:
    """BMC环境配置"""
    ip_address: str = ""
    port: int = 623
    username: str = ""
    password: str = ""
    interface: str = "lanplus"


@dataclass
class TestCase:
    """测试用例"""
    test_id: str = ""
    name: str = ""
    description: str = ""
    command: str = ""
    expected_output: Optional[str] = None
    timeout: int = 60
    retries: int = 1
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    environment_type: EnvironmentType = field(default_factory=lambda: EnvironmentType.QEMU)
    environment_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.test_id:
            self.test_id = f"test_{uuid.uuid4().hex[:8]}"


@dataclass
class TestPlan:
    """测试计划"""
    plan_id: str = ""
    name: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    environment_type: EnvironmentType = EnvironmentType.QEMU
    environment_config: Dict[str, Any] = field(default_factory=dict)
    parallel: bool = False
    stop_on_failure: bool = False
    description: str = ""

    def __post_init__(self):
        if not self.plan_id:
            self.plan_id = f"plan_{uuid.uuid4().hex[:8]}"


@dataclass
class TestResult:
    """单个测试结果"""
    test_id: str = ""
    test_name: str = ""
    status: TestStatus = TestStatus.PENDING
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    output: str = ""
    error_message: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    retry_count: int = 0

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASSED


@dataclass
class TestResults:
    """测试结果集合"""
    plan_id: str = ""
    plan_name: str = ""
    results: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    summary: str = ""

    def __post_init__(self):
        self.total_tests = len(self.results)
        self.passed = sum(1 for r in self.results if r.passed)
        self.failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        self.skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

    def generate_summary(self) -> str:
        """生成结果摘要"""
        rate = (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0
        return (
            f"Test Plan: {self.plan_name}\n"
            f"Total: {self.total_tests} | Passed: {self.passed} | "
            f"Failed: {self.failed} | Skipped: {self.skipped}\n"
            f"Pass Rate: {rate:.1f}%\n"
            f"Duration: {self.duration:.2f}s"
        )


@dataclass
class Artifact:
    """测试产物"""
    artifact_id: str = ""
    name: str = ""
    type: ArtifactType = ArtifactType.LOG
    path: str = ""
    size: int = 0
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.artifact_id:
            self.artifact_id = f"artifact_{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Environment:
    """测试环境实例"""
    env_id: str = ""
    env_type: EnvironmentType = EnvironmentType.QEMU
    status: EnvironmentStatus = EnvironmentStatus.IDLE
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    last_used: str = ""
    resource_usage: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.env_id:
            self.env_id = f"env_{uuid.uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def is_available(self) -> bool:
        """检查环境是否可用"""
        return self.status in [EnvironmentStatus.IDLE, EnvironmentStatus.RUNNING]

    def is_running(self) -> bool:
        """检查环境是否正在运行"""
        return self.status == EnvironmentStatus.RUNNING
