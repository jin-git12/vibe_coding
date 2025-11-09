"""
上下文构建器
为 Agent 构建丰富的上下文信息
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextBuilder:
    """上下文构建器"""
    
    def __init__(self, workspace_root: str):
        """
        初始化上下文构建器
        
        Args:
            workspace_root: 工作区根目录
        """
        self.workspace_root = Path(workspace_root).resolve()
        logger.info(f"ContextBuilder initialized with workspace: {self.workspace_root}")
    
    def build_context(
        self,
        current_file: Optional[str] = None,
        selected_code: Optional[str] = None,
        cursor_position: Optional[Dict[str, int]] = None,
        include_workspace_info: bool = True,
        include_related_files: bool = False
    ) -> Dict[str, Any]:
        """
        构建完整的上下文信息
        
        Args:
            current_file: 当前文件路径
            selected_code: 选中的代码
            cursor_position: 光标位置 {"line": 10, "column": 5}
            include_workspace_info: 是否包含工作区信息
            include_related_files: 是否包含相关文件
            
        Returns:
            上下文字典
        """
        context = {}
        
        # 当前文件信息
        if current_file:
            context["current_file"] = {
                "path": current_file,
                "language": self._detect_language(current_file),
                "exists": (self.workspace_root / current_file).exists()
            }
            
            # 如果文件存在，读取内容
            if context["current_file"]["exists"]:
                try:
                    file_content = (self.workspace_root / current_file).read_text(encoding='utf-8')
                    context["current_file"]["content"] = file_content
                    context["current_file"]["line_count"] = len(file_content.split('\n'))
                except Exception as e:
                    logger.warning(f"Failed to read file {current_file}: {e}")
        
        # 选中的代码
        if selected_code:
            context["selected_code"] = {
                "content": selected_code,
                "line_count": len(selected_code.split('\n'))
            }
        
        # 光标位置
        if cursor_position:
            context["cursor_position"] = cursor_position
            
            # 如果有当前文件和光标位置，提取周围代码
            if current_file and "current_file" in context:
                surrounding = self._get_surrounding_code(
                    context["current_file"].get("content", ""),
                    cursor_position.get("line", 0)
                )
                if surrounding:
                    context["surrounding_code"] = surrounding
        
        # 工作区信息
        if include_workspace_info:
            context["workspace"] = self._get_workspace_info()
        
        # 相关文件
        if include_related_files and current_file:
            context["related_files"] = self._find_related_files(current_file)
        
        return context
    
    def _detect_language(self, file_path: str) -> str:
        """
        检测文件的编程语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            语言名称
        """
        extension_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.tsx': 'typescriptreact',
            '.js': 'javascript',
            '.jsx': 'javascriptreact',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'objective-c',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.ps1': 'powershell',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
        }
        
        suffix = Path(file_path).suffix.lower()
        return extension_map.get(suffix, 'plaintext')
    
    def _get_surrounding_code(
        self,
        file_content: str,
        line_number: int,
        context_lines: int = 10
    ) -> Dict[str, Any]:
        """
        获取光标周围的代码
        
        Args:
            file_content: 文件内容
            line_number: 行号（1-based）
            context_lines: 上下文行数
            
        Returns:
            周围代码信息
        """
        if not file_content:
            return {}
        
        lines = file_content.split('\n')
        total_lines = len(lines)
        
        # 确保行号有效
        if line_number < 1 or line_number > total_lines:
            return {}
        
        # 计算范围（转换为 0-based）
        start = max(0, line_number - context_lines - 1)
        end = min(total_lines, line_number + context_lines)
        
        return {
            "start_line": start + 1,  # 转回 1-based
            "end_line": end,
            "content": '\n'.join(lines[start:end]),
            "cursor_line": line_number
        }
    
    def _get_workspace_info(self) -> Dict[str, Any]:
        """
        获取工作区信息
        
        Returns:
            工作区信息字典
        """
        info = {
            "root": str(self.workspace_root),
            "name": self.workspace_root.name
        }
        
        # 检测项目类型
        project_types = []
        
        if (self.workspace_root / "package.json").exists():
            project_types.append("node")
        if (self.workspace_root / "pyproject.toml").exists() or (self.workspace_root / "setup.py").exists():
            project_types.append("python")
        if (self.workspace_root / "pom.xml").exists():
            project_types.append("java")
        if (self.workspace_root / "Cargo.toml").exists():
            project_types.append("rust")
        if (self.workspace_root / "go.mod").exists():
            project_types.append("go")
        
        info["project_types"] = project_types
        
        # 统计文件数量（仅主要文件类型）
        try:
            file_counts = {}
            for extension in ['.py', '.ts', '.js', '.java', '.go', '.rs']:
                count = len(list(self.workspace_root.rglob(f'*{extension}')))
                if count > 0:
                    file_counts[extension] = count
            
            info["file_counts"] = file_counts
        except Exception as e:
            logger.warning(f"Failed to count files: {e}")
        
        return info
    
    def _find_related_files(self, current_file: str, max_files: int = 5) -> List[str]:
        """
        查找相关文件
        
        Args:
            current_file: 当前文件路径
            max_files: 最大文件数
            
        Returns:
            相关文件路径列表
        """
        related = []
        current_path = Path(current_file)
        
        try:
            # 1. 同目录下的文件
            parent_dir = current_path.parent
            if parent_dir != Path('.'):
                abs_parent = self.workspace_root / parent_dir
                if abs_parent.exists():
                    for file in abs_parent.iterdir():
                        if file.is_file() and file.suffix == current_path.suffix:
                            if file.name != current_path.name:
                                rel_path = file.relative_to(self.workspace_root)
                                related.append(str(rel_path))
                                if len(related) >= max_files:
                                    break
            
            # 2. __init__.py 或 index.ts 等入口文件
            if len(related) < max_files:
                entry_files = ['__init__.py', 'index.ts', 'index.js', 'main.py']
                for entry in entry_files:
                    entry_path = self.workspace_root / parent_dir / entry
                    if entry_path.exists():
                        rel_path = entry_path.relative_to(self.workspace_root)
                        path_str = str(rel_path)
                        if path_str not in related:
                            related.append(path_str)
        
        except Exception as e:
            logger.warning(f"Failed to find related files: {e}")
        
        return related[:max_files]
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        将上下文格式化为 Prompt
        
        Args:
            context: 上下文字典
            
        Returns:
            格式化的上下文文本
        """
        parts = []
        
        # 当前文件
        if "current_file" in context:
            file_info = context["current_file"]
            parts.append(f"## Current File: {file_info['path']}")
            parts.append(f"Language: {file_info['language']}")
            
            if "line_count" in file_info:
                parts.append(f"Lines: {file_info['line_count']}")
        
        # 选中的代码
        if "selected_code" in context:
            parts.append("\n## Selected Code:")
            parts.append("```" + context.get("current_file", {}).get("language", ""))
            parts.append(context["selected_code"]["content"])
            parts.append("```")
        
        # 周围代码
        elif "surrounding_code" in context:
            surrounding = context["surrounding_code"]
            parts.append(f"\n## Code Context (lines {surrounding['start_line']}-{surrounding['end_line']}):")
            parts.append("```" + context.get("current_file", {}).get("language", ""))
            parts.append(surrounding["content"])
            parts.append("```")
            parts.append(f"(Cursor at line {surrounding['cursor_line']})")
        
        # 工作区信息
        if "workspace" in context:
            ws = context["workspace"]
            parts.append(f"\n## Workspace: {ws['name']}")
            if ws.get("project_types"):
                parts.append(f"Project types: {', '.join(ws['project_types'])}")
        
        return '\n'.join(parts)

