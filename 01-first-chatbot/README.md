# 第一章：构建你的第一个命令行ChatBot
适合Agents开发入门的最简ChatBot实现方案，基于Python和OpenAI兼容API

---

## 上下文
你是Agents开发入门学习者，本章目标是从零构建一个可运行的命令行ChatBot，理解对话系统的核心原理，为后续开发更复杂的Agents打下基础。
技术选型：
- 编程语言：Python（最适合AI开发的入门语言）
- LLM接口：支持所有OpenAI API格式的接口（官方OpenAI、中转接口、本地开源模型的OpenAI兼容服务）
- 形态：命令行工具（最简实现，快速看到效果）
- 无复杂框架：纯原生实现，不使用LangChain等封装框架，直接理解核心原理

## 实现方案
### 1. 前置准备
#### 依赖说明
仅需要一个轻量依赖：
- `openai`：OpenAI官方SDK，支持所有OpenAI格式的接口调用

#### 项目结构
```
01-first-chatbot/
├── README.md     # 本教程文档
└── chatbot.py    # 核心代码
```

全局配置文件路径：`~/.min-cli/min-cli.json` （Windows下为 `C:\Users\xian\.min-cli\min-cli.json`）

### 2. 快速开始
#### 步骤1：安装依赖
方式一（推荐）：使用requirements.txt安装
```bash
pip install -r requirements.txt
```

方式二：直接安装
```bash
pip install openai==2.30.0
```

#### 步骤2：配置API信息
1. 复制项目中的配置示例文件到用户目录：
   ```bash
   cp ../../config/min-cli.json.example ~/.min-cli/min-cli.json
   ```
   （Windows下手动复制项目根目录下 `config/min-cli.json.example` 到 `C:\Users\xian\.min-cli\min-cli.json`）

2. 修改`~/.min-cli/min-cli.json`配置文件，填入你的API信息：
   ```json
   {
     "version": "1.0",
     "defaults": {
       "provider": "remote",
       "model": "gpt-3.5-turbo"
     },
     "providers": {
       "remote": {
         "baseUrl": "https://api.example.com/v1", // 你的OpenAI兼容接口地址
         "apiKey": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", // 你的API密钥
         "api": "openai-completions", // API格式：目前固定为openai-completions，后续支持其他类型
         "models": [
           {
             "id": "gpt-3.5-turbo",
             "name": "通用远程大模型"
           }
         ]
       },
       "local": {
         "baseUrl": "http://localhost:11434/v1", // 本地Ollama等开源模型接口
         "apiKey": "ollama",
         "api": "openai-completions", // API格式：目前固定为openai-completions，后续支持其他类型
         "models": [
           {
             "id": "qwen:7b",
             "name": "本地开源模型"
           }
         ]
       }
     }
   }
   ```

#### 步骤3：运行ChatBot
```bash
python chatbot.py
```

#### 步骤4：测试功能
- 单轮对话：随便问一个问题，看是否正常回复
- 多轮对话：问“我刚才问了什么问题”，看是否能记住上下文
- 退出功能：输入`exit`/`quit`/`q` 正常退出程序

### 3. 核心原理解析
代码分为5个核心模块，每个模块功能清晰：
1. **配置加载模块**：从`.env`读取配置，避免硬编码敏感信息
2. **上下文管理模块**：用列表存储对话历史，实现多轮对话记忆
3. **API调用模块**：调用LLM接口，传入上下文获取回复
4. **交互处理模块**：处理用户输入、格式化输出、支持退出命令
5. **主循环**：串联所有模块，实现持续对话

完整代码（chatbot.py）：
```python
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
    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}
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
```

### 4. 扩展学习点（可选，完成基础版后可以尝试）
1. 增加上下文长度限制，避免历史消息太长超过token限制
2. 支持清空上下文命令（比如输入/clear清空历史）
3. 支持命令行参数切换不同provider和模型
4. 增加markdown格式回复的渲染
5. 支持更多API接口类型：比如Anthropic Claude、Google Gemini、百度文心一言等非OpenAI格式的接口
6. 接入本地开源模型（比如Ollama提供的OpenAI兼容接口）

## 验证标准
实现完成后，满足以下条件即为成功：
1. 可以正常启动，没有报错
2. 输入问题后可以正常得到LLM的回复
3. 多轮对话可以记住之前的上下文
4. 输入exit可以正常退出程序
