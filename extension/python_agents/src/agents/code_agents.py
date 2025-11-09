"""
代码助手工具
提供自定义工具给 unified agent 使用
"""
import logging
from typing import List, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def create_custom_tools(
    ast_tools: Any = None,
) -> List:
    """
    创建自定义工具（仅包含 deepagents 未提供的功能）
    
    注意：deepagents 已经通过 FilesystemMiddleware 自动提供了：
    - ls: 列出文件
    - read_file: 读取文件（支持行范围）
    - write_file: 写入文件
    - edit_file: 编辑文件（搜索替换）
    - grep_search: 正则表达式搜索
    - glob_search: glob 模式搜索
    
    这里只添加 deepagents 未提供的工具（如代码分析）
    """
    tools = []
    
    # 分析 Python 代码结构工具
    @tool
    def analyze_python_code(code: str) -> str:
        """
        分析 Python 代码结构（函数、类、导入等）
        
        这是一个额外的代码分析工具，deepagents 没有提供类似功能。
        
        Args:
            code: Python 源代码
            
        Returns:
            代码结构分析结果（导入、类、函数）
        """
        try:
            if ast_tools:
                functions = ast_tools.extract_functions(code)
                classes = ast_tools.extract_classes(code)
                imports = ast_tools.extract_imports(code)
                
                result = []
                
                if imports:
                    result.append("Imports:")
                    for imp in imports:
                        result.append(f"  - {imp.module}: {', '.join(imp.names)}")
                
                if classes:
                    result.append("\nClasses:")
                    for cls in classes:
                        result.append(f"  - {cls.name} (line {cls.line})")
                        for method in cls.methods:
                            result.append(f"    - {method.name}({', '.join(method.args)})")
                
                if functions:
                    result.append("\nFunctions:")
                    for func in functions:
                        result.append(f"  - {func.name}({', '.join(func.args)}) at line {func.line}")
                
                return "\n".join(result) if result else "No structure found"
            return "Error: AST tools not available"
        except Exception as e:
            return f"Error analyzing code: {str(e)}"
    
    # 分析代码复杂度工具
    @tool
    def analyze_code_complexity(code: str) -> str:
        """
        分析代码复杂度
        
        Args:
            code: Python 源代码
            
        Returns:
            复杂度分析结果
        """
        try:
            if ast_tools:
                complexity = ast_tools.analyze_complexity(code)
                
                result = []
                result.append("Code Complexity Analysis:")
                result.append(f"  - Total functions: {complexity.get('total_functions', 0)}")
                result.append(f"  - Total classes: {complexity.get('total_classes', 0)}")
                result.append(f"  - Average complexity: {complexity.get('avg_complexity', 0)}")
                
                if complexity.get('complex_functions'):
                    result.append("\nComplex functions (>10 complexity):")
                    for func in complexity['complex_functions']:
                        result.append(f"  - {func['name']}: {func['complexity']}")
                
                return "\n".join(result)
            return "Error: AST tools not available"
        except Exception as e:
            return f"Error analyzing complexity: {str(e)}"
    
    if ast_tools:
        tools.extend([
            analyze_python_code,
            analyze_code_complexity,
        ])
    
    return tools
