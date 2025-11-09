# Vibe Coding - 架构文档

## 概述

Vibe Coding 是一个基于 **DeepAgents** 的 VSCode AI 编程助手扩展，采用**统一 Agent 架构**，通过单一聊天界面完成所有操作。

## 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                  VS Code Extension (TypeScript)          │
│  - UI (ChatPanel, TreeViews, StatusBar)                │
│  - Commands & Event Handlers                            │
└─────────────────┬───────────────────────────────────────┘
                  │ JSON-RPC over stdio
┌─────────────────▼───────────────────────────────────────┐
│              Python Agent Server                         │
│  - RPC Server (agent_server.py)                         │
│  - Unified Agent (统一入口)                              │
│  - 3 Specialized Subagents                              │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
  code-gen   code-exp    refactor
  Subagent   Subagent    Subagent
      │           │           │
      └───────────┴───────────┘
                  │
      ┌───────────▼───────────┐
      │   LLM API (Qwen/etc)  │
      └───────────────────────┘
```

## 统一 Agent 架构

### 设计理念

**类似 Cursor 的体验**: 所有操作通过一个聊天框完成，Agent 自动判断并委派给专业 subagent。

**核心优势**:
- 🎯 **单一入口**: 用户只需在聊天框输入需求
- 🤖 **智能分派**: 主 agent 自动判断任务类型并委派
- 💾 **统一记忆**: 所有 subagents 共享会话历史
- 🔄 **无缝切换**: 在同一会话中可以自由切换任务类型
- 🚀 **易扩展**: 添加新功能只需增加 subagent

### 主 Agent (Unified Agent)

**文件**: `src/agents/unified_agent.py`

```python
def create_unified_chat_agent(llm, custom_tools, backend=None):
    """创建统一的聊天 agent，包含 3 个专业 subagents"""
    
    # 主 agent 的系统提示
    system_prompt = """You are an expert AI coding assistant.
    
    For specialized tasks, delegate to your subagents:
    - code-generator: Generate new code
    - code-explainer: Explain existing code  
    - refactoring: Improve code quality
    
    Use the 'task' tool to delegate when appropriate."""
    
    # 定义 3 个 subagents
    subagents = [
        {
            "name": "code-generator",
            "agent": create_deep_agent(...),
            "description": "Generate high-quality code"
        },
        {
            "name": "code-explainer", 
            "agent": create_deep_agent(...),
            "description": "Explain code clearly"
        },
        {
            "name": "refactoring",
            "agent": create_deep_agent(...),
            "description": "Refactor and improve code"
        }
    ]
    
    # 创建主 agent
    return create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=custom_tools,
        subagents=subagents,
        backend=backend  # 共享 checkpointer
    )
```

### 三个专业 Subagents

#### 1. Code Generator (代码生成)
- **职责**: 生成新代码
- **特点**:
  - 生产就绪的代码质量
  - 包含类型提示和文档
  - 完善的错误处理
  - 考虑性能和安全性

#### 2. Code Explainer (代码解释)
- **职责**: 解释现有代码
- **特点**:
  - 高层次概览
  - 逻辑流程分析
  - 复杂度讨论
  - 最佳实践建议

#### 3. Refactoring (代码重构)
- **职责**: 改进代码质量
- **特点**:
  - 应用设计模式
  - 性能优化
  - 可读性提升
  - 保持功能完整

## 技术栈

### 前端 (TypeScript)
- **VS Code Extension API**: 扩展开发
- **WebView**: 聊天 UI
- **JSON-RPC Client**: 与 Python 通信

### 后端 (Python)
- **DeepAgents**: Agent 框架（基于 LangGraph）
- **LangGraph**: 底层状态图编排
- **LangChain**: LLM 集成和工具
- **MemorySaver**: 对话历史管理

## 核心组件

### 1. RPC Server (`agent_server.py`)

```python
class AgentServer:
    def __init__(self, workspace_root: str):
        self.rpc_server = JSONRPCServer()
        self.checkpointer = MemorySaver()  # 会话历史
        self.unified_agent = create_unified_chat_agent(...)
        
    def chat(self, params: dict) -> dict:
        """统一的聊天接口"""
        result = self.unified_agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            {"configurable": {"thread_id": conversation_id}}
        )
        return result
```

**RPC 方法**:
- `chat`: 聊天（统一入口，委派给 subagents）
- `generate_code`: 代码生成（委派给 code-generator）
- `explain_code`: 代码解释（委派给 code-explainer）
- `refactor_code`: 代码重构（委派给 refactoring）

> 注：`generate_code`、`explain_code`、`refactor_code` 实际上都是调用 `unified_agent`，
> 保留这些方法只是为了兼容前端的不同调用方式。

### 2. 会话历史管理

使用 LangGraph 的 **Checkpointer** 机制：

```python
from langgraph.checkpoint.memory import MemorySaver

# 创建 checkpointer
checkpointer = MemorySaver()

# 创建 agent 时传入
unified_agent = create_unified_chat_agent(
    llm, 
    tools, 
    backend=checkpointer
)

# 调用时指定 thread_id
result = unified_agent.invoke(
    {"messages": [...]},
    {"configurable": {"thread_id": "user-session-123"}}
)
```

**特性**:
- ✅ 每个会话独立隔离
- ✅ 支持多轮对话
- ✅ Subagents 共享会话历史
- ✅ 内存高效（使用 MemorySaver）

### 3. 工具系统

#### DeepAgents 内置工具
通过 `FilesystemMiddleware` 自动提供：
- `ls`: 列出目录
- `read_file`: 读取文件（支持行范围）
- `write_file`: 写入文件
- `edit_file`: 编辑文件（搜索替换）
- `grep_search`: 正则搜索
- `glob_search`: glob 模式搜索
- `write_todos`: 任务规划

#### 自定义工具
**文件**: `src/agents/code_agents.py`

```python
def create_custom_tools(ast_tools=None):
    """创建额外的自定义工具"""
    return [
        analyze_python_code,      # Python 结构分析
        analyze_code_complexity,  # 复杂度分析
    ]
```

### 4. LLM 配置

**文件**: `src/config/settings.py`

```python
class Settings:
    # LLM 配置优先级：
    # 1. LLM_MODEL 环境变量
    # 2. QWEN_MODEL 环境变量  
    # 3. 开发模式: qwen-turbo
    # 4. 生产模式: qwen-max
    
    llm_model = os.environ.get(
        "LLM_MODEL", 
        os.environ.get("QWEN_MODEL", default_model)
    )
```

**支持的 LLM**:
- Qwen (通义千问)
- OpenAI-compatible APIs
- 其他支持 LangChain 的模型

## 通信协议

### JSON-RPC over stdio

```javascript
// 前端发送请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "chat",
  "params": {
    "message": "帮我生成一个斐波那契函数",
    "conversationId": "session-123"
  }
}

// 后端返回响应
{
  "jsonrpc": "2.0", 
  "id": 1,
  "result": {
    "conversation_id": "session-123",
    "full_response": "好的，我来生成...",
    "suggestions": []
  }
}
```

## 数据流示例

### 完整对话流程

```
用户: "帮我生成一个计算斐波那契数列的 Python 函数"
  ↓
VSCode Extension (agentBridge.chat)
  ↓ JSON-RPC: chat(message, conversationId)
Python RPC Server (agent_server.chat)
  ↓
Unified Agent 分析请求
  → 判断：需要代码生成
  → 使用 'task' 工具委派给 code-generator subagent
  ↓
Code Generator Subagent
  → 生成代码
  → 添加文档和类型提示
  → 包含使用示例
  ↓
返回结果给主 Agent
  ↓
主 Agent 返回给用户
  ↓
VSCode 显示结果
```

### 多轮对话示例

```
[Session: conv-001]

Round 1:
用户: "生成一个快速排序函数"
Agent: [委派 code-generator] → 生成代码

Round 2:
用户: "解释一下这个函数的复杂度"
Agent: [委派 code-explainer] → 解释时间复杂度 O(n log n)

Round 3:
用户: "帮我优化一下"
Agent: [委派 refactoring] → 提供优化建议并重构

所有轮次共享同一个 thread_id="conv-001"
```

## 项目结构

```
extension/python_agents/
├── src/
│   ├── agent_server.py          # RPC 服务器主入口
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── unified_agent.py     # 统一 agent 定义
│   │   └── code_agents.py       # 自定义工具
│   ├── config/
│   │   ├── settings.py          # 配置管理
│   │   └── prompts.py           # 系统提示词
│   ├── rpc/
│   │   ├── protocol.py          # JSON-RPC 协议
│   │   ├── server.py            # RPC 服务器
│   │   └── errors.py            # 错误定义
│   ├── tools/
│   │   └── ast_tools.py         # AST 分析工具
│   └── utils/
│       ├── llm_client.py        # LLM 客户端
│       ├── context_builder.py   # 上下文构建
│       ├── logger.py            # 日志
│       └── security.py          # 安全验证
├── tests/                        # 测试
├── docs/                         # 文档
├── pyproject.toml               # Python 依赖
└── uv.lock                      # 依赖锁文件
```

## 配置

### 环境变量

```bash
# LLM 配置
export LLM_MODEL="qwen-plus"          # 优先级最高
export QWEN_MODEL="qwen3-coder-plus"  # 优先级次之
export DASHSCOPE_API_KEY="your-key"   # API 密钥

# 开发模式
export DEV_MODE="true"                # 启用调试
export PYTHONPATH="${PYTHONPATH}:./src"
```

### 调试配置

**文件**: `.vscode/launch.json`

```json
{
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch"
    },
    {
      "name": "Debug Python Backend",
      "type": "debugpy",
      "request": "attach",
      "connect": {"host": "localhost", "port": 5678},
      "cwd": "${workspaceFolder}/extension/python_agents"
    }
  ]
}
```

## 扩展功能

### 添加新的 Subagent

```python
# 1. 在 unified_agent.py 中定义新的 subagent
test_writer_agent = create_deep_agent(
    model=llm,
    system_prompt="You are an expert at writing unit tests...",
    tools=custom_tools,
    backend=backend
)

# 2. 添加到 subagents 列表
subagents = [
    {"name": "code-generator", "agent": code_gen_agent, ...},
    {"name": "code-explainer", "agent": code_exp_agent, ...},
    {"name": "refactoring", "agent": refactor_agent, ...},
    {"name": "test-writer", "agent": test_writer_agent, ...},  # 新增
]

# 3. 更新主 agent 的 system_prompt
system_prompt = """...
Available subagents:
- ...
- test-writer: Write comprehensive unit tests
"""
```

### 添加新的自定义工具

```python
# 在 code_agents.py 中
@tool
def run_tests(file_path: str) -> str:
    """Run tests for a given file"""
    # 实现测试运行逻辑
    return test_results

# 在 create_custom_tools 中添加
tools.append(run_tests)
```

## 最佳实践

### 1. Agent 设计
- ✅ 保持 subagents 职责单一
- ✅ 使用清晰的系统提示
- ✅ 让主 agent 负责分派逻辑

### 2. 工具使用
- ✅ 优先使用 DeepAgents 内置工具
- ✅ 自定义工具只做必要的补充
- ✅ 工具描述要清晰准确

### 3. 性能优化
- ✅ 使用 MemorySaver 而不是数据库（对于短期会话）
- ✅ 合理设置 thread_id（用户级或会话级）
- ✅ 定期清理过期的会话数据

### 4. 错误处理
- ✅ 所有 RPC 方法都有异常处理
- ✅ 提供降级方案（fallback mode）
- ✅ 详细的日志记录

## 参考资源

- [DeepAgents 文档](https://github.com/langchain-ai/deepagents)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [VSCode Extension API](https://code.visualstudio.com/api)
- [JSON-RPC 规范](https://www.jsonrpc.org/specification)

## 总结

Vibe Coding 采用**统一 Agent 架构**，通过单一聊天界面实现所有功能：

- 🎯 用户体验类似 Cursor，一个聊天框搞定所有
- 🤖 智能分派到专业 subagents 处理
- 💾 统一的会话历史管理
- 🔧 基于 DeepAgents 的强大工具系统
- 🚀 易于扩展和维护

这种架构既保持了功能的专业性，又提供了简洁的用户体验。
