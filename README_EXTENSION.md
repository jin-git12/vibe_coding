# Vibe Coding VS Code Extension - 快速开始

## 项目结构

```
vibe_coding/
├── extension/                 # VS Code 扩展
│   ├── src/                  # TypeScript 源代码
│   │   ├── extension.ts      # 扩展主入口
│   │   ├── agents/          # Agent 客户端
│   │   ├── commands/        # 命令实现
│   │   ├── webview/         # WebView 组件
│   │   └── utils/           # 工具函数
│   ├── package.json         # 扩展清单
│   └── tsconfig.json        # TypeScript 配置
├── backend/                  # Python 后端
│   └── api/
│       └── main.py          # FastAPI 后端
└── docs/                    # 文档
```

## 快速开始

### 1. 安装扩展依赖

```bash
cd extension
npm install
```

### 2. 编译 TypeScript

```bash
npm run compile
# 或使用监听模式
npm run watch
```

### 3. 启动后端 API

```bash
# 从项目根目录
cd backend/api
uv run python main.py
```

后端将在 `http://localhost:8000` 启动。

### 4. 调试扩展

1. 在 VS Code 中打开 `extension` 文件夹
2. 按 `F5` 启动调试
3. 新窗口将打开，扩展已加载

### 5. 测试功能

- 打开命令面板 (`Ctrl+Shift+P`)
- 输入 "Vibe Coding" 查看所有命令
- 尝试 "Generate Code" 或 "Explain Code"

## 配置

在 VS Code 设置中配置：

1. `vibe-coding.apiUrl` - 后端 API URL（默认：http://localhost:8000）
2. `vibe-coding.enableAutoComplete` - 启用 AI 自动补全

## 下一步

1. **集成真实的 Agent**：修改 `backend/api/main.py`，集成你的 LangChain Agent
2. **完善功能**：实现代码补全、搜索等高级功能
3. **优化 UI**：改进 WebView 界面
4. **添加测试**：编写单元测试和集成测试

## 文档

- [VS Code 扩展完整指南](./docs/VSCODE_EXTENSION_GUIDE.md)
- [快速开始指南](./docs/VSCODE_SETUP_GUIDE.md)
- [项目模板](./docs/VSCODE_PROJECT_TEMPLATE.md)

## 问题排查

### 扩展无法连接后端

1. 确保后端 API 正在运行 (`http://localhost:8000`)
2. 检查 VS Code 设置中的 `vibe-coding.apiUrl`
3. 查看输出面板中的 "Vibe Coding" 日志

### 命令不工作

1. 检查后端 API 是否正常响应
2. 查看开发者工具中的错误信息
3. 检查扩展是否正确激活

## 开发提示

- 使用 `console.log` 调试，输出会显示在调试控制台
- 使用 `logger` 工具记录日志，可在输出面板查看
- 修改代码后需要重新编译（或使用 `watch` 模式）

