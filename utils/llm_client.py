import os
import asyncio
import logging
import time
from typing import Optional
from openai import AsyncOpenAI
from utils.logger_config import get_logger
import dotenv

logger = get_logger(name="openai-llm", log_file="llm.log")
dotenv.load_dotenv(override=True)


class RateLimiter:
    """
    速率限制器类，用于控制API调用频率
    
    Args:
        max_per_minute (int): 每分钟最大请求数
    """
    
    def __init__(self, max_per_minute: int):
        self.interval = 60.0 / max_per_minute
        self.lock = asyncio.Lock()
        self.last = 0

    async def acquire(self):
        """
        获取令牌，如果需要则等待
        """
        async with self.lock:
            now = time.monotonic()
            wait_time = self.interval - (now - self.last)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last = time.monotonic()


class OpenAIClient:
    """
    OpenAI API 客户端封装类
    """
    
    def __init__(self, config: dict = None):
        """初始化 OpenAI 客户端"""
        if config and 'model' in config:
            model_config = config['model']
            api_key = model_config.get("api_key")
            api_base = model_config.get("base_url")
            self.model_name = model_config.get("model", "gpt-4o-2024-11-20")
            self.max_tokens = model_config.get("max_tokens", 5042)
            self.temperature = model_config.get("temperature", 1.0)
            rate_limit = model_config.get("rate_limit", 200)
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            api_base = os.environ.get("OPENAI_API_BASE")
            self.model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-2024-11-20")
            self.max_tokens = 5042
            self.temperature = 1.0
            rate_limit = 200
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置")
            
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base
        )
        
        # 初始化速率限制器
        self.rate_limiter = RateLimiter(max_per_minute=rate_limit)
        logger.debug("Successfully initialize OpenAIClient")
    
    async def chat_completion(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        调用 OpenAI 聊天完成接口
        
        Args:
            prompt (str): 发送给模型的提示
            system_prompt (str): 系统提示词
            
        Returns:
            Optional[str]: 模型的回复内容，如果出错则返回 None
        """
        await self.rate_limiter.acquire()
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                messages=messages,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return None
    
    async def safe_chat_completion(self, prompt: str, system_prompt: str = None, timeout: int = 3600) -> Optional[str]:
        """
        带超时保护的聊天完成接口
        
        Args:
            prompt (str): 发送给模型的提示
            system_prompt (str): 系统提示词
            timeout (int): 超时时间（秒）
            
        Returns:
            Optional[str]: 模型的回复内容，如果超时或出错则返回 None
        """
        try:
            return await asyncio.wait_for(self.chat_completion(prompt, system_prompt), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] 提示: {prompt[:50]}...")
            return None
        except Exception as e:
            logger.error(f"[ERROR] API 调用失败: {e}")
            return None