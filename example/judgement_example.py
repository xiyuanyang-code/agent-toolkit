"""
示例：使用 JudgementPipeline 进行评判
这个示例展示了如何使用 JudgementPipeline 类进行数据评判，并演示了参数覆盖功能
"""

import sys
import os

sys.path.append(os.getcwd())
from judgement import JudgementPipeline,JudgementStats


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
        },
        {
            "query": "Python编程语言有什么优势？",
            "answer": "Python具有简洁易读的语法，丰富的第三方库，跨平台兼容性，以及强大的社区支持。它适用于Web开发、数据科学、人工智能等多个领域。",
            "GT": "Python优点包括：语法简洁、库丰富、易学易用、跨平台、社区活跃",
            "meta_info": {
                "model_name": "claude-3"
            },
            "system_prompt_kwargs": {
                "role": "编程语言专家"
            },
            "user_prompt_kwargs": {
                "question": "Python编程语言有什么优势？",
                "reference_answer": "Python优点包括：语法简洁、库丰富、易学易用、跨平台、社区活跃",
                "model_response": "Python具有简洁易读的语法，丰富的第三方库，跨平台兼容性，以及强大的社区支持。它适用于Web开发、数据科学、人工智能等多个领域。"
            }
        },
        {
            "query": "什么是区块链技术？",
            "answer": "区块链是一种去中心化的分布式账本技术，通过密码学方法将数据块按时间顺序连接起来，形成不可篡改的链式结构。它具有去中心化、透明性、不可篡改等特点，广泛应用于数字货币、智能合约等领域。",
            "GT": "区块链是去中心化账本技术，通过密码学连接数据块，具有去中心化、透明、不可篡等特性",
            "meta_info": {
                "model_name": "gpt-4"
            },
            "system_prompt_kwargs": {
                "role": "区块链技术专家"
            },
            "user_prompt_kwargs": {
                "question": "什么是区块链技术？",
                "reference_answer": "区块链是去中心化账本技术，通过密码学连接数据块，具有去中心化、透明、不可篡等特性",
                "model_response": "区块链是一种去中心化的分布式账本技术，通过密码学方法将数据块按时间顺序连接起来，形成不可篡改的链式结构。它具有去中心化、透明性、不可篡改等特点，广泛应用于数字货币、智能合约等领域。"
            }
        },
        {
            "query": "解释一下HTTP和HTTPS的区别",
            "answer": "HTTP是超文本传输协议，使用明文传输数据，端口为80；HTTPS是安全的超文本传输协议，在HTTP基础上加入了SSL/TLS加密层，使用端口443。HTTPS更加安全，可以保护数据传输过程中的隐私和完整性。",
            "GT": "HTTP使用明文传输，端口80；HTTPS使用SSL/TLS加密，端口443，更安全",
            "meta_info": {
                "model_name": "gpt-3.5"
            },
            "system_prompt_kwargs": {
                "role": "网络协议专家"
            },
            "user_prompt_kwargs": {
                "question": "解释一下HTTP和HTTPS的区别",
                "reference_answer": "HTTP使用明文传输，端口80；HTTPS使用SSL/TLS加密，端口443，更安全",
                "model_response": "HTTP是超文本传输协议，使用明文传输数据，端口为80；HTTPS是安全的超文本传输协议，在HTTP基础上加入了SSL/TLS加密层，使用端口443。HTTPS更加安全，可以保护数据传输过程中的隐私和完整性。"
            }
        },
        {
            "query": "量子计算的基本原理是什么？",
            "answer": "量子计算利用量子比特（qubit）的叠加态和纠缠态进行计算，通过量子门操作来处理信息。其核心原理包括量子叠加、量子纠缠和量子干涉，这些特性使得量子计算机在某些特定问题上具有超越经典计算机的计算能力。",
            "GT": "量子计算利用qubit的叠加和纠缠，通过量子门操作处理信息",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "量子计算专家"
            },
            "user_prompt_kwargs": {
                "question": "量子计算的基本原理是什么？",
                "reference_answer": "量子计算利用qubit的叠加和纠缠，通过量子门操作处理信息",
                "model_response": "量子计算利用量子比特（qubit）的叠加态和纠缠态进行计算，通过量子门操作来处理信息。其核心原理包括量子叠加、量子纠缠和量子干涉，这些特性使得量子计算机在某些特定问题上具有超越经典计算机的计算能力。"
            }
        },
        {
            "query": "请描述一下微服务架构的优缺点",
            "answer": "微服务架构的优点包括：服务独立部署、技术栈灵活、易于扩展、故障隔离。缺点包括：分布式复杂性增加、数据一致性挑战、运维难度提升、网络延迟问题。",
            "GT": "优点：服务独立、技术灵活、易扩展、故障隔离；缺点：分布式复杂、数据一致性难、运维难、网络延迟",
            "meta_info": {
                "model_name": "claude-3"
            },
            "system_prompt_kwargs": {
                "role": "系统架构师"
            },
            "user_prompt_kwargs": {
                "question": "请描述一下微服务架构的优缺点",
                "reference_answer": "优点：服务独立、技术灵活、易扩展、故障隔离；缺点：分布式复杂、数据一致性难、运维难、网络延迟",
                "model_response": "微服务架构的优点包括：服务独立部署、技术栈灵活、易于扩展、故障隔离。缺点包括：分布式复杂性增加、数据一致性挑战、运维难度提升、网络延迟问题。"
            }
        },
        {
            "query": "什么是设计模式？举例说明几种常见的设计模式",
            "answer": "设计模式是软件开发中解决常见问题的可重用解决方案。常见设计模式包括：单例模式（确保类只有一个实例）、工厂模式（创建对象的接口）、观察者模式（对象间一对多依赖关系）、装饰器模式（动态添加职责）等。",
            "GT": "设计模式是解决常见问题的可重用方案，常见模式有：单例、工厂、观察者、装饰器等",
            "meta_info": {
                "model_name": "gpt-4"
            },
            "system_prompt_kwargs": {
                "role": "软件设计专家"
            },
            "user_prompt_kwargs": {
                "question": "什么是设计模式？举例说明几种常见的设计模式",
                "reference_answer": "设计模式是解决常见问题的可重用方案，常见模式有：单例、工厂、观察者、装饰器等",
                "model_response": "设计模式是软件开发中解决常见问题的可重用解决方案。常见设计模式包括：单例模式（确保类只有一个实例）、工厂模式（创建对象的接口）、观察者模式（对象间一对多依赖关系）、装饰器模式（动态添加职责）等。"
            }
        },
        {
            "query": "解释一下机器学习中的过拟合现象",
            "answer": "过拟合是指模型在训练数据上表现很好，但在测试数据上表现较差的现象。主要原因是模型过于复杂，学习了训练数据中的噪声和细节。解决方法包括：增加训练数据、使用正则化、简化模型、使用交叉验证、早停等。",
            "GT": "过拟合是模型在训练数据上表现好但在测试数据上差的现象，原因模型太复杂学了噪声，解决方法：增数据、正则化、简化模型、交叉验证等",
            "meta_info": {
                "model_name": "gpt-3.5"
            },
            "system_prompt_kwargs": {
                "role": "机器学习专家"
            },
            "user_prompt_kwargs": {
                "question": "解释一下机器学习中的过拟合现象",
                "reference_answer": "过拟合是模型在训练数据上表现好但在测试数据上差的现象，原因模型太复杂学了噪声，解决方法：增数据、正则化、简化模型、交叉验证等",
                "model_response": "过拟合是指模型在训练数据上表现很好，但在测试数据上表现较差的现象。主要原因是模型过于复杂，学习了训练数据中的噪声和细节。解决方法包括：增加训练数据、使用正则化、简化模型、使用交叉验证、早停等。"
            }
        },
        {
            "query": "数据库索引的作用和类型有哪些？",
            "answer": "数据库索引用于提高查询效率，通过创建有序的数据结构来快速定位记录。主要类型包括：B树索引、哈希索引、全文索引、位图索引等。索引虽然能提升查询速度，但也会占用存储空间并影响写入性能。",
            "GT": "索引用于提高查询效率，类型包括：B树索引、哈希索引、全文索引、位图索引等，优点提升查询，缺点占空间影响写入",
            "meta_info": {
                "model_name": "gpt-4o"
            },
            "system_prompt_kwargs": {
                "role": "数据库专家"
            },
            "user_prompt_kwargs": {
                "question": "数据库索引的作用和类型有哪些？",
                "reference_answer": "索引用于提高查询效率，类型包括：B树索引、哈希索引、全文索引、位图索引等，优点提升查询，缺点占空间影响写入",
                "model_response": "数据库索引用于提高查询效率，通过创建有序的数据结构来快速定位记录。主要类型包括：B树索引、哈希索引、全文索引、位图索引等。索引虽然能提升查询速度，但也会占用存储空间并影响写入性能。"
            }
        },
        {
            "query": "请解释一下容器化技术（Docker）的优势",
            "answer": "Docker容器化技术的优势包括：环境一致性（一次打包，到处运行）、快速部署和启动、资源利用率高、易于版本控制和回滚、简化依赖管理、支持微服务架构等。它解决了'在我机器上能运行'的经典问题。",
            "GT": "Docker优势：环境一致性、快速部署、资源利用率高、易版本控制、简化依赖、支持微服务，解决环境不一致问题",
            "meta_info": {
                "model_name": "claude-3"
            },
            "system_prompt_kwargs": {
                "role": "DevOps专家"
            },
            "user_prompt_kwargs": {
                "question": "请解释一下容器化技术（Docker）的优势",
                "reference_answer": "Docker优势：环境一致性、快速部署、资源利用率高、易版本控制、简化依赖、支持微服务，解决环境不一致问题",
                "model_response": "Docker容器化技术的优势包括：环境一致性（一次打包，到处运行）、快速部署和启动、资源利用率高、易于版本控制和回滚、简化依赖管理、支持微服务架构等。它解决了'在我机器上能运行'的经典问题。"
            }
        },
        {
            "query": "什么是RESTful API？它的设计原则是什么？",
            "answer": "RESTful API是一种基于HTTP协议的API设计风格，遵循REST（表述性状态转移）架构约束。设计原则包括：使用HTTP动词（GET、POST、PUT、DELETE等）、资源导向、无状态、统一接口、缓存友好等。它使API更加直观和易于使用。",
            "GT": "RESTful API是基于HTTP的API设计风格，原则：HTTP动词、资源导向、无状态、统一接口、缓存友好",
            "meta_info": {
                "model_name": "gpt-4"
            },
            "system_prompt_kwargs": {
                "role": "API设计专家"
            },
            "user_prompt_kwargs": {
                "question": "什么是RESTful API？它的设计原则是什么？",
                "reference_answer": "RESTful API是基于HTTP的API设计风格，原则：HTTP动词、资源导向、无状态、统一接口、缓存友好",
                "model_response": "RESTful API是一种基于HTTP协议的API设计风格，遵循REST（表述性状态转移）架构约束。设计原则包括：使用HTTP动词（GET、POST、PUT、DELETE等）、资源导向、无状态、统一接口、缓存友好等。它使API更加直观和易于使用。"
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


if __name__ == "__main__":
    main()