# Python Agents 架构文档

## 📋 概述

Vibe Coding Python 后端基于 **DeepAgents** 框架和 **LangChain** 生态系统，通过 **JSON-RPC 2.0** 协议与 VS Code 扩展通信。

### 技术栈

- **DeepAgents** (>=0.2.5) - AI Agent 框架，提供规划、文件系统和子 Agent 能力
- **LangChain** (>=1.0.2) - LLM 应用框架
- **LangGraph** - Agent 状态管理和工作流
- **Qwen LLM** - 通义千问大语言模型（通过 DashScope API）
- **Python 3.11+** - 运行时环境
- **uv** - 包管理器

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                  VS Code Extension (TypeScript)              │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Commands │  │ WebView  │  │  UI      │  │ Services │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └───────────────┴────────────┴────────────┬─────────┘
│                                                   │
│                              JSON-RPC via stdin/stdout
│                                                   │
└───────────────────────────────────────────────────┼─────────┘
                                                    │
┌───────────────────────────────────────────────────┼─────────┐
│                   Python Agent Server             │         │
│                                                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  JSON-RPC Server                      │  │
│  │  (stdin/stdout 通信, 方法路由, 错误处理)            │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │                    Agent Server                       │  │
│  │  (初始化, Agent 管理, RPC 方法实现)                 │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │                               │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│  ┌──────▼───────┐  ┌────────▼────────┐  ┌──────▼──────┐  │
│  │ Code         │  │ Chat            │  │ Refactor    │  │
│  │ Generator    │  │ Agent           │  │ Agent       │  │
│  └──────┬───────┘  └────────┬────────┘  └──────┬──────┘  │
│         └───────────────────┼───────────────────┘          │
│                             │                               │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │              DeepAgents Framework                     │  │
│  │                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────────────┐   │  │
│  │  │ TodoListMW      │  │ FilesystemMiddleware    │   │  │
│  │  │ (Planning)      │  │ (File Operations)       │   │  │
│  │  └─────────────────┘  └─────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────────────┐   │  │
│  │  │ SubAgentMW      │  │ Custom Tools            │   │  │
│  │  │ (Subagents)     │  │ (AST Analysis, etc)     │   │  │
│  │  └─────────────────┘  └─────────────────────────┘   │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │                 Qwen LLM (DashScope)                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
python_agents/
├── src/
│   ├── agent_server.py          # 🚀 主入口，RPC 服务器
│   │
│   ├── agents/                  # 🤖 Agent 层
│   │   ├── __init__.py         
│   │   └── code_agents.py       # DeepAgents 创建函数（所有 agent）
│   │
│   ├── tools/                   # 🔧 自定义工具层
│   │   ├── __init__.py
│   │   └── ast_tools.py         # Python AST 分析工具
│   │
│   ├── utils/                   # 🛠️ 工具模块
│   │   ├── __init__.py
│   │   ├── llm_client.py        # LLM 客户端封装
│   │   ├── context_builder.py   # 上下文构建器
│   │   ├── security.py          # 安全检查器
│   │   └── logger.py            # 日志工具
│   │
│   ├── config/                  # ⚙️ 配置层
│   │   ├── __init__.py
│   │   ├── settings.py          # 环境变量和配置
│   │   └── prompts.py           # System Prompt 模板
│   │
│   └── rpc/                     # 🔌 RPC 通信层
│       ├── __init__.py
│       ├── server.py            # JSON-RPC 服务器实现
│       ├── protocol.py          # 协议定义和消息格式
│       └── errors.py            # 错误类型定义
│
├── tests/                       # 🧪 测试
│   ├── README.md
│   ├── test_deepagents_implementation.py
│   └── quick_test.py
│
├── docs/                        # 📚 文档
│   ├── README.md
│   ├── ARCHITECTURE.md          # 本文档
│   ├── DEVELOPMENT.md           # 开发指南
│   └── PACKAGE_MANAGEMENT.md    # 包管理说明
│
├── pyproject.toml               # 项目配置
├── uv.lock                      # 依赖锁文件
├── .env                         # 环境变量（不提交）
└── README.md                    # 项目说明
```

## 🎯 核心组件

### 1. Agent Server (`agent_server.py`)

**职责**：
- 启动 JSON-RPC 服务器
- 初始化所有 Agent
- 实现 RPC 方法
- 管理会话和上下文

**关键方法**：
```python
class AgentServer:
    def __init__(self, workspace_root: str)
    def _initialize_agents(self)      # 初始化所有 Agent
    def health_check(self)             # 健康检查
    def chat(self, params: dict)       # 聊天
    def generate_code(self, params)    # 代码生成
    def explain_code(self, params)     # 代码解释
    def refactor_code(self, params)    # 代码重构
    def shutdown(self)                 # 优雅关闭
```

### 2. DeepAgents (`agents/code_agents.py`)

**职责**：创建各种专门的 AI Agent

**关键函数**：
```python
def create_code_generator_agent(llm, custom_tools) -> CompiledStateGraph
    """创建代码生成 Agent"""

def create_chat_agent(llm, custom_tools) -> CompiledStateGraph
    """创建通用聊天 Agent"""

def create_code_explainer_agent(llm, custom_tools) -> CompiledStateGraph
    """创建代码解释 Agent"""

def create_refactoring_agent(llm, custom_tools) -> CompiledStateGraph
    """创建代码重构 Agent"""

def create_custom_tools(ast_tools) -> List[BaseTool]
    """创建自定义工具列表"""
```

**内置能力**（通过 DeepAgents 中间件）：
- ✅ **TodoListMiddleware** - 任务规划和分解（`write_todos`）
- ✅ **FilesystemMiddleware** - 文件系统操作
  - `ls` - 列出目录
  - `read_file` - 读取文件
  - `write_file` - 写入文件
  - `edit_file` - 编辑文件
  - `grep_search` - 文本搜索（使用 ripgrep）
  - `glob_search` - 文件名搜索
- ✅ **SubAgentMiddleware** - 子 Agent 管理

### 3. 自定义工具 (`tools/`)

#### ASTTools (`ast_tools.py`)
Python 代码静态分析工具：

```python
@tool
def analyze_python_code(code: str) -> str:
    """分析 Python 代码结构（函数、类、导入等）"""
    # 使用 Python AST 解析代码
    # 返回结构化信息

@tool
def analyze_code_complexity(code: str) -> str:
    """分析代码复杂度（圈复杂度、认知复杂度）"""
    # 计算复杂度指标
    # 返回复杂度报告
```

**注意**：不再需要 `FileTools` 和 `SearchTools`，DeepAgents 已内置。

### 4. Utils 层

#### LLMClient (`utils/llm_client.py`)
统一的 LLM 客户端接口：

```python
class LLMClient:
    """支持 DashScope (Qwen) 和 OpenAI"""
    
    def create_chat_llm(config: LLMConfig) -> BaseChatModel
    def create_streaming_llm(config: LLMConfig) -> BaseChatModel
```

#### ContextBuilder (`utils/context_builder.py`)
上下文信息收集：

```python
class ContextBuilder:
    def build_code_context(file_path, selected_code, ...)
    def get_related_files(current_file, ...)
    def format_context_for_llm(context_info)
```

#### SecurityChecker (`utils/security.py`)
安全验证：

```python
class SecurityChecker:
    def is_path_safe(path: str) -> bool
    def is_command_allowed(command: str) -> bool
    def sanitize_input(text: str) -> str
```

### 5. Config 层

#### Settings (`config/settings.py`)
环境配置管理：

```python
class Settings:
    # LLM 配置
    DASHSCOPE_API_KEY: str
    QWEN_MODEL: str = "qwen-turbo"
    LLM_TEMPERATURE: float = 0.7
    
    # 工作区配置
    WORKSPACE_ROOT: str
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
```

#### Prompts (`config/prompts.py`)
System Prompt 模板：

```python
CODE_GENERATOR_PROMPT = """You are an expert code generator..."""
CHAT_AGENT_PROMPT = """You are a helpful AI coding assistant..."""
CODE_EXPLAINER_PROMPT = """You are an expert at explaining code..."""
REFACTORING_PROMPT = """You are a code refactoring expert..."""
```

### 6. RPC 层

#### JSONRPCServer (`rpc/server.py`)
JSON-RPC 2.0 协议实现：

```python
class JSONRPCServer:
    def register_method(self, name: str, handler: Callable)
    def handle_request(self, request: dict) -> dict
    def send_notification(self, method: str, params: dict)
    def run(self)  # 主循环（读取 stdin，写入 stdout）
```

## 📡 通信协议

### JSON-RPC 2.0

**请求格式**：
```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": { /* 参数 */ },
  "id": 1
}
```

**成功响应**：
```json
{
  "jsonrpc": "2.0",
  "result": { /* 结果 */ },
  "id": 1
}
```

**错误响应**：
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": { /* 额外信息 */ }
  },
  "id": 1
}
```

### 支持的方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `health_check` | 健康检查 | 无 |
| `chat` | AI 聊天 | `message`, `conversation_id`, `context`, `stream` |
| `generate_code` | 生成代码 | `prompt`, `language`, `context` |
| `explain_code` | 解释代码 | `code`, `language`, `context` |
| `refactor_code` | 重构代码 | `code`, `language`, `instructions`, `context` |
| `review_code` | 审查代码 | `code`, `language`, `context` |
| `search_code` | 搜索代码 | `query`, `file_patterns` |
| `shutdown` | 关闭服务器 | 无 |

## 🔒 安全机制

### 文件系统安全

1. **路径验证**：所有文件操作限制在 `WORKSPACE_ROOT` 内
2. **黑名单**：禁止访问敏感文件（`.env`, `.ssh/`, `.git/config`）
3. **大小限制**：单个文件最大 10MB
4. **符号链接**：解析并验证符号链接目标

### 命令执行安全

1. **白名单**：只允许特定命令（`git`, `python`, `npm`）
2. **参数验证**：检查命令参数合法性
3. **无交互**：所有命令以非交互模式运行
4. **超时**：30 秒执行超时

### 资源限制

1. **内存**：最大 500MB（可配置）
2. **CPU**：监控 CPU 使用率
3. **并发**：限制并发请求数
4. **速率限制**：防止 API 滥用

## 🎨 Agent 创建流程

```python
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

# 1. 创建 LLM
llm = ChatOpenAI(
    model="qwen-turbo",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.7,
)

# 2. 准备自定义工具（可选）
from tools import ASTTools
from agents import create_custom_tools

ast_tools = ASTTools()
custom_tools = create_custom_tools(ast_tools)

# 3. 创建 Agent（自动包含 DeepAgents 中间件）
agent = create_deep_agent(
    model=llm,
    system_prompt="You are an expert code assistant...",
    tools=custom_tools,  # 自定义工具
    # DeepAgents 自动添加：
    # - TodoListMiddleware (planning)
    # - FilesystemMiddleware (file ops)
    # - SubAgentMiddleware (subagents)
)

# 4. 调用 Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "Generate a Python function"}]
})

# 5. 提取结果
response = result["messages"][-1].content
```

## 📊 数据流

### 1. 用户请求流程

```
用户操作 (VS Code)
    ↓
TypeScript Extension
    ↓ (构建 JSON-RPC 请求)
Python Agent Server
    ↓ (解析请求)
Agent Server
    ↓ (调用相应 Agent)
DeepAgent
    ↓ (规划、工具调用)
LLM (Qwen)
    ↓ (生成响应)
DeepAgent
    ↓ (后处理)
Agent Server
    ↓ (构建 JSON-RPC 响应)
TypeScript Extension
    ↓ (更新 UI)
用户界面 (WebView)
```

### 2. Agent 执行流程

```
Agent.invoke({"messages": [...]})
    ↓
LangGraph StateGraph
    ↓
DeepAgents Middleware
    ├─ TodoListMiddleware → 分解任务
    ├─ FilesystemMiddleware → 文件操作
    └─ SubAgentMiddleware → 子任务
    ↓
Custom Tools (如需要)
    └─ AST Analysis
    ↓
LLM Generate Response
    ↓
Return {"messages": [...]}
```

## 🔄 会话管理

会话由 TypeScript 扩展管理，Python 后端是无状态的：

1. 每个请求携带 `conversation_id`
2. TypeScript 维护会话历史
3. Python 只处理单次请求
4. 需要历史时通过 `context` 参数传递

## 🚀 启动流程

1. VS Code 扩展激活
2. TypeScript 启动 Python 子进程
3. Python 初始化 Agent Server
4. 加载配置和环境变量
5. 创建 LLM 客户端
6. 初始化所有 Agent
7. 启动 JSON-RPC 服务器
8. 发送 ready 通知
9. 进入主循环（监听 stdin）

## 📚 技术细节

### DeepAgents vs 自定义实现

| 功能 | DeepAgents | 自定义实现 |
|------|-----------|----------|
| 文件操作 | ✅ 内置（FilesystemMW） | ❌ 需手动实现 |
| 任务规划 | ✅ 内置（TodoListMW） | ❌ 需手动实现 |
| 子 Agent | ✅ 内置（SubAgentMW） | ❌ 需手动实现 |
| LangGraph 集成 | ✅ 自动 | ❌ 需手动配置 |
| 工具调用 | ✅ 优化 | ⚠️ 基本支持 |

### 为什么使用 DeepAgents？

1. **成熟的框架**：经过充分测试和优化
2. **内置中间件**：减少重复代码
3. **标准化**：遵循 LangChain 和 LangGraph 最佳实践
4. **可扩展**：易于添加自定义工具和子 Agent
5. **维护性**：由官方团队维护和更新

## 🔍 调试和监控

### 日志级别

- `DEBUG` - 详细的调试信息
- `INFO` - 一般信息（默认）
- `WARNING` - 警告信息
- `ERROR` - 错误信息

### 日志输出

所有日志输出到 `stderr`，不影响 JSON-RPC 通信（使用 `stdin/stdout`）。

### 性能监控

使用 `psutil` 监控：
- CPU 使用率
- 内存使用量
- 进程状态

## 📖 参考资料

- [DeepAgents GitHub](https://github.com/aiwaves-cn/deepagents)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [DashScope API 文档](https://help.aliyun.com/dashscope/)

---

**版本**: 1.0.0  
**最后更新**: 2025-11-09  
**状态**: ✅ 生产就绪







