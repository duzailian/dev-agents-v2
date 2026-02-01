"""
Test Agent

Wraps TestOrchestrator engine.
Responsible for test environment management and test execution in the state machine.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.agents.base_agent import BaseAgent, AgentState
from src.tools.test_orchestration.orchestrator import TestOrchestrator
from src.tools.test_orchestration.models import (
    TestCase,
    TestPlan,
    TestStatus,
    EnvironmentType,
    OrchestratorConfig,
)

logger = logging.getLogger(__name__)


class TestAgent(BaseAgent):
    """
    Test Agent
    
    Encapsulates TestOrchestrator capabilities:
    - Environment Setup: Prepare QEMU or physical board environment
    - Test Execution: Execute test plan
    - Log Collection: Collect all artifacts (serial logs, system logs)
    """
    
    def _initialize_engine(self) -> None:
        """Initialize TestOrchestrator engine"""
        # Initialize orchestrator with config
        workspace_dir = self.config.get("workspace_dir", "/tmp/workspace")
        artifact_dir = self.config.get("artifact_dir", "/tmp/artifacts")
        
        orchestrator_config = OrchestratorConfig(
            workspace_dir=workspace_dir,
            artifact_dir=artifact_dir,
            max_concurrent_tests=self.config.get("max_concurrent_tests", 2),
            default_timeout=self.config.get("default_timeout", 300),
            retry_count=self.config.get("retry_count", 3),
            cleanup_on_finish=self.config.get("cleanup_on_finish", True)
        )
        
        self.orchestrator = TestOrchestrator(orchestrator_config)
        logger.info("TestAgent orchestrator initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute TestAgent logic based on current state and next_action
        
        Args:
            state: Current state
            
        Returns:
            State updates
        """
        next_action = state.get("next_action", "execute")
        
        if next_action == "execute":
            return await self._execute_tests(state)
        elif next_action == "collect_artifacts":
            return await self._collect_artifacts(state)
        elif next_action == "setup_env":
            return await self._setup_environment(state)
        else:
            logger.warning(f"Unknown next_action: {next_action}")
            return {"next_action": "error"}
    
    async def _execute_tests(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the test plan
        
        Args:
            state: Current state with test_plan
            
        Returns:
            Test execution results
        """
        test_plan = state.get("test_plan", {})
        
        if not test_plan:
            return {
                "test_results": [],
                "errors": ["No test plan specified"],
                "next_action": "error"
            }
        
        try:
            # Create TestPlan object from dict
            plan = self._dict_to_test_plan(test_plan)
            
            logger.info(f"Executing test plan: {plan.name}")
            
            # Run the test plan
            results = await self.orchestrator.run_test_plan(plan)
            
            # Convert results to dict format for state
            test_results = self._test_results_to_dict(results)
            
            # Determine next action based on results
            pass_rate = results.passed / results.total_tests if results.total_tests > 0 else 0
            
            if pass_rate >= 0.8:
                next_action = "finish"
            elif pass_rate >= 0.3:
                next_action = "analyze"  # Go to analysis to understand failures
            else:
                next_action = "escalate"  # Too many failures, escalate
            
            return {
                "test_results": test_results,
                "next_action": next_action,
                "messages": [f"Tests completed: {results.passed}/{results.total_tests} passed ({pass_rate*100:.1f}%)"]
            }
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "test_results": [],
                "errors": [f"Test execution failed: {str(e)}"],
                "next_action": "error"
            }
    
    async def _collect_artifacts(self, state: AgentState) -> Dict[str, Any]:
        """
        Collect test artifacts
        
        Args:
            state: Current state with task_id
            
        Returns:
            Artifact paths
        """
        task_id = state.get("task_id", "")
        
        if not task_id:
            return {
                "artifacts": [],
                "errors": ["No task ID specified"]
            }
        
        try:
            artifacts = await self.orchestrator.collect_artifacts(task_id)
            artifact_paths = [a.path for a in artifacts]
            
            return {
                "artifacts": artifact_paths,
                "messages": [f"Collected {len(artifact_paths)} artifacts"]
            }
        except Exception as e:
            logger.error(f"Artifact collection failed: {e}")
            return {
                "artifacts": [],
                "errors": [f"Artifact collection failed: {str(e)}"]
            }
    
    async def _setup_environment(self, state: AgentState) -> Dict[str, Any]:
        """
        Setup test environment
        
        Args:
            state: Current state with environment configuration
            
        Returns:
            Environment setup result
        """
        env_config = state.get("environment_config", {})
        
        if not env_config:
            return {
                "errors": ["No environment configuration specified"]
            }
        
        try:
            env_type_str = env_config.get("type", "qemu")
            env_type = EnvironmentType(env_type_str)
            
            env = await self.orchestrator.setup_environment(
                name=env_config.get("name", "test_env"),
                env_type=env_type,
                config=env_config
            )
            
            return {
                "environment": {
                    "env_id": env.env_id,
                    "status": env.status.value,
                    "type": env.env_type.value
                },
                "messages": [f"Environment {env.name} created with ID {env.env_id}"]
            }
        except Exception as e:
            logger.error(f"Environment setup failed: {e}")
            return {
                "errors": [f"Environment setup failed: {str(e)}"]
            }
    
    def _dict_to_test_plan(self, plan_dict: Dict[str, Any]) -> TestPlan:
        """Convert dict to TestPlan object"""
        test_cases = []
        for tc in plan_dict.get("test_cases", []):
            test_cases.append(TestCase(
                test_id=tc.get("test_id", ""),
                name=tc.get("name", ""),
                description=tc.get("description", ""),
                command=tc.get("command", ""),
                expected_output=tc.get("expected_output"),
                timeout=tc.get("timeout", 60),
                retries=tc.get("retries", 1),
                tags=tc.get("tags", [])
            ))
        
        env_type_str = plan_dict.get("environment_type", "qemu")
        
        return TestPlan(
            plan_id=plan_dict.get("plan_id", ""),
            name=plan_dict.get("name", ""),
            test_cases=test_cases,
            environment_type=EnvironmentType(env_type_str),
            environment_config=plan_dict.get("environment_config", {}),
            parallel=plan_dict.get("parallel", False),
            stop_on_failure=plan_dict.get("stop_on_failure", False)
        )
    
    def _test_results_to_dict(self, results) -> List[Dict[str, Any]]:
        """Convert TestResults to list of dicts for state"""
        return [
            {
                "test_id": r.test_id,
                "test_name": r.test_name,
                "status": r.status.value,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "duration": r.duration,
                "output": r.output,
                "error_message": r.error_message,
                "artifacts": r.artifacts
            }
            for r in results.results
        ]
