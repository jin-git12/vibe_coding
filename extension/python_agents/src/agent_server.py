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
from agents import (
    create_custom_tools,
    create_code_generator_agent,
    create_chat_agent,
    create_code_explainer_agent,
    create_refactoring_agent,
)
from tools import ASTTools


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
                logger.warning("LLM client not available, agents will use fallback mode")
                self.code_generator = None
                self.chat_agent = None
                self.code_explainer = None
                self.refactoring_agent = None
                return
            
            llm = self.llm_client._client
            
            # 创建各种 Agent (直接使用 create_deep_agent)
            self.code_generator = create_code_generator_agent(llm, self.custom_tools)
            logger.info("✓ Code generator agent created")
            
            self.chat_agent = create_chat_agent(llm, self.custom_tools)
            logger.info("✓ Chat agent created")
            
            self.code_explainer = create_code_explainer_agent(llm, self.custom_tools)
            logger.info("✓ Code explainer agent created")
            
            self.refactoring_agent = create_refactoring_agent(llm, self.custom_tools)
            logger.info("✓ Refactoring agent created")
            
            logger.info("All deep agents initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize deep agents: {e}")
            import traceback
            traceback.print_exc()
            # 降级到无 Agent 模式
            self.code_generator = None
            self.chat_agent = None
            self.code_explainer = None
            self.refactoring_agent = None
    
    def register_methods(self):
        """注册所有 RPC 方法"""
        self.rpc_server.register_method("health_check", self.health_check)
        self.rpc_server.register_method("chat", self.chat)
        self.rpc_server.register_method("generate_code", self.generate_code)
        self.rpc_server.register_method("explain_code", self.explain_code)
        self.rpc_server.register_method("refactor_code", self.refactor_code)
        self.rpc_server.register_method("review_code", self.review_code)
        self.rpc_server.register_method("search_code", self.search_code)
        self.rpc_server.register_method("shutdown", self.shutdown)
    
    def health_check(self, params: dict) -> dict:
        """健康检查"""
        logger.debug("Health check called")
        return {
            "status": "ok",
            "workspace": self.workspace_root,
            "methods": list(self.rpc_server.methods.keys())
        }
    
    def chat(self, params: dict) -> dict:
        """
        AI 聊天 (使用 DeepAgent)
        
        参数:
            message: str - 用户消息
            conversation_id: str - 会话 ID（可选）
            context: dict - 上下文信息（可选）
            stream: bool - 是否流式响应（可选）
        """
        logger.info(f"Chat request: {params.get('message', '')[:50]}...")
        
        try:
            if self.chat_agent is None:
                # 降级模式：返回模拟响应
                return {
                    "conversation_id": params.get("conversation_id", "default"),
                    "full_response": f"[Fallback Mode] Received: {params.get('message', '')}",
                    "suggestions": []
                }
            
            # 调用 DeepAgent (正确方式)
            result = self.chat_agent.invoke({
                "messages": [{"role": "user", "content": params.get("message", "")}]
            })
            
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
        生成代码 (使用 DeepAgent)
        
        参数:
            prompt: str - 生成提示
            language: str - 编程语言
            context: dict - 上下文信息（可选）
            options: dict - 生成选项（可选）
        """
        prompt = params.get('prompt', '')
        language = params.get('language', 'python')
        logger.info(f"Generate code: {prompt[:50]}... (language: {language})")
        
        try:
            if self.code_generator is None:
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
            
            # 调用 DeepAgent (正确方式)
            result = self.code_generator.invoke({
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
        解释代码 (使用 DeepAgent)
        
        参数:
            code: str - 要解释的代码
            language: str - 编程语言
        """
        code = params.get("code", "")
        language = params.get("language", "python")
        
        logger.info(f"Explain code (language: {language})")
        
        try:
            if self.code_explainer is None:
                return {
                    "summary": f"[Fallback] {language} code",
                    "detailed_explanation": "LLM not configured for code explanation",
                    "key_concepts": [],
                    "complexity": "Unknown",
                    "potential_issues": []
                }
            
            # 调用 DeepAgent (正确方式)
            result = self.code_explainer.invoke({
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
        重构代码 (使用 DeepAgent)
        
        参数:
            code: str - 要重构的代码
            language: str - 编程语言
            instructions: str - 重构说明
        """
        code = params.get("code", "")
        instructions = params.get("instructions", "")
        language = params.get("language", "python")
        
        logger.info(f"Refactor code: {instructions}")
        
        try:
            if self.refactoring_agent is None:
                return {
                    "refactored_code": code + "\n# Refactored (fallback mode)",
                    "changes": [{"type": "none", "description": "LLM not configured"}],
                    "diff": "N/A"
                }
            
            # 调用 DeepAgent (正确方式)
            result = self.refactoring_agent.invoke({
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

