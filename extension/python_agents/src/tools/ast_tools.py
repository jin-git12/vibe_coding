"""
AST 分析工具
提供代码结构分析功能
"""
import ast
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    line: int
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    line: int
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    names: List[str]
    alias: Optional[str] = None
    line: int = 0


@dataclass
class CodeMetrics:
    """代码度量"""
    lines_of_code: int
    comment_lines: int
    blank_lines: int
    functions: int
    classes: int
    complexity: int  # 圈复杂度估算


class ASTTools:
    """AST 分析工具集"""
    
    def __init__(self):
        """初始化 AST 工具"""
        logger.info("ASTTools initialized")
    
    def parse_code(self, code: str, language: str = "python") -> Optional[ast.AST]:
        """
        解析代码为 AST
        
        Args:
            code: 源代码
            language: 编程语言（目前仅支持 Python）
            
        Returns:
            AST 根节点，解析失败返回 None
        """
        if language != "python":
            logger.warning(f"Unsupported language for AST: {language}")
            return None
        
        try:
            return ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return None
    
    def extract_functions(self, code: str) -> List[FunctionInfo]:
        """
        提取代码中的函数
        
        Args:
            code: 源代码
            
        Returns:
            函数信息列表
        """
        tree = self.parse_code(code)
        if tree is None:
            return []
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 提取参数
                args = [arg.arg for arg in node.args.args]
                
                # 提取返回类型
                returns = None
                if node.returns:
                    returns = ast.unparse(node.returns)
                
                # 提取文档字符串
                docstring = ast.get_docstring(node)
                
                # 提取装饰器
                decorators = [ast.unparse(dec) for dec in node.decorator_list]
                
                functions.append(FunctionInfo(
                    name=node.name,
                    line=node.lineno,
                    args=args,
                    returns=returns,
                    docstring=docstring,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    decorators=decorators
                ))
        
        return functions
    
    def extract_classes(self, code: str) -> List[ClassInfo]:
        """
        提取代码中的类
        
        Args:
            code: 源代码
            
        Returns:
            类信息列表
        """
        tree = self.parse_code(code)
        if tree is None:
            return []
        
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 提取基类
                bases = [ast.unparse(base) for base in node.bases]
                
                # 提取方法
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [arg.arg for arg in item.args.args]
                        returns = ast.unparse(item.returns) if item.returns else None
                        docstring = ast.get_docstring(item)
                        decorators = [ast.unparse(dec) for dec in item.decorator_list]
                        
                        methods.append(FunctionInfo(
                            name=item.name,
                            line=item.lineno,
                            args=args,
                            returns=returns,
                            docstring=docstring,
                            is_async=isinstance(item, ast.AsyncFunctionDef),
                            decorators=decorators
                        ))
                
                # 提取文档字符串
                docstring = ast.get_docstring(node)
                
                # 提取装饰器
                decorators = [ast.unparse(dec) for dec in node.decorator_list]
                
                classes.append(ClassInfo(
                    name=node.name,
                    line=node.lineno,
                    bases=bases,
                    methods=methods,
                    docstring=docstring,
                    decorators=decorators
                ))
        
        return classes
    
    def extract_imports(self, code: str) -> List[ImportInfo]:
        """
        提取代码中的导入语句
        
        Args:
            code: 源代码
            
        Returns:
            导入信息列表
        """
        tree = self.parse_code(code)
        if tree is None:
            return []
        
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        line=node.lineno
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        module=node.module,
                        names=names,
                        line=node.lineno
                    ))
        
        return imports
    
    def analyze_complexity(self, code: str) -> CodeMetrics:
        """
        分析代码复杂度
        
        Args:
            code: 源代码
            
        Returns:
            代码度量信息
        """
        lines = code.split('\n')
        
        # 统计各类行数
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        # 解析 AST 获取函数和类数量
        tree = self.parse_code(code)
        functions = 0
        classes = 0
        complexity = 1  # 基础复杂度
        
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions += 1
                    complexity += self._calculate_function_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    classes += 1
        
        return CodeMetrics(
            lines_of_code=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
            classes=classes,
            complexity=complexity
        )
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """
        计算函数的圈复杂度
        
        Args:
            node: 函数 AST 节点
            
        Returns:
            复杂度值
        """
        complexity = 0
        
        for child in ast.walk(node):
            # 分支语句增加复杂度
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            # 异常处理增加复杂度
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            # 布尔运算符增加复杂度
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def find_symbol_at_line(self, code: str, line_number: int) -> Optional[Dict[str, Any]]:
        """
        查找指定行的符号信息
        
        Args:
            code: 源代码
            line_number: 行号（1-based）
            
        Returns:
            符号信息字典，找不到返回 None
        """
        tree = self.parse_code(code)
        if tree is None:
            return None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno == line_number:
                    return {
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    }
            
            elif isinstance(node, ast.ClassDef):
                if node.lineno == line_number:
                    return {
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases]
                    }
        
        return None
    
    def get_function_body(self, code: str, function_name: str) -> Optional[str]:
        """
        获取函数体代码
        
        Args:
            code: 源代码
            function_name: 函数名
            
        Returns:
            函数体代码，找不到返回 None
        """
        tree = self.parse_code(code)
        if tree is None:
            return None
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    try:
                        return ast.unparse(node)
                    except:
                        logger.error(f"Failed to unparse function: {function_name}")
                        return None
        
        return None

