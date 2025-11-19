"""
Memory Enhancement Interface:
- 上下文管理
- 如果上下文长度超过限制，需要自动启动压缩功能
"""
from typing import List, Dict, Any, Optional
import json


class MemoryEnhancer:
    """
    内存增强接口，提供上下文管理和自动压缩功能
    """
    
    def __init__(self, max_context_length: int = 4096, compression_threshold: float = 0.8):
        """
        初始化内存增强器
        
        Args:
            max_context_length: 最大上下文长度
            compression_threshold: 触发压缩的阈值（相对于最大长度的比例）
        """
        self.max_context_length = max_context_length
        self.compression_threshold = compression_threshold
        self.context: List[Dict[str, Any]] = []
        
    def add_context(self, message: Dict[str, Any]) -> None:
        """
        添加上下文消息
        
        Args:
            message: 要添加的消息
        """
        self.context.append(message)
        self._check_and_compress()
        
    def get_context(self) -> List[Dict[str, Any]]:
        """
        获取当前上下文
        
        Returns:
            上下文消息列表
        """
        return self.context.copy()
        
    def set_context(self, context: List[Dict[str, Any]]) -> None:
        """
        设置上下文
        
        Args:
            context: 新的上下文消息列表
        """
        self.context = context
        self._check_and_compress()
        
    def _check_and_compress(self) -> None:
        """
        检查上下文长度，如果超过阈值则执行压缩
        """
        current_length = self._calculate_context_length()
        if current_length > self.max_context_length * self.compression_threshold:
            self._compress_context()
            
    def _calculate_context_length(self) -> int:
        """
        计算当前上下文长度
        
        Returns:
            上下文长度（字符数）
        """
        total_length = 0
        for message in self.context:
            # 计算消息中所有字符串内容的长度
            for value in message.values():
                if isinstance(value, str):
                    total_length += len(value)
                elif isinstance(value, (dict, list)):
                    total_length += len(json.dumps(value, ensure_ascii=False))
        return total_length
        
    def _compress_context(self) -> None:
        """
        压缩上下文，保留重要的消息（如系统消息和最近的消息）
        """
        if len(self.context) <= 1:
            return  # 不能压缩到空上下文
            
        # 保留系统消息和最近的一定比例的消息
        system_messages = [msg for msg in self.context if msg.get('role') == 'system']
        non_system_messages = [msg for msg in self.context if msg.get('role') != 'system']
        
        # 计算需要保留的非系统消息数量（保留最近的 50%）
        keep_count = max(1, len(non_system_messages) // 2)
        kept_messages = non_system_messages[-keep_count:]
        
        # 重新构建上下文
        self.context = system_messages + kept_messages
        
        # 如果仍然超过长度限制，递归压缩
        if self._calculate_context_length() > self.max_context_length:
            self._compress_context()
            
    def clear_context(self) -> None:
        """
        清空上下文
        """
        self.context = []