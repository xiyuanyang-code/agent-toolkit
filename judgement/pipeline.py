import json
import os
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
import dotenv
import asyncio
import re
from tqdm import tqdm
from utils.llm_client import OpenAIClient
from utils.logger_config import get_logger
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

dotenv.load_dotenv(override=True)

class JudgementPipeline:
    """
    Judgement Pipeline类
    支持Model-Based Judgement和Rule-Based Judgement
    """

    def __init__(self, job_name: str, experiment_name: str, config_path: str = "./config/judgement.yaml", **kwargs):
        """
        初始化Pipeline

        Args:
            job_name (str): 任务名称
            experiment_name (str): 实验名称
            config_path (str): 配置文件路径
            **kwargs: 用于覆盖配置文件中的参数
        """
        self.logger = get_logger(name="judgement", log_file="judgement.log")
        self.config_path = config_path
        self.config = self._load_config()
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 任务和实验名称
        self.job_name = job_name
        self.experiment_name = experiment_name

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
        
        # 初始化tokenizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _update_config_with_kwargs(
        self, config: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> None:
        """
        用关键字参数递归更新配置字典

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
        job_dir = os.path.join(output_dir, self.job_name)
        experiment_dir = os.path.join(job_dir, self.experiment_name, self.timestamp)
        self.experiment_dir = experiment_dir
        self.logger.info(f"Loading experiment: {experiment_dir}")
        self.experiment_path = os.path.join(self.experiment_dir, "judgement_result.jsonl")
        os.makedirs(experiment_dir, exist_ok=True)

        return experiment_dir

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

    def extract_judgement_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取评判结果

        Args:
            response (str): LLM的响应内容

        Returns:
            Optional[Dict[str, Any]]: 提取的评判结果，如果未找到则返回None
        """
        try:
            accuracy_list = self.extract_all("accuracy", response)
            relevance_list = self.extract_all("relevance", response)
            clarity_list = self.extract_all("clarity", response)
            completeness_list = self.extract_all("completeness", response)
            overall_list = self.extract_all("overall", response)
            comment_list = self.extract_all("comment", response)

            # 取每个标签的最后一个值
            result = {
                "accuracy": int(accuracy_list[-1]) if accuracy_list else None,
                "relevance": int(relevance_list[-1]) if relevance_list else None,
                "clarity": int(clarity_list[-1]) if clarity_list else None,
                "completeness": int(completeness_list[-1]) if completeness_list else None,
                "overall": int(overall_list[-1]) if overall_list else None,
                "comment": comment_list[-1] if comment_list else None
            }

            return result
        except Exception as e:
            self.logger.error(f"Error extracting judgement from response using regex: {e}")

        return None

    def make_judgement_extractor(self) -> Callable[[str], Optional[Dict[str, Any]]]:
        """
        函数工厂：创建评判提取函数

        Returns:
            Callable: 评判提取函数
        """
        def extract_judgement(response: str) -> Optional[Dict[str, Any]]:
            return self.extract_judgement_from_response(response)

        return extract_judgement

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
        持续保存单个评测结果到jsonl文件

        Args:
            result (Dict[str, Any]): 单个评测结果
        """
        with self.file_lock:
            with open(self.experiment_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(result, ensure_ascii=False) + "\n")
            self.results.append(result)

    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text (str): 输入文本

        Returns:
            int: token数量
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    async def run_model_based_judgement(
        self, user_prompt: str, system_prompt: str, judgement_function=None, input_data=None, client=None
    ):
        """
        运行基于模型的评判

        Args:
            user_prompt (str): 用户提示词
            system_prompt (str): 系统提示词
            judgement_function (Callable): 评判函数
            input_data (Dict): 输入数据
            client: OpenAI客户端实例

        Returns:
            Dict: 评判结果
        """
        # 如果提供了client参数，则使用它；否则使用实例的client
        client_to_use = client if client is not None else self.client
        response = await client_to_use.safe_chat_completion(
            prompt=user_prompt, system_prompt=system_prompt
        )

        # 构造结果字典
        result = {
            "input": input_data,
            "model_response": response,
            "timestamp": datetime.now().isoformat(),
        }

        # 如果提供了评判函数，则处理评判结果
        if judgement_function:
            result["model_based_judgement"] = judgement_function(response)

        return result

    async def run_rule_based_judgement(
        self, input_data: Dict[str, Any], rule_functions: Dict[str, Callable] = None
    ):
        """
        运行基于规则的评判

        Args:
            input_data (Dict): 输入数据
            rule_functions (Dict): 规则函数字典

        Returns:
            Dict: 基于规则的评判结果
        """
        rule_judgement = {}

        # 默认统计信息 - 只统计存在的字段
        answer = input_data.get("answer", "")
        if answer:
            rule_judgement["answer-token-count"] = self.count_tokens(answer)
        
        query = input_data.get("query", "")
        if query:
            rule_judgement["query-token-count"] = self.count_tokens(query)
            
        gt = input_data.get("GT", "")
        if gt:
            rule_judgement["GT-token-count"] = self.count_tokens(gt)

        # 用户自定义规则函数
        if rule_functions:
            for key, func in rule_functions.items():
                try:
                    rule_judgement[key] = func(input_data)
                except Exception as e:
                    self.logger.error(f"Error running rule function {key}: {e}")
                    rule_judgement[key] = None

        return rule_judgement

    async def run_single_task(
        self, i: int, input_data: Dict[str, Any], 
        model_judgement_function=None, 
        rule_functions: Dict[str, Callable] = None,
        client=None
    ):
        """处理单个评判任务"""
        try:
            self.logger.debug(f"Processing judgement task {i+1}")
            self.logger.debug(f"Input data: {input_data}")

            # 检查必需字段
            if "answer" not in input_data or not input_data["answer"]:
                raise ValueError("Input data must contain a non-empty 'answer' field")

            # 运行基于模型的评判
            model_judgement = {}
            if self.system_prompt_path and self.user_prompt_path:
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

                model_judgement = await self.run_model_based_judgement(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    input_data=input_data,
                    judgement_function=model_judgement_function,
                    client=client,
                )
                self.logger.debug(f"Model-based judgement: {model_judgement}")
            else:
                self.logger.warning("System prompt path or user prompt path not set, skipping model-based judgement")

            # 运行基于规则的评判
            rule_judgement = await self.run_rule_based_judgement(
                input_data=input_data,
                rule_functions=rule_functions
            )
            self.logger.debug(f"Rule-based judgement: {rule_judgement}")

            # 合并结果
            result = {
                "input": input_data,
                "model_based_judgement": model_judgement.get("model_based_judgement", {}),
                "rule_based_judgement": rule_judgement,
                "timestamp": datetime.now().isoformat(),
            }

            # 持续保存结果
            self.save_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Error processing judgement task {i+1}: {e}")
            error_result = {
                "input": input_data,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.save_result(error_result)
            return error_result

    def run(
        self, data_pool, concurrency_limit: int = 5, 
        model_judgement_function: Callable = None,
        rule_functions: Dict[str, Callable] = None
    ):
        """
        运行评判管道，支持并发处理

        Args:
            data_pool: 数据池，包含需要评判的数据
            concurrency_limit (int): 并发限制数量，默认为5
            model_judgement_function (Callable): 模型评判函数
            rule_functions (Dict[str, Callable]): 规则函数字典
        """
        self.logger.info("Starting judgement pipeline")
        self.logger.info(f"Concurrency limit: {concurrency_limit}")
        self.logger.info(f"Total tasks: {len(data_pool)}")

        # 定义执行单个任务的函数
        def run_single_task_sync(i: int, input_data: Dict[str, Any]):
            # 在线程中创建新的客户端实例
            client = OpenAIClient(self.config_for_client)
            
            # 创建一个新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 在新的事件循环中运行异步任务
                result = loop.run_until_complete(self.run_single_task(
                    i, input_data, 
                    model_judgement_function=model_judgement_function,
                    rule_functions=rule_functions,
                    client=client
                ))
                return result
            finally:
                loop.close()

        # 使用线程池执行器
        with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
            futures = [
                executor.submit(run_single_task_sync, i, input_data)
                for i, input_data in enumerate(data_pool)
            ]

            # 创建进度条
            pbar = tqdm(total=len(data_pool), desc="Processing judgements", unit="task")
            
            # 收集结果
            results = []
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                pbar.update(1)
                pbar.set_postfix({"Completed": f"{completed}/{len(data_pool)}"})

            pbar.close()

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

        self.logger.info("Judgement pipeline completed")
        return processed_results