"""
代码助手 Agents
使用 deepagents 的正确方式创建各种代码助手
"""
import logging
from typing import List, Any, Optional
from langchain_core.tools import tool
from deepagents import create_deep_agent

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


def create_code_generator_agent(
    llm,
    custom_tools: List = None,
    middleware: List = None,
    interrupt_on: dict = None,
    backend = None,
):
    """
    创建代码生成 Agent
    
    Args:
        llm: LLM 模型实例
        custom_tools: 额外的自定义工具
        middleware: 额外的 middleware
        interrupt_on: HITL 配置 (Human-in-the-Loop)
        backend: 文件系统后端 (StateBackend, StoreBackend, etc.)
        
    Returns:
        配置好的 deep agent (CompiledStateGraph)
    """
    system_prompt = """You are an expert code generation AI assistant.

Your capabilities:
1. **Generate code**: Create high-quality, production-ready code based on requirements
2. **Read files**: Use ls and read_file to understand existing code
3. **Search code**: Use grep_search or glob_search to find patterns
4. **Analyze code**: Use analyze_python_code to understand code structure
5. **Plan**: Use write_todos to break down complex tasks

Guidelines:
- Write clean, well-documented code with type hints
- Include error handling and edge cases
- Follow language-specific best practices
- Consider performance, security, and maintainability
- Use file system tools to understand context before generating
- Break down complex tasks using the planning tool

You have access to deepagents' built-in tools:
- File system: ls, read_file, write_file, edit_file, grep_search, glob_search
- Planning: write_todos
Use these tools effectively to explore and understand the codebase."""
    
    tools = custom_tools or []
    
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware or [],
        interrupt_on=interrupt_on,
        backend=backend,
    )
    
    logger.info("Code generator agent created")
    return agent


def create_chat_agent(
    llm,
    custom_tools: List = None,
    middleware: List = None,
    interrupt_on: dict = None,
    backend = None,
):
    """
    创建通用聊天 Agent
    
    Args:
        llm: LLM 模型实例
        custom_tools: 额外的自定义工具
        middleware: 额外的 middleware
        interrupt_on: HITL 配置 (Human-in-the-Loop)
        backend: 文件系统后端
        
    Returns:
        配置好的 deep agent (CompiledStateGraph)
    """
    system_prompt = """You are an expert AI coding assistant.

Your role is to help developers with:
- Understanding code
- Debugging problems  
- Suggesting improvements
- Answering technical questions
- Explaining concepts

You have access to:
- File system tools: ls, read_file, write_file, edit_file, grep_search, glob_search
- Code search capabilities
- Code analysis tools
- Planning tool: write_todos for complex multi-step tasks

Be helpful, accurate, and provide concrete examples when possible.
Always read relevant files first to understand context before answering.
For complex tasks, use write_todos to plan your approach."""
    
    tools = custom_tools or []
    
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware or [],
        interrupt_on=interrupt_on,
        backend=backend,
    )
    
    logger.info("Chat agent created")
    return agent


def create_code_explainer_agent(
    llm,
    custom_tools: List = None,
    middleware: List = None,
    interrupt_on: dict = None,
    backend = None,
):
    """
    创建代码解释 Agent
    
    Args:
        llm: LLM 模型实例
        custom_tools: 额外的自定义工具
        middleware: 额外的 middleware
        interrupt_on: HITL 配置
        backend: 文件系统后端
        
    Returns:
        配置好的 deep agent (CompiledStateGraph)
    """
    system_prompt = """You are an expert at explaining code clearly and thoroughly.

When explaining code:
1. Start with a high-level overview
2. Break down the main components
3. Explain the logic flow
4. Discuss complexity and performance
5. Point out potential issues or improvements
6. Mention best practices

You have access to:
- File system tools: ls, read_file, write_file, edit_file, grep_search, glob_search
- Code analysis tools: analyze_python_code
- Planning tool: write_todos for complex explanations

Use analyze_python_code to understand structure, then provide a comprehensive explanation.
Use file system tools to read related files for better context."""
    
    tools = custom_tools or []
    
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware or [],
        interrupt_on=interrupt_on,
        backend=backend,
    )
    
    logger.info("Code explainer agent created")
    return agent


def create_refactoring_agent(
    llm,
    custom_tools: List = None,
    middleware: List = None,
    interrupt_on: dict = None,
    backend = None,
):
    """
    创建代码重构 Agent
    
    Args:
        llm: LLM 模型实例
        custom_tools: 额外的自定义工具
        middleware: 额外的 middleware
        interrupt_on: HITL 配置
        backend: 文件系统后端
        
    Returns:
        配置好的 deep agent (CompiledStateGraph)
    """
    system_prompt = """You are an expert at code refactoring.

Your goals:
- Improve code quality and readability
- Apply design patterns appropriately
- Optimize performance when needed
- Maintain or improve test coverage
- Keep functionality intact

Process:
1. Use ls and read_file to understand the current code
2. Use analyze_python_code to analyze structure
3. Plan the refactoring using write_todos
4. Use edit_file to make changes carefully (incremental, safe changes)
5. Explain what was changed and why

You have access to:
- File system tools: ls, read_file, write_file, edit_file, grep_search, glob_search
- Code analysis tools
- Planning tool: write_todos

Use file system tools effectively and make incremental, safe changes.
Always plan complex refactorings with write_todos before starting."""
    
    tools = custom_tools or []
    
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        middleware=middleware or [],
        interrupt_on=interrupt_on,
        backend=backend,
    )
    
    logger.info("Refactoring agent created")
    return agent

