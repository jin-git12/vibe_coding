# 📦 包管理说明

## 架构

`extension/python_agents` 是**独立的 uv 项目**：

```
vibe_coding/
└── extension/
    └── python_agents/          # 独立的 uv 项目
        ├── pyproject.toml      # 项目配置
        ├── uv.lock             # 依赖锁文件
        ├── .venv/              # 虚拟环境
        └── src/                # 源代码
```

## 配置

### Python Agents (`extension/python_agents/pyproject.toml`)

```toml
[project]
name = "vibe_coding_agents"
version = "0.2.0"
dependencies = [
    "deepagents>=0.2.5",
    "langchain>=1.0.2,<2.0.0",
    "langchain-openai>=1.0.0,<2.0.0",
    "psutil>=5.9.0",
    "python-dotenv>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

## 为什么使用这种方式？

### ✅ 依赖管理：uv

- 独立的 `uv.lock` 管理所有依赖
- 快速依赖解析和安装
- 跨平台一致性

### ✅ 构建系统：hatchling

- `extension/python_agents` 是**应用**，不是**库**
- hatchling 灵活（支持 `packages = ["src"]`）
- 不需要包名和目录结构严格匹配

### ✅ 独立项目

- 不依赖父目录配置
- 可以独立开发和测试
- 更清晰的项目边界

## 使用方法

### 安装依赖

```bash
# 切换到 python_agents 目录
cd E:\llm_project\vibe_coding\extension\python_agents

# 初始化并安装依赖
uv sync
```

### 运行测试

```bash
# 方式 1：激活虚拟环境后运行
.venv\Scripts\Activate.ps1
python test_deepagents_implementation.py

# 方式 2：直接使用虚拟环境的 Python
.venv\Scripts\python.exe test_deepagents_implementation.py
```

### 运行服务器

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 运行服务器
python src\agent_server.py
```

## 依赖更新

### 添加新依赖

编辑 `extension/python_agents/pyproject.toml`：

```toml
dependencies = [
    "deepagents>=0.2.5",
    "new-package>=1.0.0",  # 添加新依赖
]
```

然后运行：

```bash
cd E:\llm_project\vibe_coding\extension\python_agents
uv lock
```

### 更新依赖

```bash
# 更新所有依赖
uv lock --upgrade

# 更新特定包
uv lock --upgrade-package deepagents
```

## 优势

### ✅ 独立性
- 独立的项目，不依赖父目录
- 清晰的项目边界

### ✅ 灵活构建
- hatchling 支持灵活的源代码布局
- 适合应用开发

### ✅ 快速开发
- uv 的快速依赖解析和安装
- 直接 Python 运行，无需构建步骤

### ✅ 可移植性
- 整个 `python_agents` 目录可以独立移动
- 包含完整的依赖定义和锁文件

## 总结

| 方面 | 工具 | 原因 |
|------|------|------|
| 依赖管理 | uv | 快速、现代 |
| 构建系统 | hatchling | 灵活、适合应用 |
| 运行方式 | 直接 Python | 简单、快速 |
| 虚拟环境 | uv (.venv) | 独立、隔离 |
| 项目类型 | 应用 | 不是库，无需发布 |

这种方式简单、高效，适合 VS Code 扩展的 Python 后端！🎯

