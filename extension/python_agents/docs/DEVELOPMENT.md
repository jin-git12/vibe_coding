# 开发指南

## 📋 快速开始

### 1. 环境准备

```bash
# 前提条件
- Python 3.11+
- uv 包管理器
- VS Code

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装依赖

```bash
cd extension/python_agents

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
.venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
source .venv/bin/activate    # Linux/Mac
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# 必需
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 可选
QWEN_MODEL=qwen-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
WORKSPACE_ROOT=.
LOG_LEVEL=INFO
```

### 4. 运行测试

```bash
# 实现验证测试
python tests\test_deepagents_implementation.py

# 交互式测试
python tests\quick_test.py
```

### 5. 启动服务器

```bash
# 直接运行
python src\agent_server.py

# 或使用 uv
uv run python src\agent_server.py
```

## 🔧 开发工作流

### 添加新的 Agent

1. **在 `src/agents/code_agents.py` 中添加创建函数**：

```python
def create_my_new_agent(
    llm: BaseChatModel,
    custom_tools: Optional[List[BaseTool]] = None
) -> CompiledStateGraph:
    """创建我的新 Agent
    
    Args:
        llm: LLM 实例
        custom_tools: 自定义工具列表
    
    Returns:
        编译后的 StateGraph
    """
    from deepagents import create_deep_agent
    
    system_prompt = """You are a specialized agent for...
    
    Available tools:
    - ls, read_file, write_file, edit_file (file operations)
    - grep_search, glob_search (search)
    - write_todos (planning)
    - ... (your custom tools)
    """
    
    return create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=custom_tools or [],
    )
```

2. **在 `src/agent_server.py` 中初始化**：

```python
def _initialize_agents(self):
    # ... 现有代码 ...
    
    # 添加你的新 Agent
    self.my_new_agent = create_my_new_agent(
        llm=llm_client,
        custom_tools=self.custom_tools
    )
```

3. **添加 RPC 方法**：

```python
def my_new_method(self, params: dict) -> dict:
    """处理新方法的 RPC 请求"""
    try:
        if not self.my_new_agent:
            return {"error": "Agent not initialized"}
        
        # 调用 Agent
        result = self.my_new_agent.invoke({
            "messages": [{"role": "user", "content": params.get("input", "")}]
        })
        
        # 提取响应
        messages = result.get("messages", [])
        response = messages[-1].content if messages else ""
        
        return {"result": response}
    
    except Exception as e:
        logger.error(f"Error in my_new_method: {e}")
        raise

# 在 __init__ 中注册
self.rpc_server.register_method("my_new_method", self.my_new_method)
```

4. **更新 `package.json`（TypeScript 扩展）**：

```json
{
  "commands": [
    {
      "command": "vibe-coding.myNewCommand",
      "title": "My New Command"
    }
  ]
}
```

5. **添加测试**：

```python
# tests/test_my_new_agent.py
def test_my_new_agent():
    from agents import create_my_new_agent
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(
        model="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="test-key"
    )
    
    agent = create_my_new_agent(llm)
    assert agent is not None
    
    # 测试调用
    result = agent.invoke({
        "messages": [{"role": "user", "content": "test"}]
    })
    assert "messages" in result
```

### 添加自定义工具

1. **创建工具文件**（如果是新类别）：

```python
# src/tools/my_tools.py
from langchain_core.tools import tool
from typing import Optional

@tool
def my_custom_tool(arg1: str, arg2: Optional[int] = None) -> str:
    """工具描述（会显示给 LLM）
    
    Args:
        arg1: 参数1描述
        arg2: 参数2描述（可选）
    
    Returns:
        结果描述
    """
    # 实现工具逻辑
    result = f"Processed {arg1} with {arg2}"
    return result


class MyToolsClass:
    """如果需要状态，可以使用类"""
    
    def __init__(self, config: dict):
        self.config = config
    
    @tool
    def complex_tool(self, input: str) -> str:
        """复杂工具描述"""
        # 可以访问 self.config
        return f"Result: {input}"
```

2. **导出工具**：

```python
# src/tools/__init__.py
from .my_tools import my_custom_tool, MyToolsClass

__all__ = ["my_custom_tool", "MyToolsClass", ...]
```

3. **在 `src/agents/code_agents.py` 中添加到工具列表**：

```python
def create_custom_tools(ast_tools, my_tools=None) -> List[BaseTool]:
    """创建自定义工具列表"""
    tools = []
    
    # AST 工具
    if ast_tools:
        tools.extend([
            ast_tools.analyze_python_code,
            ast_tools.analyze_code_complexity,
        ])
    
    # 你的新工具
    if my_tools:
        tools.append(my_tools.my_custom_tool)
    
    return tools
```

4. **在 Agent Server 中初始化**：

```python
# src/agent_server.py
def __init__(self, workspace_root: str):
    # ... 现有代码 ...
    
    # 初始化新工具
    from tools import MyToolsClass
    self.my_tools = MyToolsClass(config={})
    
    # 传递给 create_custom_tools
    self.custom_tools = create_custom_tools(
        self.ast_tools,
        self.my_tools
    )
```

### 修改 System Prompt

所有 system prompt 在 `src/config/prompts.py` 中定义：

```python
# src/config/prompts.py

MY_AGENT_PROMPT = """You are a specialized AI assistant for...

Your capabilities:
1. Capability 1
2. Capability 2
3. Capability 3

Available tools:
- ls, read_file, write_file, edit_file: File system operations
- grep_search, glob_search: Search operations
- write_todos: Task planning
- your_custom_tool: Custom functionality

Guidelines:
- Always ...
- Never ...
- When ..., you should ...

Response format:
...
"""
```

然后在 Agent 创建函数中使用：

```python
from config.prompts import MY_AGENT_PROMPT

def create_my_agent(llm, tools):
    return create_deep_agent(
        model=llm,
        system_prompt=MY_AGENT_PROMPT,
        tools=tools,
    )
```

## 🧪 测试

### 单元测试

```python
# tests/test_unit.py
import pytest
from tools import ASTTools

def test_ast_analysis():
    ast_tools = ASTTools()
    code = """
def hello():
    print("Hello")
    """
    result = ast_tools.analyze_python_code.invoke(code)
    assert "hello" in result
```

### 集成测试

```python
# tests/test_integration.py
def test_agent_server():
    from agent_server import AgentServer
    import os
    
    os.environ["DASHSCOPE_API_KEY"] = "test-key"
    server = AgentServer("/tmp/test")
    
    # 测试健康检查
    result = server.health_check({})
    assert result["status"] == "ok"
```

### 运行测试

```bash
# 运行特定测试
python tests\test_deepagents_implementation.py

# 使用 pytest（如果安装）
pytest tests/

# 运行交互测试
python tests\quick_test.py
```

## 🐛 调试

### 启用 DEBUG 日志

```bash
# 方法 1: 环境变量
export LOG_LEVEL=DEBUG
python src\agent_server.py

# 方法 2: .env 文件
# 在 .env 中设置 LOG_LEVEL=DEBUG
```

### 查看详细输出

所有日志输出到 `stderr`，不会影响 JSON-RPC 通信（使用 `stdout`）。

### 使用 Python 调试器

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 VS Code 调试器
# 创建 .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Agent Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/agent_server.py",
      "console": "integratedTerminal",
      "env": {
        "WORKSPACE_ROOT": "${workspaceFolder}",
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

### 测试 JSON-RPC 通信

```python
# test_rpc.py
import json
import sys

# 构建请求
request = {
    "jsonrpc": "2.0",
    "method": "health_check",
    "params": {},
    "id": 1
}

# 发送（模拟）
print(json.dumps(request), file=sys.stdout, flush=True)

# Python Agent Server 会通过 stdout 返回响应
```

## 📦 依赖管理

### 添加新依赖

```bash
# 方法 1: 直接安装
cd extension/python_agents
uv add package-name

# 方法 2: 手动编辑 pyproject.toml
# 在 [project.dependencies] 中添加:
# "package-name>=1.0.0"
# 然后运行:
uv sync
```

### 更新依赖

```bash
# 更新所有依赖到最新兼容版本
uv sync --upgrade

# 更新特定包
uv add package-name@latest
```

### 查看依赖树

```bash
uv tree
```

## 🔒 安全最佳实践

### 1. 文件操作

```python
from utils.security import SecurityChecker

security = SecurityChecker(workspace_root="/path/to/workspace")

# 验证路径安全性
if security.is_path_safe("/path/to/file"):
    # 执行文件操作
    pass
else:
    raise SecurityError("Path is not safe")
```

### 2. 命令执行

```python
# 检查命令是否在白名单中
if security.is_command_allowed("git status"):
    # 执行命令
    pass
```

### 3. 输入清理

```python
# 清理用户输入
clean_input = security.sanitize_input(user_input)
```

### 4. 环境变量

```python
# 永远不要记录或返回敏感信息
import os
api_key = os.getenv("DASHSCOPE_API_KEY")
# 不要: logger.info(f"API Key: {api_key}")
# 应该: logger.info("API Key loaded")
```

## 📝 代码风格

### Python 风格指南

遵循 **PEP 8** 和项目约定：

```python
# 1. 导入顺序
import os  # 标准库
import sys

from typing import List, Optional  # 标准库类型

from langchain_core.tools import tool  # 第三方库

from utils.logger import setup_logger  # 本地模块


# 2. 类型注解
def my_function(arg1: str, arg2: int = 0) -> dict:
    """函数文档字符串
    
    Args:
        arg1: 参数1描述
        arg2: 参数2描述（默认值）
    
    Returns:
        返回值描述
    
    Raises:
        ValueError: 错误条件描述
    """
    return {"result": arg1 * arg2}


# 3. 错误处理
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    return {"error": str(e)}


# 4. 日志记录
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Error with traceback")
```

### 代码检查

```bash
# 安装开发依赖（如果需要）
uv add --dev black isort mypy flake8

# 格式化代码
black src/ tests/

# 排序导入
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
flake8 src/
```

## 🚀 发布流程

### 1. 版本更新

更新 `pyproject.toml` 中的版本号：

```toml
[project]
name = "vibe_coding_agents"
version = "0.2.0"  # 更新版本
```

### 2. 更新文档

- 更新 `README.md`
- 更新 `docs/` 中的相关文档
- 添加更新日志（可选）

### 3. 运行测试

```bash
# 确保所有测试通过
python tests\test_deepagents_implementation.py

# 手动测试
python tests\quick_test.py
```

### 4. 提交更改

```bash
git add .
git commit -m "Release v0.2.0: Add new feature X"
git tag v0.2.0
git push origin main --tags
```

## 🔍 故障排除

### 常见问题

#### 1. DeepAgents 导入失败

```bash
# 确保已安装
uv add deepagents>=0.2.5

# 检查安装
python -c "import deepagents; print(deepagents.__version__)"
```

#### 2. API Key 未设置

```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY  # Linux/Mac
$env:DASHSCOPE_API_KEY   # PowerShell

# 或在 .env 文件中设置
DASHSCOPE_API_KEY=your_key_here
```

#### 3. 虚拟环境未激活

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate

# 验证
which python  # 应该指向 .venv 中的 Python
```

#### 4. JSON-RPC 通信问题

- 确保所有输出到 `stdout` 的都是有效 JSON
- 日志应该输出到 `stderr`
- 使用 `flush=True` 确保立即发送

```python
# 正确
logger.info("Log message")  # 输出到 stderr
print(json.dumps(response), flush=True)  # 输出到 stdout

# 错误
print("Debug info")  # 会破坏 JSON-RPC 通信
```

## 📚 参考资料

### 官方文档

- [DeepAgents GitHub](https://github.com/aiwaves-cn/deepagents)
- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [uv 文档](https://github.com/astral-sh/uv)

### 内部文档

- [架构文档](ARCHITECTURE.md)
- [包管理说明](PACKAGE_MANAGEMENT.md)
- [测试说明](../tests/README.md)

---

**最后更新**: 2025-11-09  
**维护者**: Vibe Coding Team







