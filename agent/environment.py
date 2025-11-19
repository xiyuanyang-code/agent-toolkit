"""
Environment Enhancement:
- Environment 作为模拟环境与 Agent 交互
- Agent 通过一个 Tool Calling 的格式进行交互
"""
from typing import Dict, Any, List, Optional
from .tool import ToolEnhancer


class Environment:
    """
    环境类，模拟与 Agent 交互的外部环境
    """
    
    def __init__(self, tools: List[Dict[str, Any]] = None):
        """
        初始化环境
        
        Args:
            tools: 可用工具列表
        """
        self.tool_enhancer = ToolEnhancer(tools or [])
        self.state: Dict[str, Any] = {}
        
    def add_tool(self, tool: Dict[str, Any]) -> None:
        """
        添加工具到环境中
        
        Args:
            tool: 工具定义
        """
        self.tool_enhancer.add_tool(tool)
        
    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        return self.tool_enhancer.execute_tool(tool_name, arguments)
        
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具定义列表
        """
        return self.tool_enhancer.get_tools()
        
    def update_state(self, key: str, value: Any) -> None:
        """
        更新环境状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        self.state[key] = value
        
    def get_state(self, key: str) -> Any:
        """
        获取环境状态
        
        Args:
            key: 状态键
            
        Returns:
            状态值
        """
        return self.state.get(key)
        
    def get_full_state(self) -> Dict[str, Any]:
        """
        获取完整环境状态
        
        Returns:
            完整状态字典
        """
        return self.state.copy()