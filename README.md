# Vibe Coding - AI 代码助手 VS Code 扩展

基于 DeepAgents 和 Qwen LLM 的智能代码助手，提供聊天、代码生成、解释和重构等功能。

## 🎯 特性

- 💬 **AI 聊天**: 与 AI 助手对话，获取编程帮助
- 🔧 **代码生成**: 根据描述生成高质量代码
- 📖 **代码解释**: 理解复杂代码的功能和逻辑
- ♻️ **代码重构**: 优化和改进现有代码
- 🔍 **AST 分析**: Python 代码结构分析

## 📁 项目结构

```
vibe_coding/
└── extension/                      # VS Code 扩展
    ├── src/                        # TypeScript 源代码
    │   ├── extension.ts            # 扩展主入口
    │   ├── services/               # 服务层（Python 进程管理、RPC 通信）
    │   ├── ui/                     # UI 组件（聊天界面、树视图）
    │   ├── commands/               # 命令实现
    │   └── utils/                  # 工具函数
    │
    ├── python_agents/              # Python 后端（独立 uv 项目）
    │   ├── pyproject.toml          # Python 项目配置
    │   ├── uv.lock                 # 依赖锁文件
    │   ├── .venv/                  # 虚拟环境
    │   ├── src/
    │   │   ├── agent_server.py    # JSON-RPC 服务器
    │   │   ├── agents/             # DeepAgents 实现
    │   │   ├── tools/              # AST 分析工具
    │   │   ├── config/             # 配置和提示模板
    │   │   ├── utils/              # 工具函数
    │   │   └── rpc/                # RPC 协议
    │   └── test_*.py               # 测试文件
    │
    ├── resources/                  # 静态资源
    │   ├── webview/                # WebView HTML/CSS/JS
    │   ├── icons/                  # 图标
    │   └── fonts/                  # 字体
    │
    ├── package.json                # 扩展清单
    ├── tsconfig.json               # TypeScript 配置
    └── README.md                   # 扩展文档
```

## 🚀 快速开始

### 1. 安装 VS Code 扩展依赖

```bash
cd extension
pnpm install
```

### 2. 安装 Python 后端依赖

```bash
cd extension/python_agents
uv sync
```

### 3. 编译 TypeScript

```bash
cd extension
pnpm run compile

# 或使用监听模式
pnpm run watch
```

### 4. 调试扩展

1. 在 VS Code 中打开项目
2. 按 `F5` 启动调试
3. 新窗口将打开，扩展已加载

### 5. 配置 API Key

在 `extension/python_agents/.env` 中配置：

```env
DASHSCOPE_API_KEY=your_api_key_here
QWEN_MODEL=qwen-turbo
```

### 6. 测试功能

- 点击左侧边栏的 Vibe Coding 图标
- 在聊天框中输入问题
- 使用命令面板 (`Ctrl+Shift+P`) 执行各种命令

## 🛠️ 技术栈

### 前端（VS Code 扩展）
- **TypeScript** - 类型安全的 JavaScript
- **VS Code Extension API** - 扩展开发框架
- **WebView** - 嵌入式网页界面
- **JSON-RPC** - 进程间通信

### 后端（Python Agents）
- **DeepAgents** (>=0.2.5) - 深度 Agent 框架
- **LangChain** (>=1.0.2) - LLM 应用框架
- **Qwen LLM** - 通义千问大语言模型
- **uv** - 现代 Python 包管理器

## 📚 文档

- [Python 后端实现指南](extension/python_agents/README_IMPLEMENTATION.md)
- [DeepAgents 使用说明](extension/python_agents/README_DEEPAGENTS.md)
- [包管理说明](extension/python_agents/PACKAGE_MANAGEMENT.md)
- [DeepAgents 迁移指南](extension/python_agents/DEEPAGENTS_MIGRATION.md)

## 🧪 测试

### Python 后端测试

```bash
cd extension/python_agents
.venv\Scripts\python.exe test_deepagents_implementation.py
```

### 交互式测试

```bash
cd extension/python_agents
.venv\Scripts\python.exe quick_test.py
```

## 🔧 开发

### Python 后端开发

```bash
cd extension/python_agents

# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 运行服务器
python src\agent_server.py

# 运行测试
python test_deepagents_implementation.py
```

### TypeScript 开发

```bash
cd extension

# 监听模式（自动编译）
pnpm run watch

# 打包扩展
pnpm run package
```

## 📦 打包发布

```bash
cd extension
pnpm run compile
pnpm run package

# 生成 vibe-coding-*.vsix 文件
```

安装 VSIX：
```bash
code --install-extension vibe-coding-*.vsix
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [DeepAgents](https://github.com/langchain-ai/deepagents) - 深度 Agent 框架
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [Qwen](https://github.com/QwenLM/Qwen) - 通义千问大语言模型

---

**作者**: 金旭峰  
**Email**: 929039704@qq.com
