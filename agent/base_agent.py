"""
基本的 Agent 类，功能包括：
- 参数初始化
- 基本的多轮对话管理
- 导出聊天记录
- 并发调用接口
"""
import json
import asyncio
from typing import List, Dict, Optional, Any
from utils.llm_client import OpenAIClient


class BaseAgent:
    """
    基本的 Agent 类，提供多轮对话管理、聊天记录导出和并发调用接口功能
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 Agent
        
        Args:
            config: Agent 配置参数
        """
        self.config = config or {}
        self.client = OpenAIClient(config)
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_concurrent_calls = self.config.get('max_concurrent_calls', 5)
        
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        添加消息到对话历史
        
        Args:
            role: 消息角色 (user, assistant, system, function)
            content: 消息内容
            **kwargs: 其他消息字段
        """
        message = {
            "role": role,
            "content": content,
            **kwargs
        }
        self.conversation_history.append(message)
        
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史记录
        
        Returns:
            对话历史记录列表
        """
        return self.conversation_history.copy()
        
    def export_conversation(self, file_path: str) -> None:
        """
        导出聊天记录到文件
        
        Args:
            file_path: 导出文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
    async def chat(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        进行单轮对话
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            
        Returns:
            模型回复内容
        """
        # 添加用户消息到历史记录
        self.add_message("user", prompt)
        
        # 调用 LLM 获取回复
        response = await self.client.chat_completion(prompt, system_prompt)
        
        if response:
            # 添加助手回复到历史记录
            self.add_message("assistant", response)
            
        return response
        