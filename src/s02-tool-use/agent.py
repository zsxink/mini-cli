"""
s02: Tool Use

Adding a tool = adding a handler. The loop never changes.
加工具只需要加 handler + schema，循环不变。
"""

from openai import OpenAI
import json
from pathlib import Path
import subprocess
import platform

# ============== 配置 ==============
CONFIG_PATH = Path.home() / ".mini-cli" / "mini-cli.json"
WORKDIR = Path.cwd()  # 工作区目录

def load_config():
    if not CONFIG_PATH.exists():
        raise Exception(f"配置文件不存在，请先创建 {CONFIG_PATH}\n"
                      f"可以复制项目根目录下 config/mini-cli.json.example 进行修改")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    provider = config["providers"][config["defaults"]["provider"]]
    return provider, config["defaults"]["model"]

provider, MODEL = load_config()
client = OpenAI(api_key=provider["apiKey"], base_url=provider["baseUrl"])

# ============== 路径安全 ==============
def safe_path(p: str) -> Path:
    """防止路径逃逸工作区"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                    "limit": {"type": "integer", "description": "Max number of lines to read (optional)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace old_text with new_text in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "old_text": {"type": "string", "description": "Text to find and replace"},
                    "new_text": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    }
]

# ============== Dispatch Map ==============
# 工具名 -> 处理函数
# 加工具 = 加 handler + 加 schema，循环永远不变
def run_bash(command: str) -> str:
    os_type = platform.system()
    shell = ["powershell", "-Command"] if os_type == "Windows" else ["bash", "-c"]
    try:
        result = subprocess.run(shell + [command], capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else f"(error):\n{result.stderr}"
    except Exception as e:
        return f"exception: {str(e)}"

def run_read(path: str, limit: int = None) -> str:
    try:
        text = safe_path(path).read_text(encoding="utf-8")
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit]
        return "\n".join(lines)[:50000]
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def run_write(path: str, content: str) -> str:
    try:
        p = safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        p = safe_path(path)
        text = p.read_text(encoding="utf-8")
        if old_text not in text:
            return f"Text not found in file: {old_text[:50]}..."
        new_content = text.replace(old_text, new_text, 1)
        p.write_text(new_content, encoding="utf-8")
        return f"Edited {path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"

# Dispatch map - 工具名映射到处理函数
TOOL_HANDLERS = {
    "bash":       lambda args: run_bash(args["command"]),
    "read_file":  lambda args: run_read(args.get("path"), args.get("limit")),
    "write_file": lambda args: run_write(args["path"], args["content"]),
    "edit_file":  lambda args: run_edit(args["path"], args["old_text"], args["new_text"]),
}

# ============== Agent Loop ==============
# 循环和 s01 完全一致，只是工具从 1 个变成 4 个
def agent_loop(query: str) -> str:
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

        # 没有工具调用 - 返回响应
        if not response_message.tool_calls:
            return response_message.content

        # 执行工具调用，收集结果
        results = []
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            handler = TOOL_HANDLERS.get(tool_name)
            if handler:
                output = handler(args)
            else:
                output = f"Unknown tool: {tool_name}"

            print(f"\n🔧 {tool_name}\n{output[:500]}\n")
            results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": output
            })

        # 添加助手消息和工具结果，回到循环
        messages.append(response_message)
        messages.append({"role": "user", "content": results})

# ============== Main ==============
if __name__ == "__main__":
    print("=" * 60)
    print("s02: Tool Use")
    print("Adding a tool = adding a handler. The loop never changes.")
    print("=" * 60)
    print("\nTools: bash, read_file, write_file, edit_file")
    print("\nTry these prompts:")
    print("  - Create a file called greet.py with a greet(name) function")
    print("  - Read the file requirements.txt")
    print("  - Edit greet.py to add a docstring")
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
