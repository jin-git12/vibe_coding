"""
统一的 Chat Agent（使用 Subagents）
基于 deepagents 的 subagent 架构，一个聊天框完成所有操作
"""
import logging
from typing import List, Any
from deepagents import create_deep_agent

logger = logging.getLogger(__name__)


def _create_code_generator_subagent(llm, custom_tools: List, backend):
    """创建代码生成 Subagent"""
    return create_deep_agent(
        model=llm,
        system_prompt="""You are an expert code generator.

Your job:
1. Understand the requirements clearly
2. Read relevant files if context is needed (use read_file, grep_search)
3. Plan the implementation (use write_todos for complex code)
4. Generate clean, well-documented code with type hints
5. Include error handling and edge cases
6. Follow language-specific best practices

Guidelines:
- Write production-ready code, not placeholders
- Add docstrings and comments
- Consider performance, security, and maintainability
- Provide usage examples if helpful

IMPORTANT - Output format:
- Return ONLY the generated code with brief explanation
- Do NOT include raw file contents or intermediate search results
- Keep explanation under 200 words
- Use code blocks for code output

You have access to all file system tools to understand the codebase.""",
        tools=custom_tools or [],
        backend=backend,
    )


def _create_code_explainer_subagent(llm, custom_tools: List, backend):
    """创建代码解释 Subagent"""
    return create_deep_agent(
        model=llm,
        system_prompt="""You are an expert at explaining code clearly and thoroughly.

Your approach:
1. Read the code carefully (use read_file if needed)
2. Analyze the structure (use analyze_python_code if available)
3. Start with a high-level overview
4. Break down the main components
5. Explain the logic flow step by step
6. Discuss complexity and performance
7. Point out potential issues or improvements
8. Mention best practices

Make explanations:
- Clear and accessible
- Well-structured with sections
- Include examples when helpful
- Highlight key concepts

IMPORTANT - Output format to keep context clean:
- Return ONLY your explanation, NOT raw file contents
- Do NOT include detailed tool outputs or intermediate results
- Structure: Overview → Key Components → Logic Flow → Insights
- Keep response under 500 words
- Use bullet points for clarity

You have access to file system and code analysis tools.""",
        tools=custom_tools or [],
        backend=backend,
    )


def _create_refactoring_subagent(llm, custom_tools: List, backend):
    """创建代码重构 Subagent"""
    return create_deep_agent(
        model=llm,
        system_prompt="""You are an expert at code refactoring.

Your process:
1. Read and understand the current code (use read_file, grep_search)
2. Analyze the code structure and complexity
3. Plan the refactoring (use write_todos for complex changes)
4. Make incremental, safe changes
5. Explain what was changed and why
6. Ensure functionality remains intact

Refactoring goals:
- Improve code quality and readability
- Apply design patterns appropriately
- Optimize performance when needed
- Reduce duplication (DRY principle)
- Maintain or improve test coverage

Always:
- Make targeted improvements
- Preserve existing functionality
- Provide clear explanations of changes
- Use file system tools to understand context

IMPORTANT - Output format to keep context clean:
- Return: Refactored code + concise list of changes (3-5 bullet points)
- Do NOT include: Raw file contents, intermediate analysis, detailed tool outputs
- Structure: Refactored Code Block → Summary of Changes → Rationale
- Keep explanation under 300 words

You have access to all file system and analysis tools.""",
        tools=custom_tools or [],
        backend=backend,
    )


def create_unified_chat_agent(
    llm,
    custom_tools: List = None,
    backend = None,
):
    """
    创建统一的聊天 Agent（使用 Subagents）
    
    这是一个主 agent，可以：
    - 直接回答问题
    - 自动委派复杂任务给 subagents（代码生成、解释、重构）
    - 管理对话历史
    
    Args:
        llm: LLM 模型实例
        custom_tools: 额外的自定义工具（如 AST 分析）
        backend: Checkpointer（用于对话历史）
        
    Returns:
        配置好的 deep agent with subagents
    """
    
    # 🔧 显式创建每个 Subagent 实例
    logger.info("Creating specialized subagents...")
    
    code_generator_agent = _create_code_generator_subagent(llm, custom_tools, backend)
    logger.info("  ✓ Code Generator Subagent created")
    
    code_explainer_agent = _create_code_explainer_subagent(llm, custom_tools, backend)
    logger.info("  ✓ Code Explainer Subagent created")
    
    refactoring_agent = _create_refactoring_subagent(llm, custom_tools, backend)
    logger.info("  ✓ Refactoring Subagent created")
    
    # 主 Agent 的系统提示
    system_prompt = """You are Vibe Coding AI - an expert AI coding assistant.

Your capabilities:
- Answer coding questions and explain concepts
- Help debug and solve problems
- Generate, explain, and refactor code
- Search and analyze codebases
- Plan complex multi-step tasks

IMPORTANT: You have specialized subagents to help you:
- For CODE GENERATION tasks → use task(name="code-generator", task="...")
- For CODE EXPLANATION tasks → use task(name="code-explainer", task="...")
- For CODE REFACTORING tasks → use task(name="refactoring", task="...")

When to delegate to subagents:
✅ User asks to "generate", "create", or "write" code → code-generator
✅ User asks to "explain", "understand", or "what does this code do" → code-explainer
✅ User asks to "refactor", "improve", or "optimize" code → refactoring
✅ Complex multi-step tasks → break down and delegate

You also have access to:
- File system tools: ls, read_file, write_file, edit_file, grep_search, glob_search
- Code analysis tools
- Planning tool: write_todos for complex multi-step tasks

Be helpful, accurate, and provide concrete examples.
Always read relevant files first to understand context before answering."""
    
    # 🎯 使用 CompiledSubAgent 格式（官方推荐方式）
    from deepagents import CompiledSubAgent
    
    subagents = [
        CompiledSubAgent(
            name="code-generator",
            description="""Expert at generating code.
Use when the user wants to:
- Generate new code or functions
- Create classes, modules, or components
- Write boilerplate or template code
- Implement algorithms or features""",
            runnable=code_generator_agent,
        ),
        CompiledSubAgent(
            name="code-explainer",
            description="""Expert at explaining code.
Use when the user wants to:
- Understand how code works
- Get explanations of functions or classes
- Learn about complex algorithms
- Understand code flow and logic""",
            runnable=code_explainer_agent,
        ),
        CompiledSubAgent(
            name="refactoring",
            description="""Expert at refactoring code.
Use when the user wants to:
- Improve code quality and readability
- Apply design patterns
- Optimize performance
- Reduce code duplication
- Make code more maintainable""",
            runnable=refactoring_agent,
        ),
    ]
    
    # 创建主 agent with subagents
    agent = create_deep_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=custom_tools or [],
        subagents=subagents,  # 🔧 添加 subagents
        backend=backend,  # 对话历史管理（checkpointer）
    )
    
    logger.info("✓ Unified chat agent created successfully")
    logger.info("  Main agent with 3 specialized subagents ready")
    logger.info("  All subagents share the same backend for conversation history")
    
    return agent

