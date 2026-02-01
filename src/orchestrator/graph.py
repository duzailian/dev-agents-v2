"""
LangGraph State Machine Integration

This module implements the LangGraph-based state machine for the firmware testing system.
Based on STATE_MACHINE.md design with 17 states and LangGraph API.
"""

import asyncio
import logging
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.base_agent import AgentState
from src.agents.code_agent import CodeAgent
from src.agents.test_agent import TestAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.kb_agent import KBAgent

logger = logging.getLogger(__name__)


class WorkflowState(AgentState):
    """
    LangGraph Workflow State

    Inherits from AgentState to ensure consistency.
    Additional workflow-specific fields can be added here if needed.
    """
    pass


def create_workflow_graph(
    code_agent: CodeAgent,
    test_agent: TestAgent,
    analysis_agent: AnalysisAgent,
    kb_agent: KBAgent,
    max_iterations: int = 10
) -> StateGraph:
    """
    Create the LangGraph state machine for firmware testing workflow.
    
    Args:
        code_agent: CodeAgent instance
        test_agent: TestAgent instance
        analysis_agent: AnalysisAgent instance
        kb_agent: KBAgent instance
        max_iterations: Maximum number of iterations
    
    Returns:
        Compiled StateGraph
    """
    # Create the state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_node)
    workflow.add_node("code_analysis", code_agent)
    workflow.add_node("patch_generation", code_agent)
    workflow.add_node("patch_application", code_agent)
    workflow.add_node("build_setup", test_agent)
    workflow.add_node("build_run", test_agent)
    workflow.add_node("test_setup", test_agent)
    workflow.add_node("test_execution", test_agent)
    workflow.add_node("result_collection", test_agent)
    workflow.add_node("result_analysis", analysis_agent)
    workflow.add_node("convergence_check", analysis_agent)
    workflow.add_node("knowledge_retrieval", kb_agent)
    workflow.add_node("knowledge_capture", kb_agent)
    workflow.add_node("error_recovery", analysis_agent)
    workflow.add_node("success", success_node)
    workflow.add_node("failure", failure_node)
    workflow.add_node("escalate", escalate_node)
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    # Define edges
    workflow.add_edge("initialize", "code_analysis")
    workflow.add_edge("code_analysis", "patch_generation")
    workflow.add_edge("patch_generation", "patch_application")
    workflow.add_edge("patch_application", "build_setup")
    workflow.add_edge("build_setup", "build_run")
    workflow.add_edge("build_run", "test_setup")
    workflow.add_edge("test_setup", "test_execution")
    workflow.add_edge("test_execution", "result_collection")
    workflow.add_edge("result_collection", "result_analysis")
    workflow.add_edge("result_analysis", "convergence_check")
    workflow.add_edge("knowledge_retrieval", "code_analysis")
    workflow.add_edge("knowledge_capture", "success")
    
    # Conditional edges from convergence_check
    workflow.add_conditional_edges(
        "convergence_check",
        should_continue,
        {
            "continue": "code_analysis",
            "finish": "knowledge_capture",
            "failure": "failure",
            "escalate": "escalate"
        }
    )
    
    # Conditional edges from error_recovery
    workflow.add_conditional_edges(
        "error_recovery",
        should_recover,
        {
            "retry": "initialize",
            "rollback": "initialize",
            "escalate": "escalate"
        }
    )
    
    # Success/Failure/Escalate are terminal states
    workflow.add_edge("success", END)
    workflow.add_edge("failure", END)
    workflow.add_edge("escalate", END)
    
    return workflow


def should_continue(state: WorkflowState, max_iterations: int = 10) -> str:
    """
    Determine the next action based on analysis results.
    
    Args:
        state: Current workflow state
        max_iterations: Maximum iterations allowed
    
    Returns:
        Next action: "continue", "finish", "failure", or "escalate"
    """
    iteration = state.get("iteration", 0)
    next_action = state.get("next_action", "continue")
    converged = state.get("converged", False)
    
    if converged or next_action == "finish":
        return "finish"
    
    if next_action == "escalate":
        return "escalate"
    
    if iteration >= max_iterations:
        return "escalate"
    
    return "continue"


def should_recover(state: WorkflowState) -> str:
    """
    Determine recovery action based on error state.
    
    Args:
        state: Current workflow state
    
    Returns:
        Recovery action: "retry", "rollback", or "escalate"
    """
    errors = state.get("errors", [])
    
    if not errors:
        return "retry"
    
    # Check error types
    error_types = [e.lower() for e in errors]
    
    if any("build" in e or "compile" in e for e in error_types):
        return "rollback"
    
    if any("timeout" in e for e in error_types):
        return "retry"
    
    # Default to escalate for unknown errors
    return "escalate"


async def initialize_node(state: WorkflowState) -> WorkflowState:
    """
    Initialize the workflow state.
    
    Args:
        state: Initial state
    
    Returns:
        Updated state with initialization complete
    """
    logger.info(f"Initializing workflow for task: {state.get('task_id', 'unknown')}")
    
    return {
        **state,
        "iteration": 0,
        "max_iterations": state.get("max_iterations", 10),
        "messages": state.get("messages", []) + ["Workflow initialized"],
        "next_action": "analyze"
    }


async def success_node(state: WorkflowState) -> WorkflowState:
    """
    Handle successful completion.
    
    Args:
        state: Final state
    
    Returns:
        Updated state with success status
    """
    logger.info(f"Workflow completed successfully: {state.get('task_id')}")
    
    return {
        **state,
        "messages": state.get("messages", []) + ["Workflow completed successfully"],
        "next_action": "finish"
    }


async def failure_node(state: WorkflowState) -> WorkflowState:
    """
    Handle workflow failure.
    
    Args:
        state: Final state with errors
    
    Returns:
        Updated state with failure status
    """
    logger.error(f"Workflow failed: {state.get('task_id')}")
    
    return {
        **state,
        "messages": state.get("messages", []) + ["Workflow failed"],
        "next_action": "failure"
    }


async def escalate_node(state: WorkflowState) -> WorkflowState:
    """
    Handle escalation request.
    
    Args:
        state: Current state requiring escalation
    
    Returns:
        Updated state with escalation status
    """
    logger.warning(f"Workflow escalated: {state.get('task_id')}")
    
    return {
        **state,
        "messages": state.get("messages", []) + ["Workflow escalated for human review"],
        "next_action": "escalate"
    }


async def run_workflow(
    initial_state: Dict[str, Any],
    code_agent: CodeAgent,
    test_agent: TestAgent,
    analysis_agent: AnalysisAgent,
    kb_agent: KBAgent,
    max_iterations: int = 10
) -> WorkflowState:
    """
    Run the workflow with the given initial state.
    
    Args:
        initial_state: Initial state dictionary
        code_agent: CodeAgent instance
        test_agent: TestAgent instance
        analysis_agent: AnalysisAgent instance
        kb_agent: KBAgent instance
        max_iterations: Maximum iterations
    
    Returns:
        Final workflow state
    """
    # Create the workflow graph
    workflow = create_workflow_graph(
        code_agent, test_agent, analysis_agent, kb_agent, max_iterations
    )
    
    # Create memory saver for checkpointing
    memory = MemorySaver()
    
    # Compile the workflow
    app = workflow.compile(checkpointer=memory)
    
    # Convert initial state to WorkflowState
    state: WorkflowState = {
        "task_id": initial_state.get("task_id", ""),
        "iteration": 0,
        "max_iterations": max_iterations,
        "repo_path": initial_state.get("repo_path", ""),
        "current_commit": initial_state.get("current_commit", ""),
        "target_files": initial_state.get("target_files", []),
        "patch_content": "",
        "patch_applied": False,
        "test_plan": initial_state.get("test_plan", {}),
        "test_results": [],
        "artifacts": [],
        "analysis_report": {},
        "next_action": "initialize",
        "converged": False,
        "messages": [],
        "errors": []
    }
    
    # Run the workflow
    final_state = await app.ainvoke(state)
    
    return WorkflowState(**final_state) if isinstance(final_state, dict) else final_state


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'D:/workspace/dev-agents-v2')
    
    async def main():
        # Create agents
        code_agent = CodeAgent({})
        test_agent = TestAgent({})
        analysis_agent = AnalysisAgent({})
        kb_agent = KBAgent({})
        
        # Initial state
        initial_state = {
            "task_id": "test_task_001",
            "repo_path": "/tmp/test_repo",
            "target_files": ["src/main.c"],
            "test_plan": {
                "name": "smoke_test",
                "test_cases": [{"name": "test_init", "command": "./test_init"}]
            }
        }
        
        # Run workflow
        result = await run_workflow(
            initial_state,
            code_agent,
            test_agent,
            analysis_agent,
            kb_agent
        )
        
        print("Workflow completed!")
        print(f"Messages: {result.get('messages', [])}")
        print(f"Errors: {result.get('errors', [])}")
    
    asyncio.run(main())
