"""
配置管理
从环境变量和文件加载配置
"""
import os
import logging
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# 🔧 加载 .env 文件（开发时使用）
try:
    from dotenv import load_dotenv
    # 只在开发模式或者 .env 存在时加载
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.debug(f"Loaded environment from {env_file}")
except ImportError:
    logger.debug("python-dotenv not installed, skipping .env file")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")


@dataclass
class Settings:
    """全局配置"""
    
    # 工作区配置
    workspace_root: str = field(default_factory=os.getcwd)
    workspace_dir: Optional[str] = None  # Agent 生成文件的目标目录，默认为 workspace_root/workspace
    
    # LLM 配置
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-turbo"  # 默认模型改为 qwen-turbo（更快）
    llm_api_key: Optional[str] = None
    llm_api_base: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    
    # 开发模式（仅用于调试）
    dev_mode: bool = False
    
    # Agent 配置
    agent_timeout: int = 30  # 秒
    agent_max_retries: int = 3
    agent_enable_cache: bool = True
    
    # 安全配置
    max_file_size_mb: int = 10
    max_memory_mb: int = 500
    enable_security_checks: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    
    # 功能开关
    enable_streaming: bool = True
    enable_tools: bool = True
    enable_code_execution: bool = False  # 默认关闭代码执行
    
    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量加载配置"""
        # 检查是否为开发模式
        dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
        
        # 开发模式默认 API Key（仅用于调试）
        dev_api_key = "sk-3f1a10e54780416f939f2542b6abbad9" if dev_mode else None
        
        return cls(
            workspace_root=os.environ.get("WORKSPACE_ROOT", os.getcwd()),
            workspace_dir=os.environ.get("WORKSPACE_DIR"),  # 如果未设置，将使用默认路径
            
            # LLM
            llm_provider=os.environ.get("LLM_PROVIDER", "dashscope"),
            llm_model=os.environ.get("LLM_MODEL", "qwen-turbo"),  # 默认使用 qwen-turbo
            llm_api_key=os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY") or dev_api_key,
            llm_api_base=os.environ.get("LLM_API_BASE"),
            llm_temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4000")),
            
            # 开发模式标志
            dev_mode=dev_mode,
            
            # Agent
            agent_timeout=int(os.environ.get("AGENT_TIMEOUT", "30")),
            agent_max_retries=int(os.environ.get("AGENT_MAX_RETRIES", "3")),
            agent_enable_cache=os.environ.get("AGENT_ENABLE_CACHE", "true").lower() == "true",
            
            # 安全
            max_file_size_mb=int(os.environ.get("MAX_FILE_SIZE_MB", "10")),
            max_memory_mb=int(os.environ.get("MAX_MEMORY_MB", "500")),
            enable_security_checks=os.environ.get("ENABLE_SECURITY_CHECKS", "true").lower() == "true",
            
            # 日志
            log_level=os.environ.get("LOG_LEVEL", "DEBUG" if dev_mode else "INFO"),
            log_to_file=os.environ.get("LOG_TO_FILE", "false").lower() == "true",
            log_file_path=os.environ.get("LOG_FILE_PATH"),
            
            # 功能开关
            enable_streaming=os.environ.get("ENABLE_STREAMING", "true").lower() == "true",
            enable_tools=os.environ.get("ENABLE_TOOLS", "true").lower() == "true",
            enable_code_execution=os.environ.get("ENABLE_CODE_EXECUTION", "false").lower() == "true",
        )
    
    def get_workspace_dir(self) -> Path:
        """
        获取实际的 workspace 目录路径
        
        如果 workspace_dir 已设置，直接使用；
        否则使用 workspace_root/workspace 作为默认路径
        
        Returns:
            Path: workspace 目录的绝对路径
        """
        if self.workspace_dir:
            # 使用配置的路径
            workspace_path = Path(self.workspace_dir)
            # 如果是相对路径，相对于 workspace_root 解析
            if not workspace_path.is_absolute():
                workspace_path = Path(self.workspace_root) / workspace_path
            return workspace_path.resolve()
        else:
            # 默认：workspace_root/workspace
            return (Path(self.workspace_root) / "workspace").resolve()
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        issues = []
        
        # 检查工作区
        if not Path(self.workspace_root).exists():
            issues.append(f"Workspace does not exist: {self.workspace_root}")
        
        # 检查 API Key（开发模式下会自动提供）
        if not self.llm_api_key:
            if self.dev_mode:
                logger.warning("⚠️  Development mode: using built-in test API key")
            else:
                issues.append("LLM API key is not set")
        
        # 检查数值范围
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            issues.append(f"Invalid temperature: {self.llm_temperature} (must be 0-2)")
        
        if self.llm_max_tokens < 1:
            issues.append(f"Invalid max_tokens: {self.llm_max_tokens}")
        
        if self.dev_mode:
            logger.info("🔧 Development mode enabled - using test configuration")
        
        if issues:
            for issue in issues:
                logger.error(f"Configuration error: {issue}")
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "workspace_root": self.workspace_root,
            "workspace_dir": str(self.get_workspace_dir()),  # 显示实际使用的路径
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "agent_timeout": self.agent_timeout,
            "agent_max_retries": self.agent_max_retries,
            "agent_enable_cache": self.agent_enable_cache,
            "max_file_size_mb": self.max_file_size_mb,
            "max_memory_mb": self.max_memory_mb,
            "enable_security_checks": self.enable_security_checks,
            "log_level": self.log_level,
            "enable_streaming": self.enable_streaming,
            "enable_tools": self.enable_tools,
            "enable_code_execution": self.enable_code_execution,
        }
    
    def __repr__(self) -> str:
        """字符串表示（隐藏敏感信息）"""
        safe_dict = self.to_dict()
        return f"Settings({safe_dict})"


# 全局配置实例
_global_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例
    
    Returns:
        Settings 实例
    """
    global _global_settings
    
    if _global_settings is None:
        _global_settings = Settings.from_env()
        logger.info("Settings loaded from environment")
        
        # 验证配置
        if not _global_settings.validate():
            logger.warning("Configuration validation failed, but continuing...")
    
    return _global_settings


def reset_settings():
    """重置全局配置（用于测试）"""
    global _global_settings
    _global_settings = None

