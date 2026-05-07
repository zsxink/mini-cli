# s01: The Agent Loop (Agent 循环)

`[ s01 ] s02 > s03 > s04 > ...`

> *"One loop & Bash is all you need"* -- 一个工具 + 一个循环 = 一个 Agent。
>
> **Harness 层**: 循环 -- 模型与真实世界的第一道连接。

## 问题

语言模型能推理代码，但碰不到真实世界 -- 不能读文件、跑测试、看报错。
没有循环，每次工具调用你都得手动把结果粘回去。**你自己就是那个循环。**

## 解决方案

```
+--------+      +-------+      +---------+
|  User  | ---> |  LLM  | ---> |  Tool   |
| prompt |      |       |      | execute |
+--------+      +---+---+      +----+----+
                    ^                |
                    |   tool_result  |
                    +----------------+
                    (loop until stop_reason != "tool_use")
```

一个退出条件控制整个流程。循环持续运行，直到模型不再调用工具。

## 工作原理

### 1. 用户 prompt 作为第一条消息

```python
messages.append({"role": "user", "content": query})
```

### 2. 将消息和工具定义一起发给 LLM

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=TOOLS,
    tool_choice="auto",
)
```

### 3. 检查 stop_reason

```python
messages.append({"role": "assistant", "content": response.content})
if not response_message.tool_calls:
    return  # 模型没有调用工具，结束
```

### 4. 执行工具调用，收集结果，回到第 2 步

```python
for tool_call in response_message.tool_calls:
    output = run_bash(tool_call.input["command"])
    results.append({"role": "tool", "content": output, ...})
messages.append({"role": "user", "content": results})
```

### 完整循环（不到 30 行）

```python
def agent_loop(query: str) -> str:
    messages = [{"role": "user", "content": query}]

    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto"
        )
        response_message = response.choices[0].message

        # 没有工具调用 - 返回响应
        if not response_message.tool_calls:
            return response_message.content

        # 执行工具调用，收集结果
        results = []
        for tool_call in response_message.tool_calls:
            output = run_bash(tool_call.function.arguments["command"])
            results.append({"tool_call_id": tool_call.id, "role": "tool", "content": output})

        # 添加助手消息和工具结果，回到循环
        messages.append(response_message)
        messages.append({"role": "user", "content": results})
```

**不到 30 行，这就是整个 Agent。** 后面所有章节都在这个循环上叠加机制 -- 循环本身始终不变。

## 核心代码

```
src/s01-agent-loop/
├── agent.py          # 核心代码（~120 行）
└── requirements.txt  # 依赖
```

## 变更内容

| 组件          | 之前        | 之后                    |
|---------------|-------------|-------------------------|
| Agent loop    | (无)        | `while True` + stop_reason |
| Tools         | (无)        | `bash` (单一工具)       |
| Messages      | (无)        | 累积式消息列表          |
| Control flow  | (无)        | `tool_calls` 为空则结束 |

## 试一试

```bash
cd src/s01-agent-loop
pip install -r requirements.txt
python agent.py
```

试试这些 prompt：

1. `Create a file called hello.py that prints "Hello, World!"`
2. `List all files in the current directory`
3. `What is the current git branch?`
4. `Create a directory called test_output`

## 下一步

[s02: Tool Use](./s02-tool-use.md) -- 加工具只需要加 handler + schema，循环不变。

## 附录：完整源码

```python
"""
s01: The Agent Loop

One loop & Bash is all you need.
"""

from openai import OpenAI
import json
from pathlib import Path
import subprocess
import platform

# ============== 配置 ==============
CONFIG_PATH = Path.home() / ".mini-cli" / "mini-cli.json"

def load_config():
    if not CONFIG_PATH.exists():
        raise Exception(f"配置文件不存在，请先创建 {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    provider = config["providers"][config["defaults"]["provider"]]
    return provider, config["defaults"]["model"]

provider, MODEL = load_config()
client = OpenAI(api_key=provider["apiKey"], base_url=provider["baseUrl"])

# ============== 工具定义 ==============
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash command and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to execute"}
                },
                "required": ["command"]
            }
        }
    }
]

SYSTEM_PROMPT = "You are a helpful AI assistant. Use bash tool when needed."

# ============== 工具执行 ==============
def run_bash(command: str) -> str:
    os_type = platform.system()
    shell = ["powershell", "-Command"] if os_type == "Windows" else ["bash", "-c"]
    try:
        result = subprocess.run(shell + [command], capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else f"(error): {result.stderr}"
    except Exception as e:
        return f"exception: {str(e)}"

# ============== Agent Loop ==============
def agent_loop(query: str) -> str:
    messages = [{"role": "user", "content": query}]
    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto"
        )
        response_message = response.choices[0].message
        if not response_message.tool_calls:
            return response_message.content

        results = []
        for tool_call in response_message.tool_calls:
            output = run_bash(json.loads(tool_call.function.arguments)["command"])
            print(f"\n🔧 $ {json.loads(tool_call.function.arguments)['command']}\n{output}\n")
            results.append({"tool_call_id": tool_call.id, "role": "tool", "content": output})

        messages.append(response_message)
        messages.append({"role": "user", "content": results})
```
