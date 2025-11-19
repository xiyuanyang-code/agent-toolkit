# Agent 框架接口设计与使用指南

## 概述

本项目实现了一个模块化的 Agent 框架，包含基础 Agent 功能、内存增强、环境模拟和工具调用等模块。框架采用面向对象设计，便于扩展和维护。

## 模块结构

### BaseAgent - 基础 Agent 类

基础 Agent 类提供核心的对话管理功能。

#### 接口

```python
class BaseAgent:
    def __init__(self, config: Dict[str, Any] = None)
    def add_message(self, role: str, content: str, **kwargs) -> None
    def get_conversation_history(self) -> List[Dict[str, Any]]
    def export_conversation(self, file_path: str) -> None
    async def chat(self, prompt: str, system_prompt: str = None) -> Optional[str]
    async def concurrent_chat(self, prompts: List[str], system_prompt: str = None) -> List[Optional[str]]
```

#### 功能说明

- **参数初始化**: 通过 config 参数配置 Agent 行为
- **多轮对话管理**: 提供添加消息和获取对话历史的功能
- **导出聊天记录**: 将对话历史导出为 JSON 文件
- **并发调用接口**: 支持并发处理多个请求

#### 使用示例

```python
from agent import BaseAgent

# 初始化 Agent
agent = BaseAgent({
    "max_concurrent_calls": 10,
    "model": {
        "api_key": "your-api-key",
        "model": "gpt-4o-2024-11-20"
    }
})

# 单轮对话
response = await agent.chat("你好")
print(response)

# 并发对话
responses = await agent.concurrent_chat(["问题1", "问题2", "问题3"])
print(responses)

# 导出聊天记录
agent.export_conversation("conversation.json")
```

### MemoryEnhancer - 内存增强接口

提供上下文管理和自动压缩功能。

#### 接口

```python
class MemoryEnhancer:
    def __init__(self, max_context_length: int = 4096, compression_threshold: float = 0.8)
    def add_context(self, message: Dict[str, Any]) -> None
    def get_context(self) -> List[Dict[str, Any]]
    def set_context(self, context: List[Dict[str, Any]]) -> None
    def clear_context(self) -> None
```

#### 功能说明

- **上下文管理**: 添加、获取和设置上下文消息
- **自动压缩**: 当上下文长度超过阈值时自动压缩，保留重要的系统消息和最近的消息

#### 使用示例

```python
from agent import MemoryEnhancer

# 初始化内存增强器
memory = MemoryEnhancer(max_context_length=2048, compression_threshold=0.75)

# 添加上下文消息
memory.add_context({"role": "user", "content": "你好"})

# 获取当前上下文
context = memory.get_context()

# 清空上下文
memory.clear_context()
```

### Environment - 环境模拟

模拟 Agent 交互的外部环境。

#### 接口

```python
class Environment:
    def __init__(self, tools: List[Dict[str, Any]] = None)
    def add_tool(self, tool: Dict[str, Any]) -> None
    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]
    def get_available_tools(self) -> List[Dict[str, Any]]
    def update_state(self, key: str, value: Any) -> None
    def get_state(self, key: str) -> Any
    def get_full_state(self) -> Dict[str, Any]
```

#### 功能说明

- **工具管理**: 添加和获取可用工具
- **工具调用**: 执行指定工具并返回结果
- **状态管理**: 维护环境状态

#### 使用示例

```python
from agent import Environment

# 定义工具
tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
]

# 初始化环境
env = Environment(tools)

# 添加新工具
env.add_tool({
    "type": "function",
    "name": "get_time",
    "description": "获取当前时间",
    "parameters": {
        "type": "object",
        "properties": {},
    }
})

# 更新环境状态
env.update_state("user_name", "Alice")

# 获取环境状态
name = env.get_state("user_name")
```

### ToolEnhancer - 工具增强接口

处理工具调用功能。

#### 接口

```python
class ToolEnhancer:
    def __init__(self, tools: List[Dict[str, Any]] = None)
    def add_tool(self, tool: Dict[str, Any]) -> None
    def register_function(self, name: str, func: Callable) -> None
    def get_tools(self) -> List[Dict[str, Any]]
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]
    def format_tools_for_api(self) -> List[Dict[str, Any]]
```

#### 功能说明

- **工具管理**: 添加和获取工具定义
- **函数注册**: 注册工具对应的执行函数
- **工具执行**: 执行指定工具并返回结果

#### 使用示例

```python
from agent import ToolEnhancer

def get_weather(city: str):
    # 模拟天气查询
    return f"{city} 今天天气晴朗"

# 初始化工具增强器
tool_enhancer = ToolEnhancer([
    {
        "type": "function",
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
])

# 注册执行函数
tool_enhancer.register_function("get_weather", get_weather)

# 执行工具调用
result = tool_enhancer.execute_tool("get_weather", {"city": "北京"})
print(result)  # {'result': '北京 今天天气晴朗', 'tool_name': 'get_weather'}
```

## 集成使用示例

以下是将所有组件集成使用的示例：

```python
from agent import BaseAgent, MemoryEnhancer, Environment, ToolEnhancer
import asyncio

async def main():
    # 创建内存增强器
    memory = MemoryEnhancer(max_context_length=2048)
    
    # 创建工具增强器
    tool_enhancer = ToolEnhancer([
        {
            "type": "function",
            "name": "get_current_time",
            "description": "获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    ])
    
    # 注册工具执行函数
    def get_current_time():
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    tool_enhancer.register_function("get_current_time", get_current_time)
    
    # 创建环境
    env = Environment()
    for tool in tool_enhancer.get_tools():
        env.add_tool(tool)
    
    # 创建 Agent
    agent = BaseAgent()
    
    # 添加系统消息到内存
    memory.add_context({
        "role": "system",
        "content": "你是一个有用的助手，能够使用工具获取信息。"
    })
    
    # 进行对话
    response = await agent.chat("现在几点了？", system_prompt="请使用工具获取时间")
    print(f"Agent 回复: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 扩展指南

### 添加新工具

1. 定义工具的 JSON Schema
2. 实现相应的执行函数
3. 将工具添加到 ToolEnhancer 并注册执行函数

### 扩展 Agent 功能

1. 继承 BaseAgent 类
2. 添加自定义方法和属性
3. 保持与现有接口兼容

## 注意事项

- 所有异步方法都需要在异步环境中执行
- 妥善管理内存使用，避免上下文过长导致性能问题
- 工具执行函数应处理异常，避免崩溃