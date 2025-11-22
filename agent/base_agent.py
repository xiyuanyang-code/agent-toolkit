"""
基本的 Agent 类，功能包括：
- 参数初始化
- 基本的多轮对话管理
- 导出聊天记录
- 并发调用接口
"""

import json
import openai
import yaml
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from datetime import datetime
from utils.logger_config import get_logger
from typing import List, Dict, Optional, Any


class BaseAgent:
    """Design for base agent, supporting simple memory, tools and reasoning enhancement."""

    def __init__(
        self,
        experiment_name: str = None,
        config_path: str = "./config/agent_config.yaml",
    ):
        self.logger = get_logger(name="base-agent", log_file="agent.log")
        self.config_path = config_path
        if not os.path.exists(self.config_path):
            self.logger.error("Error, the config path does not exist.")
            raise FileNotFoundError

        with open(self.config_path, "r", encoding="utf-8") as file:
            self.config_data: Dict = yaml.safe_load(file)

        self.api_key = self.config_data.get("api_key", "")
        self.base_url = self.config_data.get("base_url", "")
        self.timeout = self.config_data.get("time_out", 600)
        self.model_name = self.config_data.get("model_name", "gpt-4o-mini")

        self.time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.experiment_name = (
            experiment_name if experiment_name else f"exp_{self.time_stamp}"
        )
        self.record_path = self.config_data.get("record_path", "./logs/agent_records")
        self.record_file_path = os.path.join(
            self.record_path, f"{self.model_name}_{self.experiment_name}.json"
        )
        os.makedirs(self.record_path, exist_ok=True)

        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=3,
        )

        # initialize memory
        self.initialize_memory()

    def initialize_memory(self, system_prompt: str = "You are a helpful assistant"):
        # todo optimize agentic system prompt
        self.memory = []
        self.memory.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )
        pass

    def append_context(self, input_message: str, role: str = "user"):
        pass

    def update_records(self, record: Dict):
        write_content = json.dumps(record, ensure_ascii=False)
        with open(self.record_file_path, "a", encoding="utf-8") as file:
            file.write(write_content + "\n")
        self.logger.info(f"Writing records {write_content[:30]} to {self.record_file_path} successfully.")

    async def chat(
        self,
        input_message: str,
        role: str = "user",
        append_message: bool = True,
        timeout: float = 3600,
        reasoning_efforts: str = "medium",
    ):
        if append_message:
            input_messages: list = self.memory.copy()
            input_messages.append({"role": role, "content": input_message})
        else:
            input_messages: list = [{"role": role, "content": input_message}]

        response = await self.client.responses.create(
            model=self.model_name,
            reasoning={"effort": reasoning_efforts, "summary": "auto"},
            input=input_messages,
            timeout=timeout,
        )

        # update memory
        response_json = response.model_dump()
        self.update_records(response_json)



async def main():
    agent_test = BaseAgent()
    await agent_test.chat("解释一下概率密度函数和概率之间的区别是什么？")


if __name__ == "__main__":
    asyncio.run(main=main())
