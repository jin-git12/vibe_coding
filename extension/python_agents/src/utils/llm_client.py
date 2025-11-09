"""
LLM 客户端
支持多种 LLM 提供商（主要是 Qwen/DashScope）
"""
import os
import logging
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "dashscope"  # dashscope, openai, ollama
    model: str = "qwen-max"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    stream: bool = False


class LLMClient:
    """LLM 客户端封装"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化 LLM 客户端
        
        Args:
            config: LLM 配置
        """
        self.config = config or self._load_default_config()
        self._client = None
        self._initialize_client()
        
        logger.info(f"LLMClient initialized: {self.config.provider}/{self.config.model}")
    
    def _load_default_config(self) -> LLMConfig:
        """从环境变量加载默认配置"""
        return LLMConfig(
            provider=os.environ.get("LLM_PROVIDER", "dashscope"),
            model=os.environ.get("LLM_MODEL", "qwen-max"),
            api_key=os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            api_base=os.environ.get("LLM_API_BASE"),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4000")),
        )
    
    def _initialize_client(self):
        """初始化底层 LLM 客户端"""
        if self.config.provider == "dashscope":
            self._initialize_dashscope()
        elif self.config.provider == "openai":
            self._initialize_openai()
        else:
            logger.warning(f"Unknown LLM provider: {self.config.provider}, using mock client")
            self._client = None
    
    def _initialize_dashscope(self):
        """初始化 DashScope (Qwen) 客户端"""
        try:
            from langchain_openai import ChatOpenAI
            
            # DashScope 使用 OpenAI 兼容接口
            self._client = ChatOpenAI(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            logger.info("DashScope client initialized")
        except ImportError:
            logger.error("langchain-openai not installed")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize DashScope client: {e}")
            self._client = None
    
    def _initialize_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            from langchain_openai import ChatOpenAI
            
            self._client = ChatOpenAI(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("langchain-openai not installed")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._client = None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            stream: 是否流式响应
            
        Returns:
            AI 响应文本
        """
        if self._client is None:
            return self._mock_response(messages)
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            # 转换消息格式
            lc_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:  # user
                    lc_messages.append(HumanMessage(content=content))
            
            # 调用 LLM
            if stream:
                # 流式响应
                response_chunks = []
                for chunk in self._client.stream(lc_messages):
                    content = chunk.content
                    response_chunks.append(content)
                    yield content
                
                return "".join(response_chunks)
            else:
                # 非流式响应
                response = self._client.invoke(lc_messages)
                return response.content
        
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise LLMError(f"LLM request failed: {e}")
    
    def chat_stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """
        流式聊天请求
        
        Args:
            messages: 消息列表
            
        Yields:
            AI 响应的每个片段
        """
        if self._client is None:
            yield self._mock_response(messages)
            return
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            # 转换消息格式
            lc_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(HumanMessage(content=content))
            
            # 流式调用
            for chunk in self._client.stream(lc_messages):
                if chunk.content:
                    yield chunk.content
        
        except Exception as e:
            logger.error(f"LLM stream request failed: {e}")
            raise LLMError(f"LLM stream request failed: {e}")
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """模拟响应（用于测试或无客户端时）"""
        last_message = messages[-1]["content"] if messages else "Hello"
        return f"[Mock Response] 收到您的消息: {last_message[:100]}...\n\n这是一个模拟响应，因为 LLM 客户端未正确配置。"
    
    def is_available(self) -> bool:
        """检查 LLM 客户端是否可用"""
        return self._client is not None


class LLMError(Exception):
    """LLM 错误"""
    pass


# 全局 LLM 客户端实例
_global_client: Optional[LLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """
    获取全局 LLM 客户端实例
    
    Args:
        config: LLM 配置（首次调用时使用）
        
    Returns:
        LLM 客户端实例
    """
    global _global_client
    
    if _global_client is None:
        _global_client = LLMClient(config)
    
    return _global_client

