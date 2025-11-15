"""
Agent 服务器主入口
启动 JSON-RPC 服务器并注册 Agent 方法
"""
import os
import sys
import logging
from pathlib import Path
import io

# 🔧 强制使用 UTF-8 编码（解决 Windows GBK 问题）
if sys.platform == 'win32':
    # 重新配置 stdout 和 stderr 使用 UTF-8 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# 🐛 启用远程调试（仅在开发模式）
if os.getenv('DEV_MODE') == 'true':
    try:
        import debugpy
        if not debugpy.is_client_connected():
            debugpy.listen(("0.0.0.0", 5678))
            print("🐛 Debugpy listening on port 5678", file=sys.stderr, flush=True)
            # 不要 wait_for_client()，让程序继续运行，调试器可以随时附加
    except ImportError:
        print("⚠️ debugpy not installed, debugging disabled", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"⚠️ Failed to start debugpy: {e}", file=sys.stderr, flush=True)

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from rpc import JSONRPCServer, AgentError, LLMError
from utils import (
    setup_logger,
    get_llm_client,
    LLMConfig,
    ContextBuilder,
    SecurityChecker
)
from config import get_settings
from agents import create_custom_tools
from agents.unified_agent import create_unified_chat_agent
from tools import ASTTools
from langgraph.checkpoint.memory import MemorySaver  # 🔧 对话历史管理


logger = logging.getLogger(__name__)


class AgentServer:
    """Agent 服务器 - 基于 deepagents (正确方式)"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.rpc_server = JSONRPCServer()
        
        # 加载配置
        self.settings = get_settings()
        
        # 初始化 AST 工具（deepagents 未提供）
        self.ast_tools = ASTTools()
        
        # 初始化 LLM 客户端
        llm_config = LLMConfig(
            provider=self.settings.llm_provider,
            model=self.settings.llm_model,
            api_key=self.settings.llm_api_key,
            api_base=self.settings.llm_api_base,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens
        )
        self.llm_client = get_llm_client(llm_config)
        
        # 初始化上下文构建器和安全检查器
        self.context_builder = ContextBuilder(self.workspace_root)
        self.security_checker = SecurityChecker(self.workspace_root)
        
        # 创建自定义工具（只包含 AST 分析，文件系统由 deepagents 提供）
        self.custom_tools = create_custom_tools(
            ast_tools=self.ast_tools
        )
        
        # 创建 Deep Agents
        self._initialize_agents()
        
        # 注册方法
        self.register_methods()
    
    def _initialize_agents(self):
        """初始化所有 Deep Agents"""
        try:
            logger.info("Creating deep agents...")
            
            # 检查 LLM 是否可用
            if self.llm_client._client is None:
                logger.warning("LLM client not available, agent will use fallback mode")
                self.unified_agent = None
                return
            
            llm = self.llm_client._client
            
            # 🔧 创建 Checkpointer 用于对话历史管理
            self.checkpointer = MemorySaver()
            logger.info("✓ Memory checkpointer created")
            
            # 🔧 创建 FilesystemBackend 将文件保存到真实磁盘
            from deepagents.backends import FilesystemBackend
            workspace_dir = self.settings.get_workspace_dir()
            workspace_dir.mkdir(parents=True, exist_ok=True)
            filesystem_backend = FilesystemBackend(
                root_dir=str(workspace_dir),
                virtual_mode=True  # 使用虚拟路径模式
            )
            logger.info(f"✓ Filesystem backend created: {workspace_dir}")
            if self.settings.workspace_dir:
                logger.info(f"   Custom workspace configured: {self.settings.workspace_dir}")
            
            # 🎯 创建统一的 Chat Agent
            self.unified_agent = create_unified_chat_agent(
                llm,
                self.custom_tools,
                backend=filesystem_backend  # 使用真实文件系统
            )
            logger.info("✓ Unified agent created (single DeepAgent with all capabilities)")
            logger.info("   • Can generate, explain, and refactor code")
            logger.info(f"   • Files saved to: {workspace_dir}")
            logger.info("🎉 All operations unified through one intelligent agent!")
            
        except Exception as e:
            logger.error(f"Failed to initialize unified agent: {e}")
            import traceback
            traceback.print_exc()
            # 降级到无 Agent 模式
            self.unified_agent = None
    
    def register_methods(self):
        """注册所有 RPC 方法"""
        self.rpc_server.register_method("health_check", self.health_check)
        self.rpc_server.register_method("chat", self.chat)
        self.rpc_server.register_method("generate_code", self.generate_code)
        self.rpc_server.register_method("explain_code", self.explain_code)
        self.rpc_server.register_method("refactor_code", self.refactor_code)
        self.rpc_server.register_method("review_code", self.review_code)
        self.rpc_server.register_method("search_code", self.search_code)
        self.rpc_server.register_method("switch_model", self.switch_model)  # 🆕 模型切换
        self.rpc_server.register_method("switch_workspace", self.switch_workspace)  # 🆕 工作区切换
        self.rpc_server.register_method("shutdown", self.shutdown)
    
    def health_check(self, params: dict) -> dict:
        """健康检查"""
        logger.debug("Health check called")
        return {
            "status": "ok",
            "workspace": self.workspace_root,
            "workspace_dir": str(self.settings.get_workspace_dir()),  # 实际文件保存路径
            "current_model": self.settings.llm_model,  # 包含当前模型
            "methods": list(self.rpc_server.methods.keys())
        }
    
    def switch_model(self, params: dict) -> dict:
        """
        动态切换 LLM 模型
        
        参数:
            model: str - 新的模型名称
        """
        logger.info(f"🔧 switch_model called with params: {params}")
        
        new_model = params.get('model')
        if not new_model:
            logger.error("Model name is missing in params")
            raise AgentError("Model name is required")
        
        old_model = self.settings.llm_model
        
        try:
            logger.info(f"📝 Switching model from {old_model} to {new_model}")
            
            # 更新配置
            self.settings.llm_model = new_model
            
            # 重新创建 LLM 客户端
            llm_config = LLMConfig(
                provider=self.settings.llm_provider,
                api_key=self.settings.llm_api_key,
                api_base=self.settings.llm_api_base,
                model=new_model,  # 使用新模型
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens
            )
            self.llm_client = get_llm_client(llm_config)
            
            # 重新初始化 agents
            self._initialize_agents()
            
            logger.info(f"✓ Model switched successfully: {old_model} → {new_model}")
            
            return {
                "success": True,
                "old_model": old_model,
                "new_model": new_model,
                "message": f"Model switched from {old_model} to {new_model}"
            }
            
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            # 回滚到旧模型
            self.settings.llm_model = old_model
            raise AgentError(f"Failed to switch model: {str(e)}")
    
    def switch_workspace(self, params: dict) -> dict:
        """
        动态切换工作区目录
        
        用于 VSCode 插件场景：当用户打开不同工程时，动态切换 Agent 的文件操作目标目录
        
        参数:
            workspace_dir: str - 新的工作区目录路径（绝对路径或相对于 workspace_root 的相对路径）
        """
        logger.info(f"🔧 switch_workspace called with params: {params}")
        
        new_workspace = params.get('workspace_dir') or params.get('workspaceDir')
        if not new_workspace:
            logger.error("workspace_dir is missing in params")
            raise AgentError("workspace_dir is required")
        
        old_workspace = str(self.settings.get_workspace_dir())
        
        try:
            logger.info(f"📁 Switching workspace from {old_workspace} to {new_workspace}")
            
            # 更新配置
            self.settings.workspace_dir = new_workspace
            
            # 获取实际的工作区路径
            new_workspace_path = self.settings.get_workspace_dir()
            
            # 验证路径
            if not new_workspace_path.parent.exists():
                raise AgentError(f"Parent directory does not exist: {new_workspace_path.parent}")
            
            # 创建工作区目录
            new_workspace_path.mkdir(parents=True, exist_ok=True)
            
            # 重新初始化 agents（使用新的 workspace）
            self._initialize_agents()
            
            logger.info(f"✓ Workspace switched successfully")
            logger.info(f"   Old: {old_workspace}")
            logger.info(f"   New: {new_workspace_path}")
            
            return {
                "success": True,
                "old_workspace": old_workspace,
                "new_workspace": str(new_workspace_path),
                "message": f"Workspace switched to {new_workspace_path}"
            }
            
        except Exception as e:
            logger.error(f"Failed to switch workspace: {e}")
            import traceback
            traceback.print_exc()
            raise AgentError(f"Failed to switch workspace: {str(e)}")
    
    def chat(self, params: dict) -> dict:
        """
        AI 聊天 (使用统一的 Unified Agent)
        
        所有操作（聊天、代码生成、解释、重构）都通过这个方法完成
        Agent 会自动判断是否需要委派给 subagent
        
        参数:
            message: str - 用户消息
            conversation_id: str - 会话 ID（可选）
            context: dict - 上下文信息（可选）
            stream: bool - 是否流式响应（可选）
        """
        logger.info(f"Chat request: {params.get('message', '')[:50]}...")
        
        try:
            if self.unified_agent is None:
                # 降级模式：返回模拟响应
                return {
                    "conversation_id": params.get("conversation_id", "default"),
                    "full_response": f"[Fallback Mode] Agent not initialized: {params.get('message', '')}",
                    "suggestions": []
                }
            
            # 🔧 获取会话 ID（用于对话历史管理）
            conversation_id = params.get("conversationId") or params.get("conversation_id", "default")
            
            # 调用统一 Agent with thread_id 支持对话历史
            result = self.unified_agent.invoke(
                {"messages": [{"role": "user", "content": params.get("message", "")}]},
                {"configurable": {"thread_id": conversation_id}}  # 🔧 使用 thread_id 管理对话历史
            )
            
            # 提取响应
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                else:
                    response = str(last_message)
            else:
                response = str(result)
            
            # 如果是流式响应，发送通知
            if params.get("stream"):
                # 🔧 支持 camelCase (前端) 和 snake_case (Python) 两种命名
                conversation_id = params.get("conversationId") or params.get("conversation_id", "default")
                
                # 模拟流式发送
                chunks = response.split("。")
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        self.rpc_server.send_notification("chat.stream", {
                            "conversationId": conversation_id,  # 🔧 使用 camelCase 与前端保持一致
                            "chunk": chunk + "。",
                            "done": i == len(chunks) - 1
                        })
            
            # 🔧 支持 camelCase (前端) 和 snake_case (Python) 两种命名
            conversation_id = params.get("conversationId") or params.get("conversation_id", "default")
            return {
                "conversationId": conversation_id,  # 🔧 使用 camelCase 与前端保持一致
                "full_response": response,
                "suggestions": []
            }
        
        except Exception as e:
            logger.exception("Error in chat")
            raise AgentError(str(e))
    
    def generate_code(self, params: dict) -> dict:
        """
        生成代码 (委派给统一 Agent)
        
        统一 Agent 会自动使用 code-generator subagent 处理
        
        参数:
            prompt: str - 生成提示
            language: str - 编程语言
            context: dict - 上下文信息（可选）
            options: dict - 生成选项（可选）
        """
        prompt = params.get('prompt', '')
        language = params.get('language', 'python')
        logger.info(f"Generate code request: {prompt[:50]}... (language: {language})")
        
        try:
            if self.unified_agent is None:
                # 降级模式
                code = f"""# Generated code for: {prompt}
# Language: {language}

def placeholder():
    \"\"\"Placeholder function. Configure LLM to generate real code.\"\"\"
    pass
"""
                return {
                    "code": code,
                    "explanation": "[Fallback Mode] LLM not configured",
                    "suggestions": ["Configure API key to enable real code generation"]
                }
            
            # 调用统一 Agent（会自动委派给 code-generator subagent）
            result = self.unified_agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Generate {language} code: {prompt}"
                }]
            })
            
            # 提取响应
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = str(result)
            
            # 尝试从响应中提取代码块
            code_blocks = self._extract_code_blocks(response)
            generated_code = code_blocks[0] if code_blocks else response
            
            return {
                "code": generated_code,
                "explanation": "Code generated using DeepAgent",
                "suggestions": ["Review the code", "Add tests", "Add documentation"]
            }
        
        except Exception as e:
            logger.exception("Error in generate_code")
            raise AgentError(str(e))
    
    def _extract_code_blocks(self, text: str) -> list:
        """从文本中提取代码块"""
        import re
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches]
    
    def explain_code(self, params: dict) -> dict:
        """
        解释代码 (委派给统一 Agent)
        
        统一 Agent 会自动使用 code-explainer subagent 处理
        
        参数:
            code: str - 要解释的代码
            language: str - 编程语言
        """
        code = params.get("code", "")
        language = params.get("language", "python")
        
        logger.info(f"Explain code request (language: {language})")
        
        try:
            if self.unified_agent is None:
                return {
                    "summary": f"[Fallback] {language} code",
                    "detailed_explanation": "Agent not initialized",
                    "key_concepts": [],
                    "complexity": "Unknown",
                    "potential_issues": []
                }
            
            # 调用统一 Agent（会自动委派给 code-explainer subagent）
            result = self.unified_agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"Please explain this {language} code:\n\n```{language}\n{code}\n```"
                }]
            })
            
            # 提取响应
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = str(result)
            
            return {
                "summary": response[:200] + "..." if len(response) > 200 else response,
                "detailed_explanation": response,
                "key_concepts": [],
                "complexity": "Analyzed by AI",
                "potential_issues": []
            }
        
        except Exception as e:
            logger.exception("Error in explain_code")
            raise AgentError(str(e))
    
    def refactor_code(self, params: dict) -> dict:
        """
        重构代码 (委派给统一 Agent)
        
        统一 Agent 会自动使用 refactoring subagent 处理
        
        参数:
            code: str - 要重构的代码
            language: str - 编程语言
            instructions: str - 重构说明
        """
        code = params.get("code", "")
        instructions = params.get("instructions", "")
        language = params.get("language", "python")
        
        logger.info(f"Refactor code request: {instructions}")
        
        try:
            if self.unified_agent is None:
                return {
                    "refactored_code": code + "\n# Refactored (fallback mode)",
                    "changes": [{"type": "none", "description": "Agent not initialized"}],
                    "diff": "N/A"
                }
            
            # 调用统一 Agent（会自动委派给 refactoring subagent）
            result = self.unified_agent.invoke({
                "messages": [{
                    "role": "user",
                    "content": f"""Please refactor this {language} code according to: {instructions}

Original code:
```{language}
{code}
```

Provide the refactored code and explain the changes."""
                }]
            })
            
            # 提取响应
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = str(result)
            
            # 提取重构后的代码
            code_blocks = self._extract_code_blocks(response)
            refactored = code_blocks[0] if code_blocks else code
            
            return {
                "refactored_code": refactored,
                "changes": [
                    {
                        "type": "refactoring",
                        "description": "Refactored by AI"
                    }
                ],
                "diff": response
            }
        
        except Exception as e:
            logger.exception("Error in refactor_code")
            raise AgentError(str(e))
    
    def review_code(self, params: dict) -> dict:
        """
        审查代码
        
        参数:
            code: str - 要审查的代码
            language: str - 编程语言
        """
        logger.info("Review code")
        
        return {
            "overall_score": 8,
            "issues": [
                {
                    "severity": "low",
                    "message": "建议添加类型注解",
                    "line": 5
                }
            ],
            "suggestions": ["添加文档字符串", "改进命名"],
            "summary": "代码质量良好，有一些改进空间。"
        }
    
    def search_code(self, params: dict) -> dict:
        """
        搜索代码
        
        参数:
            query: str - 搜索查询
            workspace_root: str - 工作区根目录
        """
        query = params.get("query", "")
        
        logger.info(f"Search code: {query}")
        
        return {
            "results": [],
            "total_matches": 0,
            "message": "代码搜索功能待实现"
        }
    
    def shutdown(self, params: dict) -> dict:
        """优雅关闭"""
        logger.info("Shutdown requested")
        self.rpc_server.stop()
        return {"status": "shutting down"}
    
    def run(self):
        """启动服务器"""
        logger.info(f"Starting Agent Server (workspace: {self.workspace_root})")
        self.rpc_server.run()


def main():
    """主函数"""
    # 从环境变量读取配置
    workspace_root = os.environ.get("WORKSPACE_ROOT", os.getcwd())
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    
    # 配置日志（输出到 stderr）
    setup_logger(log_level)
    
    logger.info("=" * 60)
    logger.info("Vibe Coding Agent Server")
    logger.info("=" * 60)
    logger.info(f"Workspace: {workspace_root}")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Python: {sys.version}")
    logger.info("=" * 60)
    
    # 创建并启动服务器
    server = AgentServer(workspace_root)
    
    try:
        server.run()
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)
    
    logger.info("Server exited")


if __name__ == "__main__":
    main()

