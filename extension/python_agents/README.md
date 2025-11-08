# Vibe Coding Python Agents

Python 后端 Agent 服务，通过 JSON-RPC 与 VS Code 扩展通信。

## 架构

- **JSON-RPC 服务器**: 通过 stdin/stdout 与 TypeScript 前端通信
- **Agent 层**: 基于 deepagents 的各种 AI Agent
- **工具层**: 文件操作、代码分析等工具

## 开发

### 安装依赖

```bash
uv sync
```

### 运行服务器

```bash
# 直接运行
uv run python src/agent_server.py

# 或使用环境变量
WORKSPACE_ROOT=/path/to/workspace LOG_LEVEL=DEBUG uv run python src/agent_server.py
```

### 测试

```bash
uv run pytest
```

## 通信协议

使用 JSON-RPC 2.0，通过 stdin/stdout 通信。

### 请求示例

```json
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "Hello AI",
    "stream": true
  },
  "id": 1
}
```

### 响应示例

```json
{
  "jsonrpc": "2.0",
  "result": {
    "conversation_id": "default",
    "full_response": "Hello! How can I help you?",
    "suggestions": []
  },
  "id": 1
}
```

## 支持的方法

- `health_check`: 健康检查
- `chat`: AI 聊天
- `generate_code`: 生成代码
- `explain_code`: 解释代码
- `refactor_code`: 重构代码
- `review_code`: 审查代码
- `search_code`: 搜索代码
- `shutdown`: 优雅关闭

