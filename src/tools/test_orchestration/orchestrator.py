"""
Test Orchestrator

Main orchestrator for test execution and environment management.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    TestCase,
    TestPlan,
    TestResult,
    TestResults,
    TestStatus,
    Environment,
    EnvironmentType,
    EnvironmentStatus,
    Artifact,
    ArtifactType,
    OrchestratorConfig,
)
from .environment_manager import EnvironmentManager

logger = logging.getLogger(__name__)


class TestRunner:
    """测试运行器"""

    def __init__(self, env_manager: EnvironmentManager):
        self._env_manager = env_manager

    async def run_test(
        self,
        test: TestCase,
        env: Environment,
        timeout: Optional[int] = None
    ) -> TestResult:
        """运行单个测试用例"""
        start_time = datetime.now()
        test_timeout = timeout or test.timeout

        adapter = await self._env_manager.get_adapter(env.env_id)
        if not adapter:
            return TestResult(
                test_id=test.test_id,
                test_name=test.name,
                status=TestStatus.ERROR,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                duration=0.0,
                output="",
                error_message="Environment adapter not found"
            )

        try:
            # Execute test command
            code, stdout, stderr = await adapter.execute(test.command, test_timeout)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Determine status based on return code and expected output
            if code == 0:
                # Check expected output if specified
                if test.expected_output and test.expected_output not in stdout:
                    status = TestStatus.FAILED
                    error_msg = f"Expected output not found: {test.expected_output}"
                else:
                    status = TestStatus.PASSED
                    error_msg = None
            else:
                status = TestStatus.FAILED
                error_msg = stderr or f"Command failed with code {code}"

            return TestResult(
                test_id=test.test_id,
                test_name=test.name,
                status=status,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                output=stdout,
                error_message=error_msg
            )

        except asyncio.TimeoutError:
            end_time = datetime.now()
            return TestResult(
                test_id=test.test_id,
                test_name=test.name,
                status=TestStatus.TIMEOUT,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=test_timeout,
                output="",
                error_message=f"Test timed out after {test_timeout}s"
            )
        except Exception as e:
            end_time = datetime.now()
            return TestResult(
                test_id=test.test_id,
                test_name=test.name,
                status=TestStatus.ERROR,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=0.0,
                output="",
                error_message=str(e)
            )


class ArtifactCollector:
    """测试产物收集器"""

    def __init__(self, artifact_dir: str):
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    async def collect(
        self,
        task_id: str,
        env_id: str,
        test_result: Optional[TestResult] = None
    ) -> List[Artifact]:
        """收集测试产物

        Args:
            task_id: 任务ID
            env_id: 环境ID
            test_result: 测试结果（可选）
        """
        artifacts = []

        # Create task-specific directory
        task_dir = self.artifact_dir / task_id / env_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Collect serial output if available
        adapter_artifacts = await self._collect_adapter_artifacts(env_id, task_dir)
        artifacts.extend(adapter_artifacts)

        # Create result artifact only if test_result is provided
        if test_result:
            result_artifact = Artifact(
                artifact_id="",
                name=f"result_{test_result.test_id}",
                type=ArtifactType.REPORT,
                path=str(task_dir / "result.json"),
                metadata={"test_id": test_result.test_id, "status": test_result.status.value}
            )
            artifacts.append(result_artifact)

        return artifacts

    async def _collect_adapter_artifacts(
        self,
        env_id: str,
        task_dir: Path
    ) -> List[Artifact]:
        """从适配器收集产物
        
        ⚠️ TODO: 实现完整的产物收集逻辑:
        1. 从QEMU串口日志收集输出
        2. 从Board收集测试日志和崩溃转储
        3. 收集性能分析数据
        4. 上传到统一的artifact存储
        """
        artifacts = []
        # Simplified: return empty list for now
        return artifacts


class TestOrchestrator:
    """
    Test Orchestrator - Main class for test execution orchestration

    Responsibilities:
    - Manage multiple test environments (QEMU, Board, BMC)
    - Environment lifecycle management (start, monitor, stop)
    - Test case scheduling and execution
    - Test result and artifact collection
    - Resource pool management and concurrency control
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the orchestrator

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self._env_manager = EnvironmentManager(config.workspace_dir)
        self._test_runner = TestRunner(self._env_manager)
        self._artifact_collector = ArtifactCollector(config.artifact_dir)
        self._active_tasks: Dict[str, Dict] = {}
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tests)

        # Ensure directories exist
        Path(config.workspace_dir).mkdir(parents=True, exist_ok=True)
        Path(config.artifact_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"TestOrchestrator initialized with {config.max_concurrent_tests} max concurrent tests")

    async def setup_environment(
        self,
        name: str,
        env_type: EnvironmentType,
        config: Dict[str, Any]
    ) -> Environment:
        """设置测试环境"""
        return await self._env_manager.create_environment(name, env_type, config)

    async def run_test_plan(self, plan: TestPlan) -> TestResults:
        """
        运行测试计划

        Args:
            plan: 测试计划

        Returns:
            TestResults: 测试结果
        """
        start_time = time.time()
        results: List[TestResult] = []

        # Create environment for this plan
        env = await self.setup_environment(
            plan.name,
            plan.environment_type,
            plan.environment_config
        )

        try:
            # Start the environment
            await self._env_manager.start_environment(env.env_id)

            if plan.parallel:
                # Run tests in parallel
                results = await self._run_parallel(plan.test_cases, env)
            else:
                # Run tests sequentially
                results = await self._run_sequential(plan.test_cases, env, plan.stop_on_failure)

        finally:
            # Cleanup environment
            await self._env_manager.destroy_environment(env.env_id)

        end_time = time.time()
        duration = end_time - start_time

        test_results = TestResults(
            plan_id=plan.plan_id,
            plan_name=plan.name,
            results=results,
            duration=duration
        )
        test_results.summary = test_results.generate_summary()

        logger.info(f"Test plan {plan.name} completed: {test_results.passed}/{test_results.total_tests} passed")
        return test_results

    async def run_single_test(
        self,
        test: TestCase,
        env: Environment
    ) -> TestResult:
        """运行单个测试用例"""
        async with self._semaphore:
            result = await self._test_runner.run_test(test, env)

            # Collect artifacts
            artifacts = await self._artifact_collector.collect(
                task_id=result.test_id,
                env_id=env.env_id,
                test_result=result
            )
            result.artifacts = [a.path for a in artifacts]

            return result

    async def collect_artifacts(self, task_id: str) -> List[Artifact]:
        """收集测试产物"""
        envs = self._env_manager.list_environments()
        all_artifacts = []

        for env in envs:
            artifacts = await self._artifact_collector.collect(task_id, env.env_id)
            all_artifacts.extend(artifacts)

        return all_artifacts

    async def teardown_environment(self, env: Environment) -> bool:
        """销毁环境"""
        return await self._env_manager.destroy_environment(env.env_id)

    def get_environment_status(self, env_id: str) -> Optional[Environment]:
        """获取环境状态"""
        return self._env_manager.get_environment(env_id)

    async def cleanup_all(self):
        """清理所有资源"""
        await self._env_manager.cleanup_all()

    async def _run_sequential(
        self,
        tests: List[TestCase],
        env: Environment,
        stop_on_failure: bool
    ) -> List[TestResult]:
        """顺序运行测试"""
        results = []

        for test in tests:
            result = await self.run_single_test(test, env)
            results.append(result)

            if stop_on_failure and not result.passed:
                logger.info(f"Stopping on failure: {test.name}")
                break

        return results

    async def _run_parallel(
        self,
        tests: List[TestCase],
        env: Environment
    ) -> List[TestResult]:
        """并行运行测试"""
        tasks = [self.run_single_test(test, env) for test in tests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(TestResult(
                    test_id=tests[i].test_id,
                    test_name=tests[i].name,
                    status=TestStatus.ERROR,
                    start_time="",
                    end_time="",
                    duration=0.0,
                    output="",
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results
