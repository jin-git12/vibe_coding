# 方案1：VS Code 扩展 + Python 子进程完整架构设计

## 📋 目录

1. [整体架构](#整体架构)
2. [项目结构](#项目结构)
3. [通信协议设计](#通信协议设计)
4. [数据流设计](#数据流设计)
5. [生命周期管理](#生命周期管理)
6. [核心模块说明](#核心模块说明)
7. [错误处理机制](#错误处理机制)
8. [状态管理](#状态管理)
9. [安全机制](#安全机制)
10. [实施路线图](#实施路线图)

---

## 整体架构

### 系统层次图

```
┌─────────────────────────────────────────────────────────────┐
│                        VS Code IDE                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Vibe Coding Extension                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │           UI Layer (TypeScript)                 │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │  │
│  │  │  │  Command │  │  WebView │  │  Status Bar  │  │  │  │
│  │  │  │  Palette │  │   Panel  │  │   Indicator  │  │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────────┘  │  │  │
│  │  └──────────────────┬──────────────────────────────┘  │  │
│  │                     │                                  │  │
│  │  ┌──────────────────▼──────────────────────────────┐  │  │
│  │  │        Service Layer (TypeScript)              │  │  │
│  │  │  ┌──────────────┐  ┌────────────────────────┐  │  │  │
│  │  │  │   Python     │  │   Context Manager      │  │  │  │
│  │  │  │   Process    │  │   (File System, AST)   │  │  │  │
│  │  │  │   Manager    │  │                        │  │  │  │
│  │  │  └──────┬───────┘  └────────────────────────┘  │  │  │
│  │  └─────────┼─────────────────────────────────────┘  │  │
│  └────────────┼───────────────────────────────────────┘  │
│               │ JSON-RPC over stdin/stdout                │
│  ┌────────────▼───────────────────────────────────────┐  │
│  │        Python Agent Process                        │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │      JSON-RPC Server (Python)               │   │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │  │
│  │  │  │  Request │  │ Response │  │  Error   │  │   │  │
│  │  │  │  Handler │  │  Builder │  │  Handler │  │   │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │   │  │
│  │  └──────────────────┬──────────────────────────┘   │  │
│  │                     │                               │  │
│  │  ┌──────────────────▼──────────────────────────┐   │  │
│  │  │      Agent Layer (deepagents)              │   │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │  │
│  │  │  │   Code   │  │   Chat   │  │ Refactor │  │   │  │
│  │  │  │  Agent   │  │  Agent   │  │  Agent   │  │   │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │   │  │
│  │  └──────────────────┬──────────────────────────┘   │  │
│  │                     │                               │  │
│  │  ┌──────────────────▼──────────────────────────┐   │  │
│  │  │         Tools Layer (Python)               │   │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │  │
│  │  │  │   File   │  │  Search  │  │   AST    │  │   │  │
│  │  │  │   Tools  │  │   Tools  │  │  Tools   │  │   │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  │   │  │
│  │  └──────────────────┬──────────────────────────┘   │  │
│  └────────────────────┬┴───────────────────────────────┘  │
│                       │                                    │
│  ┌────────────────────▼────────────────────────────────┐  │
│  │           Local File System                         │  │
│  │         Workspace (用户代码)                         │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Qwen LLM API │
                    │  (DashScope)  │
                    └───────────────┘
```

### 通信架构图

```
┌─────────────────────────────┐
│   VS Code Extension (TS)    │
│                             │
│  ┌───────────────────────┐  │
│  │  Python Process       │  │
│  │  Manager              │  │
│  │                       │  │
│  │  • spawn()            │  │
│  │  • lifecycle control  │  │
│  │  • health check       │  │
│  └───────┬───────────────┘  │
│          │                  │
│  ┌───────▼───────────────┐  │
│  │  JSON-RPC Client      │  │
│  │                       │  │
│  │  • request queue      │  │
│  │  • timeout handling   │  │
│  │  • response parser    │  │
│  └───────┬───────────────┘  │
└──────────┼───────────────────┘
           │
           │ stdin  ┌──────────────────────┐
           ├───────►│ {"jsonrpc": "2.0",   │
           │        │  "method": "...",    │
           │        │  "params": {...},    │
           │        │  "id": 1}            │
           │        └──────────────────────┘
           │
           │ stdout ┌──────────────────────┐
           ◄────────│ {"jsonrpc": "2.0",   │
           │        │  "result": {...},    │
           │        │  "id": 1}            │
           │        └──────────────────────┘
           │
           │ stderr ┌──────────────────────┐
           ◄────────│ [logs, errors]       │
           │        └──────────────────────┘
           │
┌──────────▼───────────────────┐
│  Python Agent Process        │
│                              │
│  ┌────────────────────────┐  │
│  │  JSON-RPC Server      │  │
│  │                       │  │
│  │  • stdin reader       │  │
│  │  • method dispatcher  │  │
│  │  • stdout writer      │  │
│  └────────┬──────────────┘  │
│           │                 │
│  ┌────────▼──────────────┐  │
│  │  Method Router        │  │
│  │                       │  │
│  │  • generate_code      │  │
│  │  • explain_code       │  │
│  │  • refactor_code      │  │
│  │  • review_code        │  │
│  │  • search_code        │  │
│  │  • chat               │  │
│  └────────┬──────────────┘  │
│           │                 │
│  ┌────────▼──────────────┐  │
│  │  deepagents           │  │
│  │  + Tools              │  │
│  └───────────────────────┘  │
└──────────────────────────────┘
```

---

## 项目结构

### 完整目录树

```
vibe_coding/
├── extension/                          # VS Code 扩展（TypeScript）
│   ├── src/
│   │   ├── extension.ts               # 扩展入口点
│   │   │
│   │   ├── services/                  # 核心服务层
│   │   │   ├── pythonProcessService.ts    # Python 进程管理
│   │   │   ├── jsonRpcClient.ts          # JSON-RPC 客户端
│   │   │   ├── contextService.ts         # 上下文收集服务
│   │   │   └── agentBridge.ts            # Agent 调用桥接
│   │   │
│   │   ├── commands/                  # VS Code 命令
│   │   │   ├── index.ts                  # 命令注册
│   │   │   ├── generateCode.ts           # 生成代码
│   │   │   ├── explainCode.ts            # 解释代码
│   │   │   ├── refactorCode.ts           # 重构代码
│   │   │   ├── reviewCode.ts             # 审查代码
│   │   │   ├── searchCode.ts             # 搜索代码
│   │   │   └── chatWithAI.ts             # AI 聊天
│   │   │
│   │   ├── ui/                        # 用户界面
│   │   │   ├── chatPanel.ts              # 聊天 WebView
│   │   │   ├── diffEditor.ts             # 差异对比
│   │   │   ├── statusBarItem.ts          # 状态栏
│   │   │   ├── progressIndicator.ts      # 进度提示
│   │   │   └── notificationManager.ts    # 通知管理
│   │   │
│   │   ├── utils/                     # 工具函数
│   │   │   ├── fileSystem.ts             # 文件操作
│   │   │   ├── textProcessor.ts          # 文本处理
│   │   │   ├── languageDetector.ts       # 语言检测
│   │   │   ├── logger.ts                 # 日志记录
│   │   │   └── config.ts                 # 配置管理
│   │   │
│   │   ├── models/                    # 数据模型/接口
│   │   │   ├── rpcTypes.ts               # RPC 请求/响应类型
│   │   │   ├── agentTypes.ts             # Agent 相关类型
│   │   │   └── contextTypes.ts           # 上下文类型
│   │   │
│   │   └── tests/                     # 测试
│   │       ├── unit/
│   │       └── integration/
│   │
│   ├── resources/                     # 静态资源
│   │   ├── python/                       # Python 代码（打包进扩展）
│   │   │   └── (从 python_agents 构建后复制)
│   │   ├── webview/                      # WebView 资源
│   │   │   ├── chat.html
│   │   │   ├── chat.css
│   │   │   └── chat.js
│   │   └── icons/                        # 图标
│   │
│   ├── package.json                   # 扩展清单
│   ├── tsconfig.json                  # TypeScript 配置
│   ├── .vscodeignore                  # 打包忽略文件
│   └── README.md                      # 扩展说明
│
├── python_agents/                      # Python Agent 开发目录
│   ├── src/
│   │   ├── agent_server.py            # JSON-RPC 服务器主入口
│   │   │
│   │   ├── rpc/                       # RPC 层
│   │   │   ├── __init__.py
│   │   │   ├── server.py                 # JSON-RPC 服务器核心
│   │   │   ├── handler.py                # 请求处理器
│   │   │   ├── protocol.py               # 协议定义
│   │   │   └── errors.py                 # 错误码定义
│   │   │
│   │   ├── agents/                    # Agent 实现
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py             # Agent 基类
│   │   │   ├── code_generator.py         # 代码生成 Agent
│   │   │   ├── code_explainer.py         # 代码解释 Agent
│   │   │   ├── code_refactorer.py        # 代码重构 Agent
│   │   │   ├── code_reviewer.py          # 代码审查 Agent
│   │   │   ├── code_searcher.py          # 代码搜索 Agent
│   │   │   └── chat_agent.py             # 聊天 Agent
│   │   │
│   │   ├── tools/                     # 工具集
│   │   │   ├── __init__.py
│   │   │   ├── file_tools.py             # 文件操作工具
│   │   │   ├── search_tools.py           # 搜索工具
│   │   │   ├── ast_tools.py              # AST 分析工具
│   │   │   ├── git_tools.py              # Git 工具
│   │   │   └── shell_tools.py            # Shell 命令工具
│   │   │
│   │   ├── utils/                     # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py             # LLM 客户端
│   │   │   ├── context_builder.py        # 上下文构建
│   │   │   ├── security.py               # 安全检查
│   │   │   ├── cache.py                  # 缓存管理
│   │   │   └── logger.py                 # 日志
│   │   │
│   │   └── config/                    # 配置
│   │       ├── __init__.py
│   │       ├── settings.py               # 设置管理
│   │       └── prompts.py                # Prompt 模板
│   │
│   ├── tests/                         # 测试
│   │   ├── test_agents/
│   │   ├── test_tools/
│   │   └── test_rpc/
│   │
│   ├── pyproject.toml                 # Python 项目配置
│   ├── requirements.txt               # 依赖列表
│   └── README.md                      # Python 端说明
│
├── docs/                               # 文档
│   ├── PROJECT_ARCHITECTURE_OPTIONS.md
│   ├── IPC_COMMUNICATION_OPTIONS.md
│   ├── SOLUTION1_ARCHITECTURE.md      # 本文档
│   ├── API_REFERENCE.md               # API 参考
│   ├── DEVELOPMENT_GUIDE.md           # 开发指南
│   └── DEPLOYMENT_GUIDE.md            # 部署指南
│
├── scripts/                            # 构建脚本
│   ├── build_extension.sh             # 构建扩展
│   ├── package_python.sh              # 打包 Python 代码
│   └── test_all.sh                    # 运行所有测试
│
├── .gitignore
├── .editorconfig
└── README.md                          # 项目总体说明
```

---

## 通信协议设计

### JSON-RPC 消息格式

#### 1. 请求消息（TypeScript → Python）

```json
{
  "jsonrpc": "2.0",
  "method": "方法名",
  "params": {
    "参数名": "参数值"
  },
  "id": 唯一请求ID
}
```

#### 2. 成功响应（Python → TypeScript）

```json
{
  "jsonrpc": "2.0",
  "result": {
    "返回数据"
  },
  "id": 对应的请求ID
}
```

#### 3. 错误响应（Python → TypeScript）

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": 错误码,
    "message": "错误消息",
    "data": {
      "详细信息"
    }
  },
  "id": 对应的请求ID
}
```

#### 4. 通知消息（无需响应）

```json
{
  "jsonrpc": "2.0",
  "method": "notification.progress",
  "params": {
    "percentage": 50,
    "message": "处理中..."
  }
}
```

### 定义的 RPC 方法

#### 核心方法列表

```
┌─────────────────────┬──────────────────────────────────────┐
│     方法名          │              说明                    │
├─────────────────────┼──────────────────────────────────────┤
│ generate_code       │ 生成代码                             │
│ explain_code        │ 解释代码                             │
│ refactor_code       │ 重构代码                             │
│ review_code         │ 审查代码                             │
│ search_code         │ 搜索代码库                           │
│ chat                │ 与 AI 聊天                           │
│ get_context         │ 获取文件上下文                       │
│ analyze_project     │ 分析整个项目结构                     │
│ health_check        │ 健康检查（心跳）                     │
│ shutdown            │ 优雅关闭                             │
└─────────────────────┴──────────────────────────────────────┘
```

#### 方法详细定义

##### 1. generate_code

**功能**：根据提示生成代码

**请求**：
```json
{
  "jsonrpc": "2.0",
  "method": "generate_code",
  "params": {
    "prompt": "创建一个计算器类",
    "language": "python",
    "context": {
      "current_file": "/path/to/file.py",
      "cursor_position": {"line": 10, "column": 5},
      "surrounding_code": "...",
      "workspace_files": ["file1.py", "file2.py"]
    },
    "options": {
      "style": "functional",
      "include_tests": true,
      "include_docs": true
    }
  },
  "id": 1
}
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "result": {
    "code": "生成的代码",
    "explanation": "代码说明",
    "suggestions": ["建议1", "建议2"]
  },
  "id": 1
}
```

##### 2. explain_code

**功能**：解释选中的代码

**请求**：
```json
{
  "jsonrpc": "2.0",
  "method": "explain_code",
  "params": {
    "code": "要解释的代码",
    "language": "typescript",
    "context": {
      "file_path": "/path/to/file.ts",
      "imports": ["import1", "import2"]
    },
    "detail_level": "detailed"
  },
  "id": 2
}
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "result": {
    "summary": "简短摘要",
    "detailed_explanation": "详细解释",
    "key_concepts": ["概念1", "概念2"],
    "complexity": "O(n)",
    "potential_issues": ["问题1"]
  },
  "id": 2
}
```

##### 3. refactor_code

**功能**：重构代码

**请求**：
```json
{
  "jsonrpc": "2.0",
  "method": "refactor_code",
  "params": {
    "code": "要重构的代码",
    "language": "python",
    "refactor_type": "extract_function",
    "instructions": "提取重复的逻辑",
    "context": {...}
  },
  "id": 3
}
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "result": {
    "refactored_code": "重构后的代码",
    "changes": [
      {
        "type": "function_extraction",
        "old_code": "...",
        "new_code": "...",
        "reason": "原因"
      }
    ],
    "diff": "unified diff 格式"
  },
  "id": 3
}
```

##### 4. search_code

**功能**：语义搜索代码库

**请求**：
```json
{
  "jsonrpc": "2.0",
  "method": "search_code",
  "params": {
    "query": "用户认证相关的函数",
    "workspace_root": "/path/to/workspace",
    "file_patterns": ["*.py", "*.ts"],
    "max_results": 10
  },
  "id": 4
}
```

**响应**：
```json
{
  "jsonrpc": "2.0",
  "result": {
    "results": [
      {
        "file": "/path/to/auth.py",
        "line": 42,
        "code_snippet": "def authenticate_user(...):",
        "relevance_score": 0.95,
        "context": "周围代码"
      }
    ],
    "total_matches": 5
  },
  "id": 4
}
```

##### 5. chat

**功能**：与 AI 自由对话

**请求**：
```json
{
  "jsonrpc": "2.0",
  "method": "chat",
  "params": {
    "message": "如何优化这个函数？",
    "conversation_id": "uuid-123",
    "context": {
      "current_file": "/path/to/file.py",
      "selected_code": "...",
      "workspace_info": {...}
    },
    "stream": true
  },
  "id": 5
}
```

**响应（流式）**：
```json
// 流式通知（多次）
{
  "jsonrpc": "2.0",
  "method": "chat.stream",
  "params": {
    "conversation_id": "uuid-123",
    "chunk": "这个函数可以通过...",
    "done": false
  }
}

// 最终响应
{
  "jsonrpc": "2.0",
  "result": {
    "conversation_id": "uuid-123",
    "full_response": "完整回复",
    "suggestions": []
  },
  "id": 5
}
```

### 错误码定义

```
┌──────────┬─────────────────────┬────────────────────────┐
│  错误码  │      名称           │       说明             │
├──────────┼─────────────────────┼────────────────────────┤
│ -32700   │ Parse error         │ JSON 解析错误          │
│ -32600   │ Invalid Request     │ 无效的请求             │
│ -32601   │ Method not found    │ 方法不存在             │
│ -32602   │ Invalid params      │ 无效的参数             │
│ -32603   │ Internal error      │ 内部错误               │
│ -32000   │ Agent error         │ Agent 执行错误         │
│ -32001   │ LLM error           │ LLM API 错误           │
│ -32002   │ File system error   │ 文件系统错误           │
│ -32003   │ Timeout error       │ 超时错误               │
│ -32004   │ Security error      │ 安全检查失败           │
└──────────┴─────────────────────┴────────────────────────┘
```

---

## 数据流设计

### 用户操作流程

#### 流程 1: 生成代码

```
用户操作
    │
    ├─► 1. 用户触发命令（Ctrl+Shift+P → "Generate Code"）
    │
    ▼
UI Layer (commands/generateCode.ts)
    │
    ├─► 2. 收集输入（显示输入框）
    │   └─► 用户输入提示词
    │
    ├─► 3. 收集上下文
    │   ├─► 当前文件路径
    │   ├─► 光标位置
    │   ├─► 周围代码
    │   └─► 语言类型
    │
    ▼
Service Layer (agentBridge.ts)
    │
    ├─► 4. 构建请求参数
    │   └─► { prompt, language, context, options }
    │
    ▼
JSON-RPC Client (jsonRpcClient.ts)
    │
    ├─► 5. 创建 JSON-RPC 请求
    │   ├─► 分配请求 ID
    │   ├─► 包装为 JSON-RPC 格式
    │   └─► 添加到待处理队列
    │
    ├─► 6. 发送到 Python 进程（stdin）
    │   └─► 写入：JSON 字符串 + '\n'
    │
    ▼
Python Process (agent_server.py)
    │
    ├─► 7. 接收请求（stdin）
    │   └─► 逐行读取 JSON
    │
    ├─► 8. 解析 JSON-RPC
    │   ├─► 验证格式
    │   ├─► 提取 method
    │   └─► 提取 params
    │
    ▼
RPC Handler (rpc/handler.py)
    │
    ├─► 9. 路由到对应方法
    │   └─► method_registry['generate_code']
    │
    ▼
Agent Layer (agents/code_generator.py)
    │
    ├─► 10. 准备 Agent
    │   ├─► 初始化 deepagent
    │   ├─► 配置 tools
    │   └─► 构建 system prompt
    │
    ├─► 11. 执行 Agent
    │   ├─► 调用 LLM (Qwen)
    │   ├─► Agent 规划
    │   ├─► 可能使用 tools（读取文件等）
    │   └─► 生成代码
    │
    ├─► 12. 构建响应
    │   └─► { code, explanation, suggestions }
    │
    ▼
RPC Server (rpc/server.py)
    │
    ├─► 13. 包装为 JSON-RPC 响应
    │   └─► { jsonrpc: "2.0", result: {...}, id: X }
    │
    ├─► 14. 发送响应（stdout）
    │   └─► 输出：JSON 字符串 + '\n'
    │
    ▼
JSON-RPC Client (TypeScript)
    │
    ├─► 15. 接收响应（stdout）
    │   └─► readline 逐行读取
    │
    ├─► 16. 解析响应
    │   ├─► 匹配请求 ID
    │   ├─► 从队列中移除
    │   └─► 解析 result
    │
    ▼
Service Layer (agentBridge.ts)
    │
    ├─► 17. 处理结果
    │   └─► 返回 Promise
    │
    ▼
UI Layer (commands/generateCode.ts)
    │
    ├─► 18. 更新 UI
    │   ├─► 在光标位置插入代码
    │   ├─► 显示通知
    │   └─► 更新状态栏
    │
    ▼
用户看到结果
```

#### 流程 2: 流式聊天

```
用户输入消息
    │
    ▼
TypeScript: 发送 chat 请求
    │   { method: "chat", params: { message, stream: true } }
    │
    ▼
Python: 开始流式生成
    │
    ├─► 循环生成 token
    │   │
    │   ├─► 每生成一个 chunk
    │   │   └─► 发送通知（无 id）
    │   │       { method: "chat.stream", params: { chunk, done: false } }
    │   │
    │   ▼
    │   TypeScript: 接收通知
    │   │   └─► 实时更新 UI（append chunk）
    │   │
    │   └─► 循环...
    │
    ├─► 生成完成
    │   └─► 发送最终响应（有 id）
    │       { result: { full_response }, id: X }
    │
    ▼
TypeScript: 显示完整消息
```

### 状态转换图

```
Python 进程状态机：

    ┌─────────┐
    │  IDLE   │  初始状态
    └────┬────┘
         │ start()
         ▼
    ┌─────────┐
    │ STARTING│  正在启动
    └────┬────┘
         │ ready event
         ▼
    ┌─────────┐
    │  READY  │◄────┐  就绪，可以处理请求
    └────┬────┘     │
         │          │ request completed
         │ request  │
         ▼          │
    ┌─────────┐    │
    │  BUSY   │────┘  正在处理请求
    └────┬────┘
         │ error / shutdown
         ▼
    ┌─────────┐
    │ STOPPED │  已停止
    └─────────┘
```

---

## 生命周期管理

### 扩展生命周期

```
VS Code 启动
    │
    ▼
extension.activate()
    │
    ├─► 1. 初始化配置
    │   ├─► 读取用户配置
    │   ├─► 验证环境（检查 Python/uv）
    │   └─► 设置日志
    │
    ├─► 2. 启动 Python 进程
    │   ├─► 确定 Python 路径
    │   ├─► 确定 Agent 脚本路径
    │   ├─► spawn 子进程
    │   ├─► 设置 stdio 管道
    │   └─► 等待就绪信号
    │
    ├─► 3. 注册命令
    │   ├─► vibe-coding.generateCode
    │   ├─► vibe-coding.explainCode
    │   ├─► vibe-coding.refactorCode
    │   ├─► vibe-coding.reviewCode
    │   ├─► vibe-coding.searchCode
    │   └─► vibe-coding.chat
    │
    ├─► 4. 初始化 UI
    │   ├─► 创建状态栏项
    │   ├─► 注册 WebView provider
    │   └─► 设置上下文菜单
    │
    ├─► 5. 启动健康检查
    │   └─► 定时心跳（每 30 秒）
    │
    └─► 扩展激活完成
         │
         ▼
    运行中...
         │
         │ 用户操作 → 命令执行
         │ RPC 调用 → 获取结果
         │
         ▼
VS Code 关闭
    │
    ▼
extension.deactivate()
    │
    ├─► 1. 清理资源
    │   ├─► 关闭 WebView
    │   ├─► 移除状态栏项
    │   └─► 取消订阅
    │
    ├─► 2. 优雅关闭 Python 进程
    │   ├─► 发送 shutdown 请求
    │   ├─► 等待进程退出（最多 5 秒）
    │   └─► 如果超时，强制 kill
    │
    └─► 扩展卸载完成
```

### Python 进程管理

#### 启动流程

```
TypeScript: 调用 spawn()
    │
    ├─► 命令：uv run python agent_server.py
    ├─► 工作目录：extension/resources/python/
    ├─► 环境变量：
    │   ├─► WORKSPACE_ROOT=/path/to/workspace
    │   ├─► DASHSCOPE_API_KEY=xxx
    │   └─► LOG_LEVEL=INFO
    │
    ▼
Python 进程启动
    │
    ├─► 1. 初始化日志（stderr）
    ├─► 2. 加载配置
    ├─► 3. 初始化 Agent
    ├─► 4. 启动 JSON-RPC 服务器
    ├─► 5. 发送就绪通知（stdout）
    │   └─► { method: "server.ready", params: {} }
    │
    ▼
TypeScript: 接收就绪通知
    │
    └─► 标记状态为 READY
```

#### 健康检查

```
定时器（每 30 秒）
    │
    ├─► 发送 health_check 请求
    │   └─► { method: "health_check", id: X }
    │
    ▼
Python: 响应
    │
    ├─► { result: { status: "ok", memory_mb: 150 }, id: X }
    │
    ▼
TypeScript: 检查响应
    │
    ├─► 如果超时（>5秒）
    │   └─► 重启进程
    │
    └─► 如果正常
        └─► 更新状态栏
```

#### 重启机制

```
检测到进程异常
    │
    ├─► 原因：
    │   ├─► 崩溃（exit code != 0）
    │   ├─► 健康检查超时
    │   └─► stderr 输出致命错误
    │
    ▼
自动重启逻辑
    │
    ├─► 1. 记录错误日志
    ├─► 2. 清理旧进程
    ├─► 3. 增加重启计数
    ├─► 4. 检查重启限制
    │   └─► 如果 5 分钟内重启 > 3 次
    │       └─► 放弃重启，通知用户
    │
    ├─► 5. 延迟启动（指数退避）
    │   └─► 等待 2^重启次数 秒
    │
    └─► 6. 重新启动进程
```

---

## 核心模块说明

### TypeScript 端核心模块

#### 1. PythonProcessService

**职责**：管理 Python 子进程的生命周期

**功能**：
- 启动 Python 进程
- 监控进程健康
- 处理进程异常
- 自动重启
- 优雅关闭

**关键方法**：
```
- start(): Promise<void>
- stop(): Promise<void>
- restart(): Promise<void>
- isHealthy(): boolean
- getStatus(): ProcessStatus
```

#### 2. JsonRpcClient

**职责**：JSON-RPC 通信客户端

**功能**：
- 发送 RPC 请求
- 接收并解析响应
- 管理请求队列
- 超时处理
- 错误重试

**关键方法**：
```
- request(method: string, params: any): Promise<any>
- notify(method: string, params: any): void
- onNotification(method: string, handler: Function): void
```

#### 3. ContextService

**职责**：收集和管理代码上下文

**功能**：
- 读取当前文件内容
- 获取光标位置
- 收集相关文件
- 分析导入依赖
- 提取函数/类定义

**关键方法**：
```
- getCurrentContext(): FileContext
- getRelatedFiles(file: string): string[]
- getSymbolAtPosition(position: Position): Symbol
- buildContextForRequest(options: ContextOptions): Context
```

#### 4. AgentBridge

**职责**：高层 Agent 调用接口

**功能**：
- 封装 RPC 调用
- 提供类型安全的 API
- 处理流式响应
- 管理会话状态

**关键方法**：
```
- generateCode(prompt: string, options?: Options): Promise<CodeResult>
- explainCode(code: string, options?: Options): Promise<Explanation>
- refactorCode(code: string, instructions: string): Promise<RefactorResult>
- chat(message: string, conversationId?: string): AsyncIterator<string>
```

### Python 端核心模块

#### 1. JSONRPCServer

**职责**：JSON-RPC 服务器核心

**功能**：
- 监听 stdin
- 解析 JSON-RPC 请求
- 路由到处理器
- 构建响应
- 错误处理

**关键方法**：
```
- run(): None  # 主循环
- register_method(name: str, handler: Callable): None
- handle_request(request: dict) -> dict
- send_response(response: dict): None
- send_notification(method: str, params: dict): None
```

#### 2. Agent Implementations

**职责**：各种 Agent 的具体实现

**模块**：
- CodeGeneratorAgent
- CodeExplainerAgent
- CodeRefactorerAgent
- CodeReviewerAgent
- CodeSearcherAgent
- ChatAgent

**通用结构**：
```python
class BaseAgent:
    def __init__(self, workspace_root: str):
        self.workspace = workspace_root
        self.llm = get_qwen_model()
        self.tools = self.setup_tools()
        self.agent = self.create_agent()
    
    def setup_tools(self) -> List[Tool]:
        # 配置工具
        pass
    
    def create_agent(self) -> DeepAgent:
        # 创建 deepagent
        pass
    
    def execute(self, **params) -> dict:
        # 执行任务
        pass
```

#### 3. Tools

**职责**：为 Agent 提供可用的工具

**工具分类**：

```
FileTools:
- read_file(path: str) -> str
- write_file(path: str, content: str) -> bool
- list_directory(path: str) -> List[str]
- find_files(pattern: str) -> List[str]

SearchTools:
- search_in_file(path: str, query: str) -> List[Match]
- search_in_workspace(query: str) -> List[Match]
- find_definition(symbol: str) -> Location
- find_references(symbol: str) -> List[Location]

ASTTools:
- parse_code(code: str, language: str) -> AST
- extract_functions(code: str) -> List[Function]
- extract_classes(code: str) -> List[Class]
- analyze_complexity(code: str) -> Metrics

GitTools:
- get_git_diff() -> str
- get_file_history(path: str) -> List[Commit]
- get_changed_files() -> List[str]

ShellTools:
- run_command(cmd: str) -> CommandResult
- check_linter(file: str) -> List[Issue]
```

#### 4. Security Module

**职责**：安全检查和权限控制

**功能**：
- 验证文件路径（防止目录遍历）
- 限制可访问的文件
- 命令白名单
- 资源使用限制

**检查项**：
```python
SecurityChecker:
- validate_file_path(path: str, workspace: str) -> bool
  # 确保文件在工作区内
  
- validate_command(cmd: str) -> bool
  # 检查命令是否在白名单
  
- check_resource_usage() -> ResourceStatus
  # 监控内存、CPU 使用
  
- sanitize_input(text: str) -> str
  # 清理输入，防止注入
```

---

## 错误处理机制

### 错误分类和处理策略

```
┌─────────────────────┬─────────────────┬─────────────────────┐
│     错误类型        │    处理策略     │       用户体验      │
├─────────────────────┼─────────────────┼─────────────────────┤
│ RPC 通信错误        │ 自动重试 3 次   │ 显示进度，最后提示  │
│ Python 进程崩溃     │ 自动重启        │ 后台处理，通知用户  │
│ LLM API 错误        │ 重试 + 降级     │ 提示错误，建议操作  │
│ 文件系统错误        │ 立即返回        │ 明确错误消息        │
│ 超时错误            │ 可取消          │ 显示进度，可中断    │
│ 参数验证错误        │ 立即返回        │ 输入提示，高亮错误  │
└─────────────────────┴─────────────────┴─────────────────────┘
```

### 错误处理流程

```
发生错误
    │
    ├─► 1. 捕获异常
    │   ├─► TypeScript: try-catch
    │   └─► Python: exception handler
    │
    ├─► 2. 分类错误
    │   ├─► 可恢复：重试
    │   ├─► 临时性：等待
    │   └─► 致命性：报告
    │
    ├─► 3. 记录日志
    │   ├─► 错误堆栈
    │   ├─► 上下文信息
    │   └─► 时间戳
    │
    ├─► 4. 用户通知
    │   ├─► 错误消息
    │   ├─► 建议操作
    │   └─► 详情链接
    │
    └─► 5. 恢复尝试
        ├─► 重试请求
        ├─► 重启进程
        └─► 降级功能
```

### 重试策略

```typescript
// 指数退避重试
重试逻辑：
    尝试次数  等待时间  累计时间
    1        0s       0s
    2        1s       1s
    3        2s       3s
    4        4s       7s
    5        8s       15s
    放弃     -        -

// 不同错误的重试策略
网络错误：    重试 5 次
超时错误：    重试 3 次
参数错误：    不重试
内部错误：    重试 2 次
```

---

## 状态管理

### 扩展状态

```typescript
扩展状态层级：

GlobalState (跨会话)
├─► apiKey: string
├─► modelPreference: string
└─► userSettings: Settings

WorkspaceState (工作区级别)
├─► pythonProcessStatus: ProcessStatus
├─► activeConversations: Map<string, Conversation>
├─► recentCommands: Command[]
└─► contextCache: Map<string, Context>

SessionState (会话内)
├─► currentRequest: Request | null
├─► pendingRequests: Request[]
└─► uiState: UIState
```

### 状态同步

```
TypeScript 状态         Python 状态
     │                       │
     ├──► workspace_root ───►├─► workspace_root
     ├──► api_key ──────────►├─► llm_config
     ├──► user_settings ────►├─► agent_settings
     │                       │
     │◄─── agent_status ─────┤
     │◄─── resource_usage ───┤
```

---

## 安全机制

### 安全边界

```
┌─────────────────────────────────────────────────────┐
│                VS Code 扩展沙箱                      │
│  ┌───────────────────────────────────────────────┐  │
│  │         TypeScript 代码（可信）                │  │
│  └───────────────────┬───────────────────────────┘  │
└──────────────────────┼───────────────────────────────┘
                       │ JSON-RPC
                       │ (数据验证)
┌──────────────────────▼───────────────────────────────┐
│          Python 子进程（受限）                        │
│  ┌───────────────────────────────────────────────┐  │
│  │   安全检查层                                   │  │
│  │   - 文件路径验证（必须在 workspace 内）       │  │
│  │   - 命令白名单                                 │  │
│  │   - 资源限制（内存、CPU）                     │  │
│  └───────────────┬───────────────────────────────┘  │
│                  │                                   │
│  ┌───────────────▼───────────────────────────────┐  │
│  │   Agent 执行层                                 │  │
│  │   - 只能访问允许的文件                         │  │
│  │   - 只能执行白名单命令                         │  │
│  └───────────────┬───────────────────────────────┘  │
└──────────────────┼───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│           用户工作区（受保护）                        │
│           - 只读/写工作区文件                         │
│           - 不能访问系统文件                          │
└───────────────────────────────────────────────────────┘
```

### 安全策略

#### 1. 文件访问控制

```python
# 安全检查示例
def validate_file_path(file_path: str, workspace_root: str) -> bool:
    """验证文件路径是否安全"""
    # 转换为绝对路径
    abs_path = os.path.abspath(file_path)
    abs_workspace = os.path.abspath(workspace_root)
    
    # 确保在工作区内
    if not abs_path.startswith(abs_workspace):
        raise SecurityError("Access denied: file outside workspace")
    
    # 黑名单检查
    forbidden_patterns = [
        '**/.git/**',
        '**/.env',
        '**/id_rsa',
        '**/secrets.json'
    ]
    
    for pattern in forbidden_patterns:
        if fnmatch.fnmatch(abs_path, pattern):
            raise SecurityError(f"Access denied: sensitive file")
    
    return True
```

#### 2. 命令执行白名单

```python
# 允许的命令
ALLOWED_COMMANDS = {
    'git': ['status', 'diff', 'log', 'show'],
    'python': ['-m', 'pytest', '-m', 'mypy'],
    'npm': ['list', 'outdated'],
    'ruff': ['check', 'format'],
}

def validate_command(cmd: list) -> bool:
    """验证命令是否在白名单"""
    if not cmd:
        return False
    
    program = cmd[0]
    if program not in ALLOWED_COMMANDS:
        raise SecurityError(f"Command not allowed: {program}")
    
    # 检查子命令
    if len(cmd) > 1:
        subcommand = cmd[1]
        allowed_subcmds = ALLOWED_COMMANDS[program]
        if subcommand not in allowed_subcmds:
            raise SecurityError(f"Subcommand not allowed: {subcommand}")
    
    return True
```

#### 3. 资源限制

```python
# 资源监控
class ResourceMonitor:
    MAX_MEMORY_MB = 500  # 最大内存 500MB
    MAX_FILE_SIZE_MB = 10  # 单文件最大 10MB
    MAX_EXECUTION_TIME = 30  # 最长执行 30 秒
    
    def check_memory(self):
        """检查内存使用"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.MAX_MEMORY_MB:
            raise ResourceError(f"Memory limit exceeded: {memory_mb:.1f}MB")
    
    def check_file_size(self, file_path: str):
        """检查文件大小"""
        size_mb = os.path.getsize(file_path) / 1024 / 1024
        
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise ResourceError(f"File too large: {size_mb:.1f}MB")
```

#### 4. 输入清理

```python
def sanitize_input(text: str) -> str:
    """清理用户输入，防止注入攻击"""
    # 移除控制字符
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # 限制长度
    MAX_INPUT_LENGTH = 10000
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH]
    
    return text
```

### 安全检查清单

```
启动时：
✓ 验证 Python 环境
✓ 检查工作区路径
✓ 验证 API Key

运行时：
✓ 每次文件操作前验证路径
✓ 每次命令执行前检查白名单
✓ 定期检查资源使用
✓ 清理所有用户输入

关闭时：
✓ 清理临时文件
✓ 关闭所有文件句柄
✓ 释放资源
```

---

## 实施路线图

### Phase 1: MVP（最小可行产品）- 2-3 天

#### 目标
建立基础架构，实现一个核心功能（代码生成）

#### 任务清单

**Day 1: 基础设施**
```
□ 创建项目结构
  ├─ extension/ 目录
  ├─ python_agents/ 目录
  └─ docs/ 目录

□ TypeScript 端
  ├─ extension.ts (入口)
  ├─ pythonProcessService.ts (进程管理)
  └─ jsonRpcClient.ts (RPC 客户端)

□ Python 端
  ├─ agent_server.py (入口)
  ├─ rpc/server.py (RPC 服务器)
  └─ agents/base_agent.py (基类)

□ 通信测试
  └─ 验证 JSON-RPC 双向通信
```

**Day 2: 核心功能**
```
□ 实现代码生成 Agent
  ├─ agents/code_generator.py
  ├─ 集成 Qwen LLM
  └─ 基础 prompt 模板

□ 实现 VS Code 命令
  ├─ commands/generateCode.ts
  ├─ 输入框交互
  └─ 结果插入编辑器

□ 上下文收集
  └─ 获取当前文件、语言、光标位置
```

**Day 3: 测试和完善**
```
□ 端到端测试
  └─ 用户触发命令 → 生成代码 → 插入编辑器

□ 错误处理
  ├─ 进程崩溃处理
  ├─ 超时处理
  └─ 用户友好的错误提示

□ 基础文档
  └─ README.md
```

**MVP 验收标准**
- ✅ 扩展可以安装
- ✅ Python 进程自动启动
- ✅ 用户可以通过命令生成代码
- ✅ 生成的代码自动插入编辑器
- ✅ 基本错误处理工作

---

### Phase 2: 核心功能完善 - 1 周

#### 目标
实现所有基础功能，完善用户体验

#### Week 1 任务

**Day 1-2: 更多 Agent 功能**
```
□ 代码解释 (explainCode)
  ├─ agents/code_explainer.py
  └─ 显示在 Markdown WebView

□ 代码重构 (refactorCode)
  ├─ agents/code_refactorer.py
  └─ 显示差异对比

□ 代码审查 (reviewCode)
  └─ agents/code_reviewer.py
```

**Day 3-4: WebView 聊天界面**
```
□ 创建聊天 WebView
  ├─ ui/chatPanel.ts
  ├─ resources/webview/chat.html
  └─ resources/webview/chat.css

□ 聊天 Agent
  ├─ agents/chat_agent.py
  └─ 流式响应支持

□ 会话管理
  └─ 保存历史对话
```

**Day 5: 上下文增强**
```
□ 智能上下文收集
  ├─ 分析相关文件
  ├─ 提取导入依赖
  └─ 收集函数/类定义

□ 上下文缓存
  └─ 减少重复分析
```

**Day 6-7: UI/UX 完善**
```
□ 状态栏指示器
  ├─ 显示 Agent 状态
  └─ 显示当前操作

□ 进度提示
  ├─ 长时间操作显示进度
  └─ 可取消操作

□ 通知管理
  ├─ 成功/错误通知
  └─ 操作建议
```

**Phase 2 验收标准**
- ✅ 6 个核心命令全部实现
- ✅ 聊天界面可用
- ✅ 流式响应工作正常
- ✅ 上下文收集准确
- ✅ UI 响应流畅

---

### Phase 3: 高级功能 - 1-2 周

#### 目标
添加高级功能，优化性能和稳定性

#### Week 1: 高级功能

**代码搜索**
```
□ 实现语义搜索
  ├─ agents/code_searcher.py
  ├─ 集成 embedding 模型
  └─ 搜索结果排序

□ 搜索 UI
  └─ 显示搜索结果，支持跳转
```

**项目分析**
```
□ 分析项目结构
  ├─ 识别文件类型
  ├─ 分析依赖关系
  └─ 生成项目图

□ 智能建议
  └─ 根据项目上下文提供建议
```

**多文件操作**
```
□ 批量重构
  └─ 跨文件重命名、提取

□ 项目级搜索替换
  └─ AI 辅助的智能替换
```

#### Week 2: 性能和稳定性

**性能优化**
```
□ 缓存优化
  ├─ LLM 响应缓存
  ├─ 文件内容缓存
  └─ AST 缓存

□ 并发处理
  ├─ 请求队列优化
  └─ 异步处理

□ 资源管理
  └─ 内存使用优化
```

**稳定性增强**
```
□ 完善错误处理
  ├─ 所有边界情况
  └─ 降级策略

□ 自动恢复
  ├─ 进程崩溃恢复
  └─ 请求重试

□ 健康监控
  └─ 实时监控和报警
```

**测试覆盖**
```
□ 单元测试
  ├─ TypeScript 端
  └─ Python 端

□ 集成测试
  └─ 端到端流程

□ 压力测试
  └─ 高并发、长时间运行
```

**Phase 3 验收标准**
- ✅ 所有高级功能可用
- ✅ 性能达标（响应时间 < 2s）
- ✅ 稳定性达标（无崩溃）
- ✅ 测试覆盖率 > 70%

---

### Phase 4: 发布准备 - 3-5 天

#### 目标
准备发布到 VS Code Marketplace

**Day 1-2: 打包优化**
```
□ 压缩 Python 代码
  └─ 移除测试和开发文件

□ 优化扩展大小
  ├─ 移除不必要的依赖
  └─ 压缩资源文件

□ 构建脚本
  ├─ 自动化打包
  └─ CI/CD 配置
```

**Day 3: 文档完善**
```
□ 用户文档
  ├─ README.md
  ├─ 安装指南
  ├─ 使用教程
  └─ 常见问题 FAQ

□ 开发者文档
  ├─ 架构说明
  ├─ API 参考
  └─ 贡献指南

□ CHANGELOG
  └─ 版本历史
```

**Day 4: 跨平台测试**
```
□ Windows 测试
  └─ 路径、编码等问题

□ macOS 测试
  └─ 权限、Python 环境

□ Linux 测试
  └─ 不同发行版
```

**Day 5: 发布**
```
□ Marketplace 准备
  ├─ 图标和截图
  ├─ 描述和标签
  └─ 许可证

□ 发布到 Marketplace
  └─ vsce publish

□ 宣传
  ├─ GitHub README
  ├─ 博客文章
  └─ 社交媒体
```

**发布验收标准**
- ✅ .vsix 包 < 50MB
- ✅ 文档完整
- ✅ 跨平台测试通过
- ✅ 无已知严重 bug
- ✅ 成功发布到 Marketplace

---

## 总结

### 架构亮点

1. **零配置用户体验**
   - 安装即用，无需手动启动服务
   - VS Code 自动管理 Python 进程

2. **标准通信协议**
   - JSON-RPC 2.0，成熟可靠
   - VS Code 生态的标准做法

3. **完整本地访问**
   - deepagents 完整功能可用
   - 直接操作本地文件系统

4. **安全可靠**
   - 文件访问控制
   - 命令白名单
   - 资源限制

5. **可扩展性**
   - 模块化设计
   - 易于添加新 Agent
   - 易于添加新工具

### 技术栈

**前端（TypeScript）**
- VS Code Extension API
- Node.js child_process
- readline 模块

**后端（Python）**
- deepagents
- LangChain
- Qwen (DashScope)

**通信**
- JSON-RPC 2.0
- stdin/stdout

**工具**
- uv (Python 包管理)
- pnpm (Node.js 包管理)
- vsce (扩展打包)

### 预期指标

| 指标 | 目标值 |
|-----|--------|
| 扩展包大小 | < 50MB |
| 启动时间 | < 3 秒 |
| 响应时间 | < 2 秒 |
| 内存占用 | < 500MB |
| 稳定性 | 99% 无崩溃 |

### 下一步

1. ✅ 阅读和理解本架构文档
2. 📋 确认技术选型和实施计划
3. 🏗️ 创建项目骨架
4. 🚀 开始 Phase 1 开发

---

## 附录

### 参考资料

**VS Code 扩展开发**
- [VS Code Extension API](https://code.visualstudio.com/api)
- [Extension Samples](https://github.com/microsoft/vscode-extension-samples)

**JSON-RPC**
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)

**deepagents**
- [deepagents Documentation](https://github.com/example/deepagents)
- [LangChain Documentation](https://python.langchain.com/)

**Qwen**
- [DashScope Documentation](https://help.aliyun.com/dashscope/)

### 常见问题

**Q: Python 进程崩溃怎么办？**
A: 自动重启机制会处理，用户基本无感知。如果频繁崩溃，会提示用户查看日志。

**Q: 支持远程开发吗？**
A: 目前设计针对本地开发。远程开发（VS Code Remote）需要特殊处理，可在后续版本支持。

**Q: 能否支持其他 LLM？**
A: 可以。架构设计支持多 LLM，只需修改 Python 端的 LLM 客户端即可。

**Q: 数据隐私如何保证？**
A: 代码在本地处理，只有 prompt 发送到 LLM API。可选择本地部署的 LLM。

**Q: 性能会影响 VS Code 吗？**
A: Python 进程独立运行，不会阻塞 VS Code UI。有资源限制保护。

---

**文档版本**: v1.0  
**最后更新**: 2025-11-08  
**作者**: Vibe Coding Team