# Judgement Module

In this module, we hope we can judge agent's generated output with **model-based judgement** and **rule-based judgement**.

## Data Loading

这一部分需要用户手动实现（为了适配各种数据模式），但是需要保证数据是这样的基本格式并且一定要有 answer 这一项。

```json
{
    "query": "",
    "answer": "",
    "GT": "",
    "system_prompt_kwargs": {},
    "user_prompt_kwargs": {}
}
```

## Judgement

在这里需要提供一个 Judgement 的接口，并且自动提取结构化的信息和统计量。

### Model-Based Judgement

仍然需要用户手动构建提示词，这一部分的参考方式可以见 `./data_generation/pipeline.py` 并且**用户需要手动提供一个提取函数**。

> 这里本质可以看作是一种 `data_generation` 的实例化。

### Rule-Based Judgement

Rule-Based Judgement 更多作为一种统计信息出现，默认需要统计的信息是：
- Numbers of GT tokens
- Numbers of answer tokens
- Numbers of query tokens

这一部分也支持用户手动传入 Rule-Based 的解析函数（例如解析调用工具的数量等等）

最终用户需要传入的参数是：

```json
{
    "count-tools": count_tool,
    // count_tool 是传入的用户自定义函数
    ...
}
```

而对于每一个评测单元（一条数据），模型需要输出一个 json 数据：

```json
{
    "query-token-count": 100,
    "answer-token-count": 100,
    "GT-token-count": 100,
    // 上面的三个是默认统计的 Rule-based 的参数统计量，
    "count-tools": 12
    // 这些是用户传入的自定义函数的返回结果
}
```

因此，最终对于一个评测单元，生成如下的一个 json 格式的文件：

```json
{
    "model-based-judgement": {...},
    "rule-based-judgement": {...},
}
```

For example:

```json
{"input": {"query": "什么是RESTful API？它的设计原则是什么？", "answer": "RESTful API是一种基于HTTP协议的API设计风格，遵循REST（表述性状态转移）架构约束。设计原则包括：使用HTTP动词（GET、POST、PUT、DELETE等）、资源导向、无状态、统一接口、缓存友好等。它使API更加直观和易于使用。", "GT": "RESTful API是基于HTTP的API设计风格，原则：HTTP动词、资源导向、无状态、统一接口、缓存友好", "meta_info": {"model_name": "gpt-4"}, "system_prompt_kwargs": {"role": "API设计专家"}, "user_prompt_kwargs": {"question": "什么是RESTful API？它的设计原则是什么？", "reference_answer": "RESTful API是基于HTTP的API设计风格，原则：HTTP动词、资源导向、无状态、统一接口、缓存友好", "model_response": "RESTful API是一种基于HTTP协议的API设计风格，遵循REST（表述性状态转移）架构约束。设计原则包括：使用HTTP动词（GET、POST、PUT、DELETE等）、资源导向、无状态、统一接口、缓存友好等。它使API更加直观和易于使用。"}}, "model_based_judgement": {"accuracy": 8, "relevance": 10, "clarity": 8, "completeness": 7, "overall": 8, "comment": null}, "rule_based_judgement": {"answer-token-count": 93, "query-token-count": 19, "GT-token-count": 39, "count-tools": 0}, "timestamp": "2025-11-17T10:22:36.238280"}
```

## 数据的存储

对于每一次实验，都需要指定:

- job_name
- experiment_name

存储的输出在 `./job_name/experiment_name/` 中，存储的信息是一个带时间戳的 jsonl 文件，这个文件每一行就是测评结果。支持实时写入。

> todo: 后续加入 Resume Download 提升效率

## Usage

### Simple Workflow

> [!IMPORTANT]
> 最基本的评判工作流，支持对数据进行批量自动化评估。

- 在配置中准备好 user_prompt 和 system_prompt 的模版
- 自定义生成 data_pool 的函数，数据格式如下：
    - 要求返回一个 List，List 中的每一个元素是包含 `query`, `answer`, `GT` 的字典
    - 在后续的评判中，pipeline 会自动的将输入的这些模板填充到 user prompt 和 system prompt 中，形成 ready 的 对话版本的提示词
- 模型调用的版本已经封装完成（带安全限制的高并发模型）
- **需要提供一个 model_judgement_function()** 函数，将模型输出的评判内容进行格式化处理，返回结构化的评分结果。
- **需要提供一个 rule_functions** 字典，包含用户自定义的规则函数
- 最终评判结果会记录在对应的 jsonl 文件中，可以选择文件是否需要带上时间戳

```python
def load_judgement_data():
    """
    加载示例评判数据
    """
    data_pool = [
        {
            "query": "人工智能的主要应用领域有哪些？",
            "answer": "AI技术在医疗诊断、金融风控、自动驾驶、智能教育、工业制造等方面都有重要应用",
            "GT": "人工智能广泛应用于医疗、金融、交通、教育、制造业等领域",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "专业AI评估师"
            },
            "user_prompt_kwargs": {
                "question": "人工智能的主要应用领域有哪些？",
                "reference_answer": "人工智能广泛应用于医疗、金融、交通、教育、制造业等领域",
                "model_response": "AI技术在医疗诊断、金融风控、自动驾驶、智能教育、工业制造等方面都有重要应用"
            }
        },
        {
            "query": "机器学习和深度学习有什么区别？",
            "answer": "机器学习是人工智能的一个分支，而深度学习是机器学习的一种特殊形式，它主要使用多层神经网络结构来模拟人脑的学习过程",
            "GT": "机器学习是AI的子集，深度学习是机器学习的子集。深度学习使用神经网络",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "专业AI评估师"
            },
            "user_prompt_kwargs": {
                "question": "机器学习和深度学习有什么区别？",
                "reference_answer": "机器学习是AI的子集，深度学习是机器学习的子集。深度学习使用神经网络",
                "model_response": "机器学习是人工智能的一个分支，而深度学习是机器学习的一种特殊形式，它主要使用多层神经网络结构来模拟人脑的学习过程"
            }
        }
    ]
    return data_pool

def count_tools_usage(input_data):
    """
    示例自定义规则函数：计算工具使用次数
    """
    # 这里只是一个示例，实际应用中可以根据 input_data 的内容计算工具使用次数
    answer = input_data.get("answer", "")
    # 假设在 answer 中查找工具使用次数（这里只是示例逻辑）
    return answer.count("工具")  # 示例：计算"工具"一词出现的次数
```

```python
"""
示例：使用 JudgementPipeline 进行评判
这个示例展示了如何使用 JudgementPipeline 类进行数据评判，并演示了参数覆盖功能
"""

import sys
import os

sys.path.append(os.getcwd())
from judgement import JudgementPipeline, JudgementStats


def load_judgement_data():
    """
    加载示例评判数据
    """
    data_pool = [
        {
            "query": "人工智能的主要应用领域有哪些？",
            "answer": "AI技术在医疗诊断、金融风控、自动驾驶、智能教育、工业制造等方面都有重要应用",
            "GT": "人工智能广泛应用于医疗、金融、交通、教育、制造业等领域",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "专业AI评估师"
            },
            "user_prompt_kwargs": {
                "question": "人工智能的主要应用领域有哪些？",
                "reference_answer": "人工智能广泛应用于医疗、金融、交通、教育、制造业等领域",
                "model_response": "AI技术在医疗诊断、金融风控、自动驾驶、智能教育、工业制造等方面都有重要应用"
            }
        },
        {
            "query": "机器学习和深度学习有什么区别？",
            "answer": "机器学习是人工智能的一个分支，而深度学习是机器学习的一种特殊形式，它主要使用多层神经网络结构来模拟人脑的学习过程",
            "GT": "机器学习是AI的子集，深度学习是机器学习的子集。深度学习使用神经网络",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "专业AI评估师"
            },
            "user_prompt_kwargs": {
                "question": "机器学习和深度学习有什么区别？",
                "reference_answer": "机器学习是AI的子集，深度学习是机器学习的子集。深度学习使用神经网络",
                "model_response": "机器学习是人工智能的一个分支，而深度学习是机器学习的一种特殊形式，它主要使用多层神经网络结构来模拟人脑的学习过程"
            }
        }
    ]
    return data_pool


def count_tools_usage(input_data):
    """
    示例自定义规则函数：计算工具使用次数
    """
    # 这里只是一个示例，实际应用中可以根据 input_data 的内容计算工具使用次数
    answer = input_data.get("answer", "")
    # 假设在 answer 中查找工具使用次数（这里只是示例逻辑）
    return answer.count("工具")  # 示例：计算"工具"一词出现的次数


def main():
    pipeline = JudgementPipeline(
        job_name="my_job",
        experiment_name="my_experiment",
        temperature=0.5,  # 覆盖模型温度
        max_tokens=1024,  # 覆盖最大token数
        system_prompt_path="prompt/system_prompts/default.prompt_evaluation.txt",  # 覆盖系统提示词路径
        user_prompt_path="prompt/user_prompts/default.prompt_evaluation.txt",  # 覆盖用户提示词路径
        output_data={
            "output_dir": "output",
            "experiment_name": "judgement_demo",
            "need_time_stamp": True,
        },
        need_time_stamp=False
    )
    data_pool = load_judgement_data()
    
    # 定义规则函数
    rule_functions = {
        "count-tools": count_tools_usage
    }
    
    results = pipeline.run(
        data_pool,
        concurrency_limit=3,
        model_judgement_function=pipeline.make_judgement_extractor(),  # 使用内置的评判提取器
        rule_functions=rule_functions  # 传入自定义规则函数
    )
    print(results)


if __name__ == "__main__":
    main()
```

### 统计功能

评判任务完成后，可以使用 `JudgementStats` 类对结果进行统计分析：

```python
from judgement import JudgementStats

def main():
    # ... (运行评判任务) ...
    
    # 使用统计模块分析结果
    stats = JudgementStats()
    
    # 定义需要统计的数值字段
    numeric_fields = [
        "model_based_judgement.accuracy",
        "model_based_judgement.relevance", 
        "model_based_judgement.clarity",
        "model_based_judgement.completeness",
        "model_based_judgement.overall",
        "rule_based_judgement.answer-token-count",
        "rule_based_judgement.query-token-count",
        "rule_based_judgement.GT-token-count",
        "rule_based_judgement.count-tools"
    ]
    
    # 定义需要统计分布的字段
    distribution_fields = [
        "model_based_judgement.accuracy",
        "model_based_judgement.overall"
    ]
    
    # 生成并打印统计报告
    stats.print_report(
        pipeline.experiment_path,  # 使用pipeline生成的实验结果文件路径
        numeric_fields=numeric_fields,
        distribution_fields=distribution_fields
    )
```
