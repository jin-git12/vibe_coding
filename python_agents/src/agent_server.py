"""
Agent 服务器主入口
启动 JSON-RPC 服务器并注册 Agent 方法
"""
import os
import sys
import logging
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from rpc import JSONRPCServer, AgentError, LLMError
from utils import setup_logger


logger = logging.getLogger(__name__)


class AgentServer:
    """Agent 服务器"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.rpc_server = JSONRPCServer()
        self.register_methods()
    
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
        AI 聊天
        
        参数:
            message: str - 用户消息
            conversation_id: str - 会话 ID（可选）
            stream: bool - 是否流式响应（可选）
        """
        message = params.get("message", "")
        conversation_id = params.get("conversation_id")
        stream = params.get("stream", False)
        
        logger.info(f"Chat request: {message[:50]}...")
        
        try:
            # 这里应该调用实际的 Agent
            # 目前返回模拟响应
            response = f"我收到了你的消息: {message}\n\n这是一个模拟的 AI 回复。后续会集成真实的 deepagents 和 Qwen LLM。"
            
            if stream:
                # 模拟流式响应
                chunks = response.split("。")
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        self.rpc_server.send_notification("chat.stream", {
                            "conversation_id": conversation_id,
                            "chunk": chunk + "。",
                            "done": i == len(chunks) - 1
                        })
            
            return {
                "conversation_id": conversation_id or "default",
                "full_response": response,
                "suggestions": []
            }
        
        except Exception as e:
            logger.exception("Error in chat")
            raise AgentError(str(e))
    
    def generate_code(self, params: dict) -> dict:
        """
        生成代码
        
        参数:
            prompt: str - 生成提示
            language: str - 编程语言
            context: dict - 上下文信息（可选）
        """
        prompt = params.get("prompt", "")
        language = params.get("language", "python")
        
        logger.info(f"Generate code: {prompt[:50]}... (language: {language})")
        
        # 模拟代码生成
        code = f"""# Generated code for: {prompt}
def example_function():
    \"\"\"This is a placeholder. Real implementation will use deepagents + Qwen.\"\"\"
    pass
"""
        
        return {
            "code": code,
            "explanation": "这是一个模拟生成的代码示例。",
            "suggestions": ["添加错误处理", "编写单元测试"]
        }
    
    def explain_code(self, params: dict) -> dict:
        """
        解释代码
        
        参数:
            code: str - 要解释的代码
            language: str - 编程语言
        """
        code = params.get("code", "")
        language = params.get("language", "python")
        
        logger.info(f"Explain code (language: {language})")
        
        return {
            "summary": "代码摘要",
            "detailed_explanation": f"这段 {language} 代码的详细解释...",
            "key_concepts": ["概念1", "概念2"],
            "complexity": "O(n)",
            "potential_issues": []
        }
    
    def refactor_code(self, params: dict) -> dict:
        """
        重构代码
        
        参数:
            code: str - 要重构的代码
            language: str - 编程语言
            instructions: str - 重构说明
        """
        code = params.get("code", "")
        instructions = params.get("instructions", "")
        
        logger.info(f"Refactor code: {instructions}")
        
        return {
            "refactored_code": code + "\n# Refactored version (placeholder)",
            "changes": [
                {
                    "type": "improvement",
                    "description": "改进代码结构"
                }
            ],
            "diff": "placeholder diff"
        }
    
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

