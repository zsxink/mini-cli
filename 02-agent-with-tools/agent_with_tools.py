from openai import OpenAI
import json
from pathlib import Path
import subprocess
import sys
import platform

# 加载配置（和第一章完全一致）
CONFIG_PATH = Path.home() / ".mini-cli" / "mini-cli.json"
os_type = platform.system()
SYSTEM_PROMPT = f"""你是一个能干的AI助手，可以调用工具帮用户完成实际任务。
当前运行的系统是：{os_type}
重要规则：
1. 优先使用专用工具：
   ✅ 写文件必须用`write_file`工具，**绝对不要用系统命令（Set-Content、cat等）写文件**，这个工具是跨平台原生实现，Windows/Linux/Mac都能正常工作
   ✅ 执行系统命令、运行程序用`run_command`工具
2. 所有需要实际执行的操作，必须调用对应的工具，**绝对不能只说不做**：
   ✅ 提到"帮你运行"、"执行一下"、"跑一下程序"的时候，必须调用run_command工具执行对应的命令
   ✅ 提到"帮你写文件"、"保存文件"的时候，必须调用write_file工具
   ✅ 可以连续调用多个工具完成复杂任务，比如先写文件→再运行程序→再查看结果
3. 只要能通过调用工具完成的操作，直接调用工具执行，不需要询问用户，不要只输出文字告诉用户怎么做
4. 当需要调用工具时，严格按照工具调用格式返回，不要直接回答
5. 不要生成危险命令（删除系统文件、格式化磁盘、修改系统配置等）。"""

# 危险命令黑名单（自动拦截）
DANGEROUS_COMMANDS = [
    # Linux/macOS 危险命令
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "shutdown", "reboot", "init 0", "init 6",
    "chmod -R 777 /", "chown -R /", "mv /home /dev/null", "rm -rf ~", "rm -rf ~/*",
    "dd if=/dev/zero of=", ":(){ :|:& };:", "fork bomb",
    # Windows 危险命令
    "del /f /s /q C:\\", "rd /s /q C:\\", "format C:", "diskpart /s", "shutdown /s",
    "shutdown /r", "Remove-Item -Recurse -Force C:\\", "Format-Volume", "rmdir /s /q C:\\"
]

def load_config():
    """加载全局配置"""
    if not CONFIG_PATH.exists():
        raise Exception(f"配置文件不存在，请先创建 {CONFIG_PATH}\n可以复制项目根目录下 config/mini-cli.json.example 进行修改")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 获取默认provider
    default_provider = config["defaults"]["provider"]
    provider_config = config["providers"][default_provider]

    # 获取默认model
    default_model = config["defaults"]["model"]

    return provider_config, default_model

provider, MODEL = load_config()
client = OpenAI(api_key=provider["apiKey"], base_url=provider["baseUrl"])

# 定义可用工具：执行系统命令、写文件
tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行系统命令（Bash/Powershell），返回命令执行结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的系统命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "跨平台写文件工具，支持Windows/Linux/Mac，优先用这个工具写文件，不要用系统命令写文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要写入的文件路径（绝对路径或相对路径）"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容，支持任意文本格式"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    }
]

def is_dangerous_command(command: str) -> bool:
    """检查是否是危险命令"""
    command_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return True
    return False

def run_command(command: str) -> str:
    """执行系统命令，跨平台支持Windows(Powershell)/macOS/Linux(Bash)"""
    # 先拦截危险命令
    if is_dangerous_command(command):
        return f"❌ 已拦截危险命令：`{command}`\n为了系统安全，此类高危操作禁止自动执行，请手动确认后操作。"

    # 确定系统类型，选择对应的shell
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
            return f"执行成功：\n{result.stdout}"
        else:
            return f"执行失败，错误信息：\n{result.stderr}"
    except Exception as e:
        return f"执行出错：{str(e)}"

def write_file(file_path: str, content: str) -> str:
    """跨平台写文件工具，支持Windows/Linux/Mac，直接用Python原生API，不需要系统命令
    参数：
        file_path: 要写入的文件路径（绝对路径或相对路径）
        content: 文件内容
    返回：执行结果
    """
    try:
        # 自动创建父目录
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        # 写入文件，utf-8编码
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 写文件成功：{file_path}\n文件大小：{len(content)} 字节"
    except Exception as e:
        return f"❌ 写文件失败：{str(e)}"

# 上下文记忆
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def chat(user_input):
    messages.append({"role": "user", "content": user_input})

    # 支持多轮工具调用，直到LLM不需要调用工具为止
    while True:
        # 调用LLM
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7
        )

        response_message = response.choices[0].message

        # 如果没有工具调用，直接返回最终回答
        if not response_message.tool_calls:
            return response_message.content

        # 处理所有工具调用
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "run_command":
                # 解析命令参数
                args = json.loads(tool_call.function.arguments)
                command = args["command"]

                # 执行命令（危险命令会被自动拦截）
                print(f"\n🔧 正在执行命令：`{command}`")
                result = run_command(command)
                print(f"\n执行结果：\n{result}")

                # 把工具执行结果加入上下文
                messages.append(response_message)
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "run_command",
                    "content": result
                })
            elif tool_call.function.name == "write_file":
                # 解析写文件参数
                args = json.loads(tool_call.function.arguments)
                file_path = args["file_path"]
                content = args["content"]

                # 执行写文件
                print(f"\n📝 正在写文件：`{file_path}`")
                result = write_file(file_path, content)
                print(f"\n执行结果：\n{result}")

                # 把工具执行结果加入上下文
                messages.append(response_message)
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "write_file",
                    "content": result
                })

if __name__ == "__main__":
    print("🚀 工具型Agent已启动，输入exit退出")
    print("⚠️  【免责声明】本工具仅用于学习用途，执行命令的风险由用户自行承担，开发者不承担任何责任。")
    print("✅ 安全机制：已自动拦截常见危险命令，普通命令将直接执行，无需确认。")
    print("可以让我帮你执行系统命令，比如：查看当前目录文件、查看系统版本、列出Python版本等")
    print("-" * 70)

    while True:
        user_input = input("\n你: ").strip()

        # 处理退出命令
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 再见！")
            break

        # 空输入跳过
        if not user_input:
            continue

        try:
            reply = chat(user_input)
            print(f"\n助手: {reply}")
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
