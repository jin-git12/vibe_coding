# LangSmith 配置说明

## 什么是 LangSmith？

LangSmith 是 LangChain 提供的可观测性平台，用于：
- 追踪和监控 agent 的运行
- 调试和优化 agent 性能
- 查看详细的执行日志和调用链

## 当前状态

**默认已禁用 LangSmith 追踪**，因为：
- 需要额外的 API Key
- 会产生网络请求
- 对于开发和调试可能不是必需的

## 如何启用 LangSmith（可选）

如果你想要使用 LangSmith 来追踪 agent 运行：

### 1. 获取 LangSmith API Key

1. 访问 [LangSmith](https://smith.langchain.com/)
2. 注册/登录账号
3. 在设置中获取 API Key

### 2. 配置环境变量

在 `.env` 文件中添加：

```env
# LangSmith 配置
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=your_project_name  # 可选，用于组织追踪数据
```

### 3. 修改代码启用追踪

在 `research_agent.py` 中，将：

```python
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
```

改为：

```python
# 从环境变量读取，如果未设置则默认为 false
# 如果设置了 LANGCHAIN_TRACING_V2=true，则会启用追踪
```

或者直接删除这行代码，然后在 `.env` 文件中设置 `LANGCHAIN_TRACING_V2=true`。

## 错误信息说明

如果你看到以下警告：

```
LangSmithMissingAPIKeyWarning: API key must be provided when using hosted LangSmith API
Failed to multipart ingest runs: Authentication failed
```

**含义**：
- LangChain 尝试将运行数据发送到 LangSmith
- 但没有提供有效的 API Key
- **这不影响程序运行**，只是无法记录追踪数据

**解决方法**：
1. **忽略警告**（推荐）- 如果不需要追踪功能
2. **禁用追踪** - 设置 `LANGCHAIN_TRACING_V2=false`（已在代码中设置）
3. **提供 API Key** - 如果需要追踪功能，设置有效的 API Key

## 验证配置

运行以下命令检查环境变量：

```bash
# Windows PowerShell
$env:LANGCHAIN_TRACING_V2
$env:LANGCHAIN_API_KEY

# 或者在 Python 中
python -c "import os; print('Tracing:', os.getenv('LANGCHAIN_TRACING_V2', 'not set'))"
```

## 总结

- ✅ **默认已禁用** LangSmith 追踪，不会看到警告
- ✅ 如果需要追踪功能，可以启用并配置 API Key
- ✅ 警告不影响程序功能，可以安全忽略

