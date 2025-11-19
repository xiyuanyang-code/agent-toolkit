"""
Tool Enhancement Interface
- 工具调用接口 OpenAI SDK 的接口
"""
from typing import Dict, Any, List, Optional, Callable
import json


class ToolEnhancer:
    """
    工具增强接口，用于处理工具调用
    """
    
    def __init__(self, tools: List[Dict[str, Any]] = None):
        """
        初始化工具增强器
        
        Args:
            tools: 工具定义列表
        """
        self.tools: List[Dict[str, Any]] = tools or []
        self.functions: Dict[str, Callable] = {}
        
    def add_tool(self, tool: Dict[str, Any]) -> None:
        """
        添加工具
        
        Args:
            tool: 工具定义
        """
        self.tools.append(tool)
        
    def register_function(self, name: str, func: Callable) -> None:
        """
        注册工具对应的执行函数
        
        Args:
            name: 函数名称
            func: 执行函数
        """
        self.functions[name] = func
        
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义
        
        Returns:
            工具定义列表
        """
        return self.tools
        
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        执行指定工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.functions:
            return {
                "error": f"Function {tool_name} not found",
                "tool_name": tool_name
            }
            
        try:
            # 执行函数并返回结果
            result = self.functions[tool_name](**arguments)
            return {
                "result": result,
                "tool_name": tool_name
            }
        except Exception as e:
            return {
                "error": str(e),
                "tool_name": tool_name
            }
            
    def format_tools_for_api(self) -> List[Dict[str, Any]]:
        """
        格式化工具定义以适应 API 调用
        
        Returns:
            格式化后的工具定义列表
        """
        return self.tools