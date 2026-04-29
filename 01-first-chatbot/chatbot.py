from openai import OpenAI
import os
import json
from pathlib import Path

# 1. 加载全局配置
CONFIG_PATH = Path.home() / ".min-cli" / "min-cli.json"
DEFAULT_SYSTEM_PROMPT = "你是一个友好的AI助手，回答简洁准确。"

def load_config():
    """加载min-cli配置文件"""
    if not CONFIG_PATH.exists():
        raise Exception(f"配置文件不存在，请先创建 {CONFIG_PATH}\n可以复制 {CONFIG_PATH}.example 进行修改")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 获取默认provider
    default_provider = config["defaults"]["provider"]
    provider_config = config["providers"][default_provider]

    # 获取默认model
    default_model = config["defaults"]["model"]

    return provider_config, default_model

# 初始化配置和客户端
provider_config, MODEL = load_config()
client = OpenAI(
    api_key=provider_config["apiKey"],
    base_url=provider_config["baseUrl"]
)

# 2. 初始化上下文，系统提示词定义ChatBot的行为
messages = [
    {"role": "system", "content": "你是一个友好的助手，回答简洁准确。"}
]

def get_llm_response(user_input: str) -> str:
    """3. 调用LLM接口获取回复"""
    # 把用户输入加入上下文
    messages.append({"role": "user", "content": user_input})

    # 调用API
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7
    )

    # 把LLM回复也加入上下文，实现多轮记忆
    assistant_reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply

def main():
    """4. 命令行交互主逻辑"""
    print("🚀 欢迎使用你的第一个ChatBot！输入 'exit' 或 'quit' 退出")
    print("-" * 50)

    while True:
        # 读取用户输入
        user_input = input("\n你: ").strip()

        # 处理退出命令
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 再见！")
            break

        # 空输入跳过
        if not user_input:
            continue

        try:
            # 获取回复并打印
            reply = get_llm_response(user_input)
            print(f"\n助手: {reply}")
        except Exception as e:
            print(f"\n❌ 出错了: {str(e)}")

if __name__ == "__main__":
    main()
