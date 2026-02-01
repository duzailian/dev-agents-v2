"""
Analysis Agent

Wraps ResultAnalyzer engine.
Responsible for analyzing test results and making decisions in the state machine.
"""

import logging
from typing import Dict, Any, List, Optional

from src.agents.base_agent import BaseAgent, AgentState
from src.tools.result_analysis.analyzer import ResultAnalyzer
from src.tools.result_analysis.models import (
    ResultAnalyzerConfig,
    ActionType,
    FailureCategory,
)

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent
    
    Encapsulates ResultAnalyzer capabilities:
    - Failure Analysis: Parse test logs and extract error features
    - Root Cause Analysis: Combine code changes and error logs to infer root cause
    - Decision Making: Output next_action to control state machine flow
    """
    
    def _initialize_engine(self) -> None:
        """Initialize ResultAnalyzer engine"""
        # Initialize analyzer with config
        analyzer_config = ResultAnalyzerConfig(
            llm_model=self.config.get("llm_model", "gpt-4"),
            confidence_threshold=self.config.get("confidence_threshold", 0.8),
            max_history_depth=self.config.get("max_history_depth", 10),
            enable_ai_analysis=self.config.get("enable_ai", True),
            pattern_db_path=self.config.get("pattern_db_path")
        )
        
        self.analyzer = ResultAnalyzer(analyzer_config)
        logger.info("AnalysisAgent analyzer initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute AnalysisAgent logic based on current state and next_action
        
        Args:
            state: Current state
            
        Returns:
            State updates
        """
        next_action = state.get("next_action", "analyze")
        
        if next_action == "analyze":
            return await self._analyze_results(state)
        elif next_action == "parse_logs":
            return await self._parse_logs(state)
        elif next_action == "decide":
            return await self._make_decision(state)
        else:
            logger.warning(f"Unknown next_action: {next_action}")
            return {"next_action": "error"}
    
    async def _analyze_results(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyze test results and generate analysis report
        
        Args:
            state: Current state with test_results
            
        Returns:
            Analysis results
        """
        test_results = state.get("test_results", [])
        iteration = state.get("iteration", 0)
        task_id = state.get("task_id", "unknown")
        
        if not test_results:
            return {
                "analysis_report": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "summary": "No test results to analyze"
                },
                "next_action": "finish"
            }
        
        try:
            # Calculate statistics
            total_tests = len(test_results)
            passed = sum(1 for r in test_results if r.get("status") == "passed")
            failed = sum(1 for r in test_results if r.get("status") == "failed")
            skipped = sum(1 for r in test_results if r.get("status") == "skipped")
            
            # Extract test outputs for analysis
            test_outputs = {}
            for result in test_results:
                test_id = result.get("test_id", "")
                output = result.get("output", "") or result.get("error_message", "")
                test_outputs[test_id] = output
            
            # Run analysis
            report = self.analyzer.analyze_results(
                test_run_id=task_id,
                total_tests=total_tests,
                passed=passed,
                failed=failed,
                skipped=skipped,
                test_outputs=test_outputs,
                iteration=iteration
            )
            
            # Convert report to dict
            analysis_report = {
                "report_id": report.report_id,
                "timestamp": report.timestamp,
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
                "summary": report.summary,
                "decision": {
                    "action": report.decision.action.value if report.decision else None,
                    "confidence": report.decision.confidence if report.decision else 0.0,
                    "rationale": report.decision.rationale if report.decision else ""
                },
                "convergence": {
                    "converged": report.convergence.converged if report.convergence else False,
                    "trend": report.convergence.trend if report.convergence else "stable"
                } if report.convergence else None,
                "recommendations": report.recommendations,
                "failures": [
                    {
                        "test_id": f.failure_id,
                        "category": f.category.value,
                        "message": f.message[:200] if f.message else ""
                    }
                    for f in report.failures
                ]
            }
            
            # Determine next action
            next_action = self._determine_next_action(state, report)
            
            return {
                "analysis_report": analysis_report,
                "next_action": next_action,
                "messages": [f"Analysis complete: {report.summary}"]
            }
        except Exception as e:
            logger.error(f"Result analysis failed: {e}")
            return {
                "analysis_report": {},
                "errors": [f"Analysis failed: {str(e)}"],
                "next_action": "error"
            }
    
    async def _parse_logs(self, state: AgentState) -> Dict[str, Any]:
        """
        Parse log files and extract structured data
        
        Args:
            state: Current state with artifact paths
            
        Returns:
            Parsed log entries
        """
        artifacts = state.get("artifacts", [])
        log_paths = [a for a in artifacts if a.endswith(('.log', '.txt'))]
        
        if not log_paths:
            return {
                "analysis_report": {
                    "parsed_logs": [],
                    "summary": "No log files found"
                }
            }
        
        try:
            log_entries = self.analyzer.parse_logs(log_paths)
            
            return {
                "analysis_report": {
                    "parsed_logs": [
                        {
                            "timestamp": e.timestamp,
                            "level": e.level,
                            "source": e.source,
                            "message": e.message
                        }
                        for e in log_entries
                    ],
                    "summary": f"Parsed {len(log_entries)} log entries"
                },
                "messages": [f"Parsed {len(log_entries)} log entries from {len(log_paths)} files"]
            }
        except Exception as e:
            logger.error(f"Log parsing failed: {e}")
            return {
                "analysis_report": {"parsed_logs": []},
                "errors": [f"Log parsing failed: {str(e)}"]
            }
    
    async def _make_decision(self, state: AgentState) -> Dict[str, Any]:
        """
        Make decision based on current state and history
        
        Args:
            state: Current state with analysis_report and history
            
        Returns:
            Decision result
        """
        analysis_report = state.get("analysis_report", {})
        iteration = state.get("iteration", 0)
        
        # Use the decision from analysis if available
        decision = analysis_report.get("decision", {})
        action = decision.get("action", "continue")
        rationale = decision.get("rationale", "")
        
        # Override based on iteration count
        max_iterations = state.get("max_iterations", 10)
        
        if iteration >= max_iterations:
            action = "escalate"
            rationale = f"Reached maximum iterations ({max_iterations})"
        elif analysis_report.get("convergence", {}).get("converged"):
            action = "finish"
            rationale = "Convergence criteria met"
        
        return {
            "next_action": action,
            "messages": [f"Decision: {action}"],
            "analysis_report": {
                **analysis_report,
                "decision": {
                    **decision,
                    "action": action,
                    "rationale": rationale
                }
            }
        }
    
    def _determine_next_action(self, state: AgentState, report) -> str:
        """
        Determine the next action based on analysis results
        
        Args:
            state: Current state
            report: AnalysisReport
            
        Returns:
            Next action string
        """
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 10)
        pass_rate = report.pass_rate
        
        # Check convergence
        if report.convergence and report.convergence.converged:
            return "finish"
        
        # Check iteration limit
        if iteration >= max_iterations:
            return "escalate"
        
        # Check pass rate
        if pass_rate >= 0.8:
            return "finish"
        elif pass_rate >= 0.3:
            # Has some progress, try to continue fixing
            return "modify"
        else:
            # Too many failures, may need different approach
            if iteration < 2:
                return "modify"
            else:
                return "escalate"
    
    def _get_decision_rationale(self, action: str, iteration: int, pass_rate: float, max_iterations: int) -> str:
        """Get rationale string for decision"""
        if action == "finish":
            return f"Pass rate {pass_rate*100:.1f}% meets success threshold"
        elif action == "escalate":
            return f"Reached iteration limit ({iteration}/{max_iterations}) or pass rate too low"
        else:
            return f"Continuing fix attempt ({iteration}/{max_iterations})"
