"""
Base Agent

Abstract base class for all agents in the system.
Agents are nodes in the LangGraph state machine, receiving state and returning updated state.
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """全局共享状态定义 - LangGraph状态机的核心数据结构"""
    
    # 任务标识
    task_id: str
    iteration: int
    max_iterations: int
    
    # 代码上下文
    repo_path: str
    current_commit: str
    target_files: List[str]
    patch_content: str
    patch_applied: bool
    
    # 测试上下文
    test_plan: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    artifacts: List[str]
    
    # 分析结果
    analysis_report: Dict[str, Any]
    next_action: str
    converged: bool
    
    # 错误与消息
    messages: List[str]
    errors: List[str]


@dataclass
class AgentConfig:
    """Agent配置基类"""
    model_name: str = "gpt-4"
    timeout: int = 300
    max_retries: int = 3
    enable_ai: bool = True


class BaseAgent(ABC):
    """
    Agent基类
    
    所有Agent的抽象基类，定义了:
    - 与LangGraph状态机集成的接口
    - 底层引擎初始化模式
    - 通用错误处理和消息记录
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent
        
        Args:
            config: Agent配置字典
        """
        self.config = config or {}
        self.agent_type = self.__class__.__name__
        self._initialize_engine()
        logger.info(f"{self.agent_type} initialized with config: {self.config}")
    
    @abstractmethod
    def _initialize_engine(self) -> None:
        """
        初始化底层引擎
        
        子类必须实现此方法以初始化对应的Core Engine
        """
        pass
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        LangGraph节点入口
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            logger.info(f"{self.agent_type} executing with task_id={state.get('task_id')}")
            
            # 执行Agent逻辑
            result = await self.execute(state)
            
            # 合并状态
            merged: AgentState = {**state, **result}  # type: ignore[assignment]
            
            # 添加执行消息
            messages = merged.get("messages", [])
            messages.append(f"{self.agent_type}: 执行完成")
            merged["messages"] = messages
            
            return merged
        except Exception as e:
            logger.error(f"{self.agent_type} execution failed: {e}")
            errors = state.get("errors", [])
            errors.append(f"{self.agent_type}错误: {str(e)}")
            return {
                "task_id": state.get("task_id", ""),
                "iteration": state.get("iteration", 0),
                "max_iterations": state.get("max_iterations", 10),
                "repo_path": state.get("repo_path", ""),
                "current_commit": state.get("current_commit", ""),
                "target_files": state.get("target_files", []),
                "patch_content": state.get("patch_content", ""),
                "patch_applied": state.get("patch_applied", False),
                "test_plan": state.get("test_plan", {}),
                "test_results": state.get("test_results", []),
                "artifacts": state.get("artifacts", []),
                "analysis_report": state.get("analysis_report", {}),
                "next_action": "escalate",
                "converged": False,
                "messages": state.get("messages", []),
                "errors": errors
            }
    
    @abstractmethod
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        执行Agent核心逻辑
        
        子类必须实现此方法
        
        Args:
            state: 当前状态
            
        Returns:
            状态更新字典，将与原状态合并
        """
        pass
    
    def _add_message(self, state: AgentState, message: str) -> Dict[str, Any]:
        """添加消息到状态"""
        messages = state.get("messages", [])
        messages.append(message)
        return {"messages": messages}
    
    def _add_error(self, state: AgentState, error: str) -> Dict[str, Any]:
        """添加错误到状态"""
        errors = state.get("errors", [])
        errors.append(error)
        return {"errors": errors}
    
    def _check_convergence(self, state: AgentState, pass_rate: float) -> Dict[str, Any]:
        """检查是否收敛"""
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 10)
        
        converged = (
            pass_rate >= 0.8 or  # 通过率达到80%
            iteration >= max_iterations  # 达到最大迭代次数
        )
        
        return {"converged": converged}
