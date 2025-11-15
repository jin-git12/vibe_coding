"""
LangGraph Studio 入口点
提供一个可观测的 Agent 实例供 Studio 使用

配置 LangSmith Tracing 以观测 Subagent：
1. 在 .env 中设置 LANGSMITH_TRACING=true
2. 在 .env 中设置 LANGSMITH_API_KEY=<your_key>
3. 运行 langgraph dev 后，在 https://smith.langchain.com 查看完整 trace
"""
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from agents.unified_agent import create_unified_chat_agent
from agents.code_agents import create_custom_tools
from tools import ASTTools
from utils import get_llm_client, LLMConfig
from config import get_settings
from deepagents.backends import FilesystemBackend

# 🔍 确保 LangSmith Tracing 配置生效
# 如果 .env 中配置了 LANGSMITH_TRACING=true，这些会自动加载
if os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1"):
    print("[OK] LangSmith Tracing enabled for subagent observation")
    print(f"   Project: {os.getenv('LANGSMITH_PROJECT', 'default')}")
    print(f"   View traces at: https://smith.langchain.com")
else:
    print("[INFO] LangSmith Tracing disabled. To observe subagents:")
    print("   1. Set LANGSMITH_TRACING=true in .env")
    print("   2. Set LANGSMITH_API_KEY=<your_key> in .env")
    print("   3. Restart langgraph dev")

# 加载配置
settings = get_settings()

# 初始化 LLM 客户端
llm_config = LLMConfig(
    provider=settings.llm_provider,
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    api_base=settings.llm_api_base,
    temperature=settings.llm_temperature,
    max_tokens=settings.llm_max_tokens
)
llm_client = get_llm_client(llm_config)

# 初始化代码分析工具
ast_tools = ASTTools()
custom_tools = create_custom_tools(ast_tools=ast_tools)

# 配置 FilesystemBackend（真实磁盘存储）
# 使用配置的 workspace 路径（支持动态配置）
workspace_dir = settings.get_workspace_dir()
workspace_dir.mkdir(parents=True, exist_ok=True)

# 关键：使用 virtual_mode=True，让路径以 / 开头（虚拟绝对路径）
filesystem_backend = FilesystemBackend(
    root_dir=str(workspace_dir),
    virtual_mode=True  # 启用虚拟路径模式
)
print(f"[OK] Workspace: {workspace_dir.absolute()}")
print(f"[OK] FilesystemBackend initialized (virtual_mode=True)")
if settings.workspace_dir:
    print(f"[INFO] Custom workspace configured via WORKSPACE_DIR: {settings.workspace_dir}")

# 创建统一 Agent（使用 DeepAgents 原生的文件系统工具）
agent = create_unified_chat_agent(
    llm=llm_client._client,  # 传递内部的 ChatOpenAI 实例
    custom_tools=custom_tools,  # 代码分析工具
    backend=filesystem_backend,  # 使用 FilesystemBackend 提供 write_file/read_file 等工具
)
print(f"[OK] Agent created with FilesystemBackend + {len(custom_tools)} code analysis tools")

# Studio 会自动检测这个 'agent' 变量
__all__ = ["agent"]

