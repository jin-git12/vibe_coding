# 📚 Python Agents 文档

Python 后端 Agent 服务的完整文档，基于 DeepAgents 框架。

## 📖 文档导航

### 核心文档

| 文档 | 说明 | 适合读者 |
|------|------|---------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 系统架构设计 | 所有开发者 |
| **[DEVELOPMENT.md](DEVELOPMENT.md)** | 开发指南和最佳实践 | 贡献者 |
| **[PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md)** | 依赖和包管理 | 新手开发者 |

### 快速开始

#### 👨‍💻 我想了解系统架构
→ 阅读 **[ARCHITECTURE.md](ARCHITECTURE.md)**
- 🏗️ 系统整体设计
- 📁 目录结构说明
- 🎯 核心组件介绍
- 📡 通信协议详解
- 🔒 安全机制说明

#### 🛠️ 我想开始开发
→ 阅读 **[DEVELOPMENT.md](DEVELOPMENT.md)**
- 🚀 环境搭建
- 🔧 开发工作流
- 🧪 测试和调试
- 📦 依赖管理
- 📝 代码风格指南

#### 📦 我想管理依赖
→ 阅读 **[PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md)**
- uv 包管理器使用
- 虚拟环境配置
- 依赖安装和更新
- 项目配置详解

## 🎯 常见任务

### 新建 Agent
1. 在 `src/agents/code_agents.py` 创建函数
2. 在 `src/agent_server.py` 注册 RPC 方法
3. 添加到 TypeScript 扩展
4. 编写测试

→ 详见 [DEVELOPMENT.md - 添加新的 Agent](DEVELOPMENT.md#添加新的-agent)

### 添加自定义工具
1. 在 `src/tools/` 创建工具文件
2. 使用 `@tool` 装饰器
3. 添加到 `create_custom_tools`
4. 更新 system prompt

→ 详见 [DEVELOPMENT.md - 添加自定义工具](DEVELOPMENT.md#添加自定义工具)

### 调试问题
1. 启用 DEBUG 日志
2. 使用 Python 调试器
3. 查看 stderr 输出
4. 测试 JSON-RPC 通信

→ 详见 [DEVELOPMENT.md - 调试](DEVELOPMENT.md#🐛-调试)

## 📊 文档结构

```
docs/
├── README.md                 # 📍 本文件（文档索引和导航）
├── ARCHITECTURE.md           # 🏗️ 系统架构（新）
├── DEVELOPMENT.md            # 🛠️ 开发指南（新）
└── PACKAGE_MANAGEMENT.md     # 📦 包管理说明
```

## 🔄 文档更新历史

### v1.0.0 (2025-11-09)

**重大更新**：文档重组和整合

**新增**：
- ✅ `ARCHITECTURE.md` - 统一的架构文档
- ✅ `DEVELOPMENT.md` - 完整的开发指南

**合并**：
- ♻️ `README_DEEPAGENTS.md` → `ARCHITECTURE.md`
- ♻️ `README_IMPLEMENTATION.md` → `ARCHITECTURE.md` + `DEVELOPMENT.md`

**删除**：
- ❌ `DEEPAGENTS_MIGRATION.md` - 迁移已完成，历史意义不大
- ❌ `README_DEEPAGENTS.md` - 已合并
- ❌ `README_IMPLEMENTATION.md` - 已合并

**保留**：
- ✅ `PACKAGE_MANAGEMENT.md` - 独立且重要

## 🤝 贡献文档

### 添加新文档

1. 在 `docs/` 目录创建新的 `.md` 文件
2. 使用清晰的标题和结构
3. 添加代码示例和图表
4. 更新本 `README.md` 添加索引链接

### 文档风格指南

- ✅ 使用 emoji 图标增强可读性
- ✅ 提供代码示例
- ✅ 包含实际用例
- ✅ 添加警告和注意事项
- ✅ 保持简洁明了
- ✅ 定期更新

### 文档模板

```markdown
# 文档标题

## 📋 概述
简要说明文档内容...

## 🎯 目标读者
本文档适合...

## 📖 内容
...

## 🔗 相关文档
- [文档1](link1.md)
- [文档2](link2.md)

---
**最后更新**: YYYY-MM-DD
```

## 📚 外部资源

### 框架和库
- [DeepAgents GitHub](https://github.com/aiwaves-cn/deepagents) - AI Agent 框架
- [LangChain 文档](https://python.langchain.com/) - LLM 应用框架
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/) - Agent 工作流
- [uv 文档](https://github.com/astral-sh/uv) - Python 包管理器

### API 和服务
- [DashScope API](https://help.aliyun.com/dashscope/) - 通义千问 API
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification) - 通信协议

### VS Code 扩展开发
- [VS Code 扩展 API](https://code.visualstudio.com/api) - 官方文档
- [VS Code Extension Samples](https://github.com/microsoft/vscode-extension-samples) - 示例代码

## 💡 反馈和建议

如果发现文档有误或需要改进：
1. 在项目中创建 Issue
2. 提交 Pull Request
3. 联系维护团队

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-09  
**维护者**: Vibe Coding Team

