# mini-cli 🚀
**从零开始构建你的 AI Agent 开发技能树**  
> 一个循序渐进的学习项目，教你从基础 ChatBot 到完整工具型 Agent 的实现原理

---

## 🎯 项目目标
通过两个实战章节，让你**真正理解并掌握** AI Agent 的核心原理：
1. **第一章**：构建基础命令行 ChatBot - 理解 LLM 对话的核心机制
2. **第二章**：给 ChatBot 加上工具能力 - 掌握 Function Call，让 AI 真正能帮你干活

学完这个项目，你将拥有开发类似 **Claude Code、Cursor、OpenCode** 等复杂 Agent 的基础能力。

---

## ✨ 核心特点
### 🧠 **理论结合实战**
- 每章都有完整可运行的代码，边学边做
- 用最精简的代码（100-150行）展示核心原理，没有复杂框架干扰理解

### 🔧 **真正的工具能力**
- 跨平台支持：Windows/Linux/Mac 都能正常工作
- 原生工具实现：`write_file` 直接用 Python API，100%兼容，没有命令语法差异问题
- 危险命令自动拦截：内置安全机制，防止误操作

### 🛡️ **生产级设计**
- 全局配置文件：`~/.mini-cli/mini-cli.json`，支持多 Provider、多模型
- OpenAI API 兼容：支持官方接口、中转服务、本地开源模型的 OpenAI 兼容接口
- 可扩展架构：新增工具只需 5 分钟，成本极低

---

## 📁 项目结构
```
mini-cli/
├── mini-cli.json.example          # 全局配置模板（复制到 ~/.mini-cli/mini-cli.json 使用）
├── 01-first-chatbot/              # 第一章：基础 ChatBot
│   ├── chatbot.py                 # 核心代码（仅 100 行）
│   ├── requirements.txt           # 依赖
│   ├── README.md                  # 完整教程
│   └── 01-构建你的聊天Agent.md    # 极简版教程
├── 02-agent-with-tools/           # 第二章：工具型 Agent
│   ├── agent_with_tools.py        # 核心代码（支持多轮工具调用）
│   ├── requirements.txt           # 依赖
│   ├── 2-给Agent加上Tools.md      # 完整教程
│   └── hello.py                   # 测试生成的文件
├── .gitignore
└── LICENSE
```

---

## 🚀 快速开始
### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/yourusername/mini-cli.git
cd mini-cli

# 配置全局文件（只需要一次）
mkdir -p ~/.mini-cli
cp mini-cli.json.example ~/.mini-cli/mini-cli.json

# 编辑配置文件，填入你的 API 信息
# Windows: C:\Users\你的用户名\.mini-cli\mini-cli.json
# Linux/macOS: ~/.mini-cli/mini-cli.json
```

### 2. 配置说明
编辑 `~/.mini-cli/mini-cli.json`：
```json
{
  "version": "1.0",
  "defaults": {
    "provider": "remote",      // 默认使用远程接口
    "model": "gpt-3.5-turbo"   // 默认模型
  },
  "providers": {
    "remote": {
      "baseUrl": "https://api.example.com/v1",  // 你的 OpenAPI 兼容接口
      "apiKey": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  // 你的 API 密钥
      "api": "openai-completions",  // 固定为 openai-completions，后续扩展其他类型
      "models": [
        {"id": "gpt-3.5-turbo", "name": "通用远程大模型"}
      ]
    },
    "local": {
      "baseUrl": "http://localhost:11434/v1",  // 本地 Ollama 等开源模型
      "apiKey": "ollama",
      "api": "openai-completions",
      "models": [
        {"id": "qwen:7b", "name": "本地开源模型"}
      ]
    }
  }
}
```

### 3. 运行第一章：基础 ChatBot
```bash
cd 01-first-chatbot
pip install -r requirements.txt
python chatbot.py
```
测试功能：
- 随便问一个问题，看是否正常回复
- 问"我刚才问了什么问题"，测试多轮对话记忆
- 输入 `exit`/`quit`/`q` 正常退出

### 4. 运行第二章：工具型 Agent
```bash
cd ../02-agent-with-tools
pip install -r requirements.txt
python agent_with_tools.py
```
测试工具能力：
- "查看当前目录下的文件"
- "帮我写一个 Python Hello World 程序"
- "运行刚才写的程序"

---

## 📚 学习路线
### 第一章：理解 ChatBot 的核心原理
**核心问题**：ChatBot 为什么能记住对话历史？  
**答案**：维护一个上下文消息列表，每次把历史消息一起传给 LLM

```python
# 关键代码：上下文管理
messages = [
    {"role": "system", "content": "你是一个友好的助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你的？"},
    # 每次对话都会把新的问答加到这里...
]
```

### 第二章：掌握 Agent 的核心能力
**核心问题**：为什么普通 ChatBot 只能"说"，而 Agent 能"做"？  
**答案**：Agent = LLM + 工具调用能力 + 自主决策能力 + 记忆能力

```python
# 工具定义（OpenAI Function Call 标准）
tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行系统命令",
            "parameters": {...}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "跨平台写文件",
            "parameters": {...}
        }
    }
]
```

---

## 🔧 工具能力详解
### 1. `run_command` - 执行系统命令
- **跨平台支持**：自动识别 Windows(PowerShell)/Linux/macOS(Bash)
- **安全机制**：内置危险命令黑名单，自动拦截删除系统文件、格式化磁盘等高危操作
- **无需确认**：普通查询命令直接执行，体验流畅

### 2. `write_file` - 跨平台写文件
- **100%原生实现**：直接用 Python 文件 API，完全不用系统命令
- **无兼容性问题**：Windows/Linux/Mac 行为完全一致，没有 `cat << EOF` vs `Set-Content` 的语法差异
- **自动创建目录**：文件路径的父目录不存在时会自动创建
- **统一 UTF-8 编码**：不会出现乱码问题

### 多轮工具调用
支持复杂任务的自动化执行：
- 写文件 → 运行程序 → 查看结果
- 创建项目 → 安装依赖 → 启动服务
- 等等... Agent 会自动连续调用多个工具完成任务

---

## 🛡️ 安全机制
```
⚠️  【免责声明】本工具仅用于学习用途，执行命令的风险由用户自行承担
✅  安全机制：已自动拦截常见危险命令，普通命令将直接执行，无需确认
```

### 危险命令黑名单包括：
- **Linux/macOS**：`rm -rf /`、`dd if=/dev/zero`、`shutdown`、`reboot`、`mkfs` 等
- **Windows**：`del /f /s /q C:\`、`format C:`、`shutdown /s`、`diskpart /s` 等

检测到危险命令会自动拦截，返回安全提示。

---

## 🚀 后续扩展方向
### 基础工具扩展
1. **`read_file`** - 读取文件内容
2. **`list_dir`** - 列出目录结构
3. **`mkdir`** - 创建目录
4. **`delete_file`** - 删除文件（带安全校验）

### 高级功能
1. **并行工具调用**：多个独立工具同时执行
2. **工具调用缓存**：重复操作缓存结果
3. **权限粒度控制**：支持配置工具白名单
4. **交互式确认**：危险操作二次确认

### 架构演进
1. **单工具 Agent** → **多工具 Agent** → **规划型 Agent** → **多 Agent 协作系统**
2. **本地执行** → **远程 API 调用** → **数据库操作** → **网页自动化**

---

## 🤔 常见问题
### Q: 为什么我的 Agent 说"帮你运行"但没实际执行？
A: 检查系统提示词是否包含"所有需要实际执行的操作，必须调用对应的工具，绝对不能只说不做"的规则。

### Q: Windows 下写文件为什么是空的？
A: 旧版本使用了 `Write-Host` 命令，这个命令的输出不会进入管道。现已改用原生 `write_file` 工具，100%可靠。

### Q: 如何接入其他模型（如 Claude、Gemini）？
A: 配置文件支持扩展，后续会增加 `api` 字段支持 `anthropic-messages`、`gemini` 等类型。

### Q: 这个项目适合什么水平的学习者？
A: 适合有基础 Python 知识，想了解 AI Agent 开发原理的初学者。每章代码都控制在 150 行以内，聚焦核心原理。

---

## 📄 许可证
MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🎯 学习目标达成
完成这个项目后，你将能够：
1. ✅ 理解 LLM 对话的上下文管理机制
2. ✅ 掌握 OpenAI Function Call 的工作流程
3. ✅ 实现跨平台的工具调用能力
4. ✅ 设计安全的 Agent 执行环境
5. ✅ 扩展新的工具能力（5分钟新增一个工具）
6. ✅ 为开发复杂 Agent 打下坚实基础

**现在就开始你的 Agent 开发之旅吧！** 🚀
