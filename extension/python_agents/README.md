# Vibe Coding Python Agents

Python 后端 Agent 服务，基于 DeepAgents 框架，通过 JSON-RPC 与 VS Code 扩展通信。

## 📁 项目结构

```
python_agents/
├── src/                    # 源代码
│   ├── agent_server.py    # JSON-RPC 服务器入口
│   ├── agents/            # AI Agent 实现（基于 DeepAgents）
│   ├── tools/             # 自定义工具（AST 分析等）
│   ├── config/            # 配置和提示模板
│   ├── utils/             # 工具函数
│   └── rpc/               # RPC 协议实现
├── docs/                   # 📚 文档
├── tests/                  # 🧪 测试
├── .venv/                  # 虚拟环境
├── pyproject.toml         # 项目配置
└── uv.lock                # 依赖锁文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd extension/python_agents
uv sync
```

### 2. 配置环境

#### 方式 A：开发模式（推荐用于调试）🔧

在 VS Code 中按 **F5** 启动调试，会自动启用开发模式：
- ✅ 自动使用测试 API Key
- ✅ 启用 DEBUG 日志
- ✅ 无需手动配置

或手动设置：

```bash
# Windows
$env:DEV_MODE="true"

# Linux/Mac
export DEV_MODE=true
```

⚠️ **开发模式仅用于本地调试，请勿在生产环境使用！**

#### 方式 B：生产模式（用户环境）

创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=your_api_key_here
QWEN_MODEL=qwen-turbo
WORKSPACE_ROOT=.
LOG_LEVEL=INFO
```

### 3. 运行测试

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 运行实现测试
python tests\test_deepagents_implementation.py

# 交互式测试
python tests\quick_test.py
```

### 4. 运行服务器

```bash
python src\agent_server.py
```

## 📚 文档

详细文档请查看 [`docs/`](docs/) 目录：

- **[DeepAgents 使用指南](docs/README_DEEPAGENTS.md)** - DeepAgents 框架完整说明
- **[实现文档](docs/README_IMPLEMENTATION.md)** - 架构和 API 参考
- **[包管理说明](docs/PACKAGE_MANAGEMENT.md)** - uv 和依赖管理
- **[迁移指南](docs/DEEPAGENTS_MIGRATION.md)** - 从旧实现迁移

## 🧪 测试

测试文档请查看 [`tests/`](tests/) 目录：

- **[测试说明](tests/README.md)** - 测试套件使用指南
- `test_deepagents_implementation.py` - 实现验证测试
- `quick_test.py` - 交互式功能测试

## 🔧 开发

### 技术栈

- **DeepAgents** (>=0.2.5) - 深度 Agent 框架
- **LangChain** (>=1.0.2) - LLM 应用框架
- **Qwen LLM** - 通义千问大语言模型
- **uv** - Python 包管理器

### 通信协议

使用 **JSON-RPC 2.0**，通过 stdin/stdout 与 VS Code 扩展通信。

支持的方法：
- `health_check` - 健康检查
- `chat` - AI 聊天
- `generate_code` - 代码生成
- `explain_code` - 代码解释
- `refactor_code` - 代码重构
- `review_code` - 代码审查
- `search_code` - 代码搜索
- `shutdown` - 优雅关闭

### 添加新 Agent

1. 在 `src/agents/code_agents.py` 中创建新的 Agent 函数
2. 使用 `create_deep_agent` 创建 Agent
3. 在 `src/agent_server.py` 中注册 RPC 方法
4. 添加测试到 `tests/`

## 📊 架构

```
VS Code Extension (TypeScript)
        ↕ (JSON-RPC via stdin/stdout)
Agent Server (Python)
        ↓
DeepAgents Framework
        ├─ TodoListMiddleware (planning)
        ├─ FilesystemMiddleware (file ops)
        └─ Custom Tools (AST analysis)
        ↓
Qwen LLM (via DashScope API)
```

## 🤝 贡献

1. 添加新功能前先查看[实现文档](docs/README_IMPLEMENTATION.md)
2. 确保所有测试通过
3. 更新相关文档

