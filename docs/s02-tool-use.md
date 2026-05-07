# s02: Tool Use (工具使用)

`s01 > [ s02 ] s03 > s04 > ...`

> *"Adding a tool = adding a handler. The loop never changes."* -- 循环不用动，新工具注册进 dispatch map 就行。
>
> **Harness 层**: 工具分发 -- 扩展模型能触达的边界。

## 问题

只有 `bash` 时，所有操作都走 shell。`cat` 截断不可预测，`sed` 遇到特殊字符就崩，每次 bash 调用都是不受约束的安全面。

**关键洞察**: 加工具不需要改循环。

## 解决方案

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

The dispatch map is a dict: {tool_name: handler_function}.
One lookup replaces any if/elif chain.
```

## 工作原理

### 1. 每个工具有一个处理函数

```python
def safe_path(p: str) -> Path:
    """防止路径逃逸工作区"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text()
    lines = text.splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)[:50000]
```

### 2. Dispatch map 将工具名映射到处理函数

```python
TOOL_HANDLERS = {
    "bash":       lambda args: run_bash(args["command"]),
    "read_file":  lambda args: run_read(args.get("path"), args.get("limit")),
    "write_file": lambda args: run_write(args["path"], args["content"]),
    "edit_file":  lambda args: run_edit(args["path"], args["old_text"], args["new_text"]),
}
```

### 3. 循环中按名称查找处理函数

```python
for tool_call in response_message.tool_calls:
    handler = TOOL_HANDLERS.get(tool_call.function.name)
    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
    results.append({"tool_call_id": tool_call.id, "role": "tool", "content": output})
```

**加工具 = 加 handler + 加 schema。循环永远不变。**

## 相对 s01 的变更

| 组件           | 之前 (s01)         | 之后 (s02)                     |
|----------------|--------------------|--------------------------------|
| Tools          | 1 (仅 bash)        | 4 (bash, read, write, edit)   |
| Dispatch       | 硬编码 bash 调用   | `TOOL_HANDLERS` 字典           |
| 路径安全       | 无                 | `safe_path()` 沙箱             |
| Agent loop     | 不变               | 不变                           |

## 核心代码

```
src/s02-tool-use/
├── agent.py          # 核心代码（~200 行）
└── requirements.txt # 依赖
```

## 试一试

```bash
cd src/s02-tool-use
pip install -r requirements.txt
python agent.py
```

试试这些 prompt：

1. `Read the file requirements.txt`
2. `Create a file called greet.py with a greet(name) function`
3. `Edit greet.py to add a docstring to the function`
4. `Read greet.py to verify the edit worked`

## 下一步

[s03: Todo Write](./s03-todo-write.md) -- 任务规划和待办事项系统。

## 附录：Dispatch Map 详解

### 为什么用 Dispatch Map？

传统写法（不好）:
```python
if tool_name == "bash":
    result = run_bash(args)
elif tool_name == "read_file":
    result = run_read(args)
elif tool_name == "write_file":
    result = run_write(args)
# ... 每次加工具都要改这里
```

Dispatch Map 写法（好）:
```python
TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    # 加新工具只需要在这里加一行
}

# 调用永远不变
result = TOOL_HANDLERS[tool_name](args)
```

### 路径沙箱

```python
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

这确保 Agent 只能操作工作区内的文件，防止读写 `/etc/passwd` 或 `C:\Windows` 等敏感路径。
