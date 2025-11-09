"""
安全检查模块
提供文件路径验证、命令白名单等安全功能
"""
import os
import re
import psutil
import logging
from pathlib import Path
from typing import List, Optional, Dict
from fnmatch import fnmatch

logger = logging.getLogger(__name__)


class SecurityChecker:
    """安全检查器"""
    
    # 文件访问黑名单
    FORBIDDEN_PATTERNS = [
        '**/.git/**',
        '**/.env',
        '**/.env.*',
        '**/id_rsa',
        '**/id_rsa.*',
        '**/.ssh/**',
        '**/secrets.json',
        '**/credentials*',
        '**/token*',
        '**/*.key',
        '**/*.pem',
        '**/*.pfx',
        '**/config/secrets/**',
    ]
    
    # 命令白名单
    ALLOWED_COMMANDS = {
        'git': ['status', 'diff', 'log', 'show', 'branch', 'remote'],
        'python': ['-m', 'pytest', '-m', 'mypy', '-m', 'pip', 'list', '--version'],
        'node': ['--version', '-v'],
        'npm': ['list', 'outdated', '--version'],
        'pnpm': ['list', '--version'],
        'yarn': ['list', '--version'],
        'ruff': ['check', 'format', '--version'],
        'black': ['--check', '--version'],
        'mypy': ['--version'],
        'pytest': ['--version'],
    }
    
    # 资源限制
    MAX_MEMORY_MB = 500
    MAX_FILE_SIZE_MB = 10
    MAX_EXECUTION_TIME = 30
    
    def __init__(self, workspace_root: str):
        """
        初始化安全检查器
        
        Args:
            workspace_root: 工作区根目录
        """
        self.workspace_root = Path(workspace_root).resolve()
        logger.info(f"SecurityChecker initialized for workspace: {self.workspace_root}")
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        验证文件路径是否安全
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否安全
            
        Raises:
            SecurityError: 路径不安全时
        """
        # 转换为绝对路径
        if Path(file_path).is_absolute():
            abs_path = Path(file_path).resolve()
        else:
            abs_path = (self.workspace_root / file_path).resolve()
        
        # 确保路径在工作区内
        try:
            abs_path.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(f"Access denied: path outside workspace: {file_path}")
        
        # 黑名单检查
        path_str = str(abs_path)
        for pattern in self.FORBIDDEN_PATTERNS:
            if fnmatch(path_str, pattern) or fnmatch(file_path, pattern):
                raise SecurityError(f"Access denied: sensitive file: {file_path}")
        
        # 检查是否为隐藏文件（以点开头）
        if any(part.startswith('.') for part in abs_path.parts[len(self.workspace_root.parts):]):
            raise SecurityError(f"Access denied: hidden file: {file_path}")
        
        return True
    
    def validate_command(self, command: List[str]) -> bool:
        """
        验证命令是否在白名单中
        
        Args:
            command: 命令列表 ['git', 'status']
            
        Returns:
            是否安全
            
        Raises:
            SecurityError: 命令不在白名单时
        """
        if not command:
            raise SecurityError("Empty command")
        
        program = command[0]
        
        # 检查程序是否在白名单
        if program not in self.ALLOWED_COMMANDS:
            raise SecurityError(f"Command not allowed: {program}")
        
        # 检查子命令
        if len(command) > 1:
            allowed_subcmds = self.ALLOWED_COMMANDS[program]
            subcommand = command[1]
            
            # 检查子命令是否匹配允许的模式
            if not any(subcommand == allowed or subcommand.startswith(allowed + ' ') 
                      for allowed in allowed_subcmds):
                raise SecurityError(f"Subcommand not allowed: {program} {subcommand}")
        
        return True
    
    def check_memory_usage(self) -> Dict[str, float]:
        """
        检查当前进程的内存使用
        
        Returns:
            内存使用信息 {"memory_mb": float, "memory_percent": float}
            
        Raises:
            ResourceError: 内存超限时
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            if memory_mb > self.MAX_MEMORY_MB:
                raise ResourceError(
                    f"Memory limit exceeded: {memory_mb:.1f}MB / {self.MAX_MEMORY_MB}MB"
                )
            
            return {
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2)
            }
        except psutil.Error as e:
            logger.warning(f"Failed to check memory usage: {e}")
            return {"memory_mb": 0, "memory_percent": 0}
    
    def check_file_size(self, file_path: str) -> bool:
        """
        检查文件大小是否超限
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否在限制内
            
        Raises:
            ResourceError: 文件过大时
        """
        abs_path = self.workspace_root / file_path
        
        if not abs_path.exists():
            return True
        
        size_mb = abs_path.stat().st_size / 1024 / 1024
        
        if size_mb > self.MAX_FILE_SIZE_MB:
            raise ResourceError(
                f"File too large: {size_mb:.1f}MB / {self.MAX_FILE_SIZE_MB}MB"
            )
        
        return True
    
    def sanitize_input(self, text: str) -> str:
        """
        清理用户输入
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        # 移除控制字符（保留换行和制表符）
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # 限制长度
        MAX_INPUT_LENGTH = 100000  # 100K 字符
        if len(text) > MAX_INPUT_LENGTH:
            logger.warning(f"Input truncated from {len(text)} to {MAX_INPUT_LENGTH} chars")
            text = text[:MAX_INPUT_LENGTH]
        
        return text
    
    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """
        验证 API Key 格式
        
        Args:
            api_key: API Key
            
        Returns:
            是否有效
        """
        if not api_key:
            return False
        
        # 基本格式检查
        if len(api_key) < 10:
            return False
        
        # 检查是否只包含合法字符
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key):
            return False
        
        return True
    
    def is_safe_workspace(self) -> bool:
        """
        检查工作区是否安全
        
        Returns:
            工作区是否安全
        """
        # 检查是否为系统目录
        system_dirs = [
            '/etc',
            '/bin',
            '/sbin',
            '/usr/bin',
            '/usr/sbin',
            '/System',
            '/Library',
            'C:\\Windows',
            'C:\\Program Files',
        ]
        
        workspace_str = str(self.workspace_root).lower()
        
        for sys_dir in system_dirs:
            if workspace_str.startswith(sys_dir.lower()):
                logger.error(f"Unsafe workspace: {self.workspace_root}")
                return False
        
        return True


class SecurityError(Exception):
    """安全错误"""
    pass


class ResourceError(Exception):
    """资源错误"""
    pass

