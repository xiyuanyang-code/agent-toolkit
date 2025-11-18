import json
import os
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
import dotenv
import re
import asyncio
from tqdm import tqdm
from utils.llm_client import OpenAIClient
from utils.logger_config import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

dotenv.load_dotenv(override=True)


class DataGenerationPipeline:
    """
    数据合成自动化Pipeline类
    """

    def __init__(self, config_path: str = "./config/data_generation.yaml", **kwargs):
        """
        初始化Pipeline

        Args:
            config_path (str): 配置文件路径
            **kwargs: 用于覆盖配置文件中的参数
        """
        self.logger = get_logger(name="data_generation", log_file="data_generation.log")
        self.config_path = config_path
        self.config = self._load_config()
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # 用传入的参数覆盖配置文件中的参数
        self._update_config_with_kwargs(self.config, kwargs)

        self.config_for_client = self.config  # 保存配置以供线程中创建客户端使用
        self.output_dir = self._setup_output_dir()

        # prompt config path
        self.system_prompt_path = self.config.get("prompts", {}).get(
            "system_prompt_path"
        )
        self.user_prompt_path = self.config.get("prompts", {}).get("user_prompt_path")

        # 初始化文件锁和结果存储
        self.file_lock = threading.Lock()
        self.results = []

    def _update_config_with_kwargs(
        self, config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> None:
        """
        用关键字参数递归更新配置字典（不再支持 '.' 嵌套键）。

        Args:
            config: 配置字典（会被原地修改）
            kwargs: 关键字参数
        """

        def _recursive_update(d: Dict[str, Any], key: str, value: Any) -> bool:
            """
            在字典 d 中递归查找并更新 key。
            返回 True 表示已找到并更新，否则 False。
            """
            if key in d:
                d[key] = value
                return True

            for sub_key, sub_val in d.items():
                if isinstance(sub_val, dict):
                    if _recursive_update(sub_val, key, value):
                        return True
            return False

        for key, value in kwargs.items():
            if value is not None:  # 只有非 None 才更新
                found = _recursive_update(config, key, value)
                if found:
                    self.logger.info(f"Updating Configs for: {key}: {value}")
                else:
                    self.logger.warning(f"Key '{key}' not found in config, skipped.")

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            Dict[str, Any]: 配置字典
        """
        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def _setup_output_dir(self) -> str:
        """
        设置输出目录

        Returns:
            str: 输出目录路径
        """
        output_config: dict = self.config.get("output_data", {})
        output_dir = output_config.get("output_dir", "output")
        experiment_name = output_config.get("experiment_name", "experiment")
        need_time_stamp = output_config.get("need_time_stamp", True)
        if need_time_stamp:
            experiment_dir = os.path.join(output_dir, experiment_name, self.timestamp)
        else:
            experiment_dir = os.path.join(output_dir, experiment_name)
        self.experiment_dir = experiment_dir
        self.logger.info(f"Loading experiment: {experiment_dir}")
        self.experiment_path = os.path.join(self.experiment_dir, "result.jsonl")
        os.makedirs(experiment_dir, exist_ok=True)

        return experiment_dir

    def _load_prompt_from_file(self, file_path: str, **format_variables) -> str:
        """
        从文件加载提示词内容

        Args:
            file_path (str): 提示词文件路径

        Returns:
            str: 提示词内容
        """
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                prompt = file.read().strip()
                try:
                    # formatting prompt
                    prompt = prompt.format(**format_variables)
                except KeyError as e:
                    self.logger.warning(
                        f"Prompt formatting error, missing key: {e}. Using original prompt."
                    )
                except Exception as e:
                    self.logger.error(f"Error occurred while formatting strings: {e}")
                return prompt

        self.logger.error(f"Error, failed to load prompt file from {file_path}")
        return ""

    def save_result(self, result: Dict[str, Any]) -> None:
        """
        持续保存单个生成结果到jsonl文件

        Args:
            result (Dict[str, Any]): 单个生成结果
        """
        with self.file_lock:
            with open(self.experiment_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(result, ensure_ascii=False) + "\n")
            self.results.append(result)

    def extract_all(self, pattern_name: str, text: str) -> List[str]:
        """
        提取文本中所有 <pattern_name>...</pattern_name> 的内容（支持多行、属性、大小写）

        示例：
            extract_all("draft", "<draft>hello</draft>") -> ["hello"]
        """
        tag = re.escape(pattern_name.strip().lower())
        pattern = rf"<{tag}\b[^>]*>\s*(.*?)\s*</{tag}>"
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        return [m.strip() for m in matches]

    def make_default_extractor(
        self, pattern_name: str
    ) -> Callable[[str, str, bool], Optional[Union[str, List[str]]]]:
        """
        函数工厂：创建 default_extract 函数，绑定 extractor 实例。

        Args:
            extractor: 拥有 extract_all(pattern_name, text) 和 logger 的对象

        Returns:
            Callable: default_extract(pattern_name, response, to_list)
        """
        logger = self.logger

        def extract(response: str, to_list: bool = True) -> Union[List[str], str, None]:
            try:
                extract_list = self.extract_all(pattern_name, response)

                if not extract_list:
                    logger.warning(f"No <{pattern_name}> found in response.")
                    return [] if to_list else None

                return extract_list if to_list else extract_list[0]

            except Exception as e:
                logger.error(f"Extraction failed for <{pattern_name}>: {e}")
                return [] if to_list else None

        return extract

    async def run_single_queries(
        self,
        user_prompt: str,
        system_prompt: str,
        extract_function=None,
        input_data=None,
        client=None,
    ):
        # 如果提供了client参数，则使用它；否则使用实例的client
        client_to_use = client if client is not None else self.client
        response = await client_to_use.safe_chat_completion(
            prompt=user_prompt, system_prompt=system_prompt
        )

        # 构造结果字典
        result = {
            "input": input_data,
            "response": response,
            "timestamp": datetime.now().isoformat(),
        }

        # extract answer
        if extract_function:
            result["extracted"] = extract_function(response)

        # 持续保存结果
        self.save_result(result)

        return result

    async def run_single_task(
        self, i: int, input_data: Dict[str, Any], extract_function=None, client=None
    ):
        """处理单个任务"""
        try:
            self.logger.debug(f"Processing task {i+1}")
            self.logger.debug(f"Input data: {input_data}")

            self.logger.debug("Loading system prompt")
            system_prompt_kwargs = input_data.get("system_prompt_kwargs", {})
            system_prompt = self._load_prompt_from_file(
                self.system_prompt_path, **system_prompt_kwargs
            )
            self.logger.debug(f"System prompt: {system_prompt}")

            self.logger.debug("Loading user prompt")
            user_prompt_kwargs = input_data.get("user_prompt_kwargs", {})
            user_prompt = self._load_prompt_from_file(
                self.user_prompt_path, **user_prompt_kwargs
            )
            self.logger.debug(f"user prompt: {user_prompt}")

            result = await self.run_single_queries(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                input_data=input_data,
                extract_function=extract_function,
                client=client,
            )
            self.logger.debug(f"Getting result: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error processing task {i+1}: {e}")
            error_result = {
                "input": input_data,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.save_result(error_result)
            return error_result

    async def run_all_tasks(
        self, data_pool, concurrency_limit: int = 5, extract_function: Callable = None
    ):
        sem = asyncio.Semaphore(concurrency_limit)

        async def worker(i, input_data):
            async with sem:
                client = OpenAIClient(self.config_for_client)
                return await self.run_single_task(
                    i, input_data, extract_function, client
                )

        tasks = [worker(i, x) for i, x in enumerate(data_pool)]
        results = []
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            results.append(await coro)
        return results

    def run(
        self, data_pool, concurrency_limit: int = 5, extract_function: Callable = None
    ):
        """
        运行数据生成管道，支持并发处理

        Args:
            data_pool: 数据池
            concurrency_limit (int): 并发限制数量，默认为5
        """
        self.logger.info("Starting data generation pipeline")
        self.logger.info(f"Concurrency limit: {concurrency_limit}")
        self.logger.info(f"Total tasks: {len(data_pool)}")

        results = asyncio.run(
            self.run_all_tasks(
                data_pool=data_pool,
                concurrency_limit=concurrency_limit,
                extract_function=extract_function,
            )
        )

        # # 定义执行单个任务的函数
        # def run_single_task_sync(i: int, input_data: Dict[str, Any]):
        #     # 在线程中创建新的客户端实例
        #     client = OpenAIClient(self.config_for_client)

        #     # 创建一个新的事件循环
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)

        #     try:
        #         # 在新的事件循环中运行异步任务
        #         result = loop.run_until_complete(
        #             self.run_single_task(
        #                 i, input_data, extract_function=extract_function, client=client
        #             )
        #         )
        #         return result
        #     finally:
        #         loop.close()

        # 使用线程池执行器
        # with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
        #     futures = [
        #         executor.submit(run_single_task_sync, i, input_data)
        #         for i, input_data in enumerate(data_pool)
        #     ]

        #     # 创建进度条
        #     pbar = tqdm(total=len(data_pool), desc="Processing tasks", unit="task")

        #     # 收集结果
        #     results = []
        #     completed = 0
        #     for future in as_completed(futures):
        #         result = future.result()
        #         results.append(result)
        #         completed += 1
        #         pbar.update(1)
        #         pbar.set_postfix({"Completed": f"{completed}/{len(data_pool)}"})

        #     pbar.close()

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {i+1} failed with exception: {result}")
                processed_results.append(
                    {"error": f"Task failed with exception: {result}", "index": i}
                )
            else:
                processed_results.append(result)

        self.logger.info("Data generation pipeline completed")
        return processed_results
