"""
s01: The Agent Loop

One loop & Bash is all you need.
一个工具 + 一个循环 = 一个 Agent。
"""

from openai import OpenAI
import json
from pathlib import Path

# ============== 配置 ==============
CONFIG_PATH = Path.home() / ".mini-cli" / "mini-cli.json"

def load_config():
    """加载全局配置"""
    if not CONFIG_PATH.exists():
        raise Exception(f"配置文件不存在，请先创建 {CONFIG_PATH}\n"
                      f"可以复制项目根目录下 config/mini-cli.json.example 进行修改")
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
            "description": "Execute a bash command and return the output. "
                          "Use this for running shell commands like ls, git, python, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a helpful AI assistant.
When you need to execute a shell command to complete a task, use the bash tool.
Do not ask for confirmation - just execute the command and report the results."""

# ============== 工具执行 ==============
import subprocess
import platform

def run_bash(command: str) -> str:
    """Execute a bash command"""
    os_type = platform.system()
    if os_type == "Windows":
        shell = ["powershell", "-Command"]
    else:
        shell = ["bash", "-c"]

    try:
        result = subprocess.run(
            shell + [command],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout or "(no output)"
        else:
            return f"(error {result.returncode}):\n{result.stderr}"
    except Exception as e:
        return f"exception: {str(e)}"

# ============== Agent Loop ==============
def agent_loop(query: str) -> str:
    """
    The core agent loop.

    1. Send user prompt as the first message.
    2. Send messages + tools to LLM.
    3. If LLM calls a tool, execute it and loop back.
    4. If no tool call, return the response.
    """
    messages = [{"role": "user", "content": query}]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=8000
        )

        response_message = response.choices[0].message

        # No tool call - return the response
        if not response_message.tool_calls:
            return response_message.content

        # Execute tool calls and collect results
        results = []
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "bash":
                args = json.loads(tool_call.function.arguments)
                command = args["command"]
                output = run_bash(command)
                print(f"\n🔧 $ {command}\n{output}\n")
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": output
                })

        # Add assistant message and tool results, loop back
        messages.append(response_message)
        messages.append({"role": "user", "content": results})

# ============== Main ==============
if __name__ == "__main__":
    print("=" * 60)
    print("s01: The Agent Loop")
    print("One loop & Bash is all you need.")
    print("=" * 60)
    print("\nTry these prompts:")
    print("  - Create a file called hello.py that prints 'Hello, World!'")
    print("  - List all files in the current directory")
    print("  - What is the current git branch?")
    print("\nType 'exit' to quit.\n")
    print("-" * 60)

    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        if not query:
            continue
        try:
            response = agent_loop(query)
            print(f"\nAssistant: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")
