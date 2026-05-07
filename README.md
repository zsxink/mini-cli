# mini-cli 🚀

**从零开始构建你的 AI Agent 开发技能树**

> 一个循序渐进的学习项目，基于 [Ant，每月更新一章节](/dist)
>
> 学完这个项目，你将拥有开发类似 **Claude Code、Cursor、OpenCode** 等复杂 Agent 的基础能力

---

## 📚 课程目录

| 章节 | 主题 | 状态 |
|------|------|------|
| [s01](./docs/s01-agent-loop.md) | The Agent Loop - Agent 循环 | ✅ 完成 |
| [s02](./docs/s02-tool-use.md) | Tool Use - 工具使用 | ✅ 完成 |
| s03 | Todo Write - 任务规划 | 🚧 进行中 |
| s04-s12 | 高级主题（子 Agent、技能加载、上下文压缩等） | 📋 待开始 |

---

## 🎯 核心设计原则

### 1. 循环不变 (The Loop Never Changes)
```
s01: One loop & Bash is all you need.
s02: Adding a tool = adding a handler. The loop never changes.
```
所有 12 个章节都基于同一个循环，只是逐步叠加机制。

### 2. 极简代码
每章代码控制在 **100-200 行**，没有复杂框架，直击核心原理。

### 3. 渐进式学习
```
s01 (基础) → s02 (工具) → s03 (规划) → ... → s12 (多 Agent 协作)
```

---

## 📁 项目结构

```
mini-cli/
├── docs/                       # 教程文档
│   ├── s01-agent-loop.md       # 第一章：Agent 循环
│   ├── s02-tool-use.md         # 第二章：工具使用
│   └── ...                     # 更多章节...
├── src/                        # 源码
│   ├── s01-agent-loop/          # 第一章源码
│   │   ├── agent.py
│   │   └── requirements.txt
│   ├── s02-tool-use/           # 第二章源码
│   │   ├── agent.py
│   │   └── requirements.txt
│   └── ...                     # 更多章节...
├── config/                     # 配置文件模板
│   └── mini-cli.json.example
├── dist/                       # 参考资料（原始课程）
├── README.md
└── .gitignore
```

---

## 🚀 快速开始

### 1. 配置全局文件

```bash
# 克隆项目
git clone https://github.com/zsxink/mini-cli.git
cd mini-cli

# 配置全局文件（只需要一次）
mkdir -p ~/.mini-cli
cp config/mini-cli.json.example ~/.mini-cli/mini-cli.json

# 编辑配置文件，填入你的 API 信息
# Windows: C:\Users\<用户名>\.mini-cli\mini-cli.json
# Linux/macOS: ~/.mini-cli/mini-cli.json
```

### 2. 运行第一章：Agent 循环

```bash
cd src/s01-agent-loop
pip install -r requirements.txt
python agent.py
```

### 3. 运行第二章：工具使用

```bash
cd ../s02-tool-use
pip install -r requirements.txt
python agent.py
```

---

## 📖 教程索引

### s01: The Agent Loop (Agent 循环)

**核心问题**: 语言模型能推理代码，但碰不到真实世界。没有循环，每次工具调用你都得手动把结果粘回去。

**解决方案**: 一个 `while True` 循环 + stop_reason 退出条件

```
+--------+      +-------+      +---------+
|  User  | ---> |  LLM  | ---> |  Tool   |
| prompt |      |       |      | execute |
+--------+      +---+---+      +----+----+
                    ^                |
                    | tool_result    |
                    +----------------+
```

**关键代码**:
```python
while True:
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    if not response.message.tool_calls:  # 没有工具调用，结束
        return response.message.content
    # 执行工具，收集结果，回到循环
```

---

### s02: Tool Use (工具使用)

**核心问题**: 只有 bash 时，所有操作都走 shell。sed 遇到特殊字符就崩，路径安全无法控制。

**解决方案**: Dispatch map 管理多个工具，循环不变

```
+--------+      +-------+      +------------------+
|  User  | ---> |  LLM  | ---> | Tool Dispatch    |
| prompt |      |       |      | {                |
+--------+      +---+---+      |   bash: run_bash |
                    ^           |   read: run_read |
                    |           |   write: run_wr |
                    +-----------+   edit: run_edit |
                    tool_result | }                |
                                +------------------+
```

**关键洞察**: 加工具 = 加 handler + 加 schema，循环永远不变

```python
TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
}
```

---

## 🔧 配置说明

编辑 `~/.mini-cli/mini-cli.json`:

```json
{
  "version": "1.0",
  "defaults": {
    "provider": "remote",
    "model": "gpt-3.5-turbo"
  },
  "providers": {
    "remote": {
      "baseUrl": "https://api.example.com/v1",
      "apiKey": "sk-xxxxxxxx",
      "api": "openai-completions",
      "models": [
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5"}
      ]
    }
  }
}
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License
