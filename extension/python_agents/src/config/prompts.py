"""
Prompt 模板管理
为不同的 Agent 任务提供专业的 Prompt 模板
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Prompt 模板集合"""
    
    # 系统 Prompt
    SYSTEM_BASE = """You are an expert AI coding assistant integrated into a VS Code extension.
You have deep knowledge of software development, multiple programming languages, and best practices.
Your role is to help developers write better code, understand existing code, and solve programming problems.

Guidelines:
- Be concise but thorough in your explanations
- Provide working, production-ready code
- Follow language-specific conventions and best practices
- Consider performance, security, and maintainability
- When unsure, state your assumptions clearly
"""
    
    # 代码生成
    CODE_GENERATION = """## Task: Code Generation

Generate {language} code based on the following requirements:

{prompt}

## Context:
{context}

## Requirements:
- Write clean, well-documented code
- Include type hints/annotations where applicable
- Add error handling
- Follow {language} best practices
- Make the code production-ready

Generate the code with appropriate comments and documentation."""
    
    # 代码解释
    CODE_EXPLANATION = """## Task: Code Explanation

Explain the following {language} code:

```{language}
{code}
```

## Context:
{context}

## Your Explanation Should Include:
1. **Overview**: What does this code do? (1-2 sentences)
2. **Key Components**: Break down the main parts
3. **Logic Flow**: Explain the execution flow
4. **Complexity**: Time and space complexity analysis
5. **Potential Issues**: Any bugs, edge cases, or improvements
6. **Best Practices**: How well does it follow conventions?

Be thorough but concise."""
    
    # 代码重构
    CODE_REFACTORING = """## Task: Code Refactoring

Refactor the following {language} code according to these instructions:

**Instructions**: {instructions}

**Original Code**:
```{language}
{code}
```

## Context:
{context}

## Refactoring Goals:
- Improve code quality and readability
- Apply design patterns where appropriate
- Optimize performance if needed
- Maintain or improve test coverage
- Keep functionality intact

Provide:
1. The refactored code
2. Explanation of changes made
3. Benefits of the refactoring
4. Any trade-offs or considerations"""
    
    # 代码审查
    CODE_REVIEW = """## Task: Code Review

Review the following {language} code for quality, security, and best practices:

```{language}
{code}
```

## Context:
{context}

## Review Criteria:
1. **Code Quality**: Readability, maintainability, structure
2. **Correctness**: Logic errors, edge cases, potential bugs
3. **Performance**: Efficiency, optimization opportunities
4. **Security**: Vulnerabilities, unsafe practices
5. **Best Practices**: Language conventions, design patterns
6. **Testing**: Test coverage, testability
7. **Documentation**: Comments, docstrings, clarity

Provide:
- Overall assessment (score out of 10)
- Specific issues found (categorized by severity)
- Concrete suggestions for improvement
- Positive aspects worth keeping"""
    
    # 代码搜索
    CODE_SEARCH = """## Task: Semantic Code Search

Find code in the workspace that matches this query:

**Query**: {query}

## Context:
{context}

## Search Strategy:
- Look for functions, classes, or patterns related to the query
- Consider semantic meaning, not just keyword matching
- Prioritize relevant results
- Include context around matches

Describe what you're looking for and suggest file patterns to search."""
    
    # 聊天对话
    CHAT = """## Task: General Coding Assistance

User's question/request:
{message}

## Current Context:
{context}

Provide a helpful, accurate response. If the user is asking for code, provide complete, working examples.
If explaining concepts, be clear and use examples. If debugging, analyze the problem systematically."""
    
    # Bug 修复
    BUG_FIX = """## Task: Bug Fix

The user has reported a bug or error in their code.

**Issue Description**: {issue}

**Code**:
```{language}
{code}
```

## Context:
{context}

## Debug Process:
1. **Identify**: What's causing the bug?
2. **Analyze**: Why does this happen?
3. **Fix**: Provide corrected code
4. **Explain**: Explain the fix and why it works
5. **Prevent**: Suggest how to avoid similar bugs

Provide a clear, working solution."""
    
    # 测试生成
    TEST_GENERATION = """## Task: Generate Tests

Generate comprehensive unit tests for the following {language} code:

```{language}
{code}
```

## Context:
{context}

## Test Requirements:
- Use appropriate testing framework for {language}
- Cover normal cases, edge cases, and error cases
- Aim for high code coverage
- Include setup and teardown if needed
- Add clear test names and documentation
- Test both positive and negative scenarios

Generate complete, runnable test code."""
    
    # 文档生成
    DOCUMENTATION = """## Task: Generate Documentation

Generate documentation for the following {language} code:

```{language}
{code}
```

## Context:
{context}

## Documentation Should Include:
- Overview/purpose
- Parameters/arguments with types
- Return values
- Usage examples
- Exceptions/errors that may be raised
- Notes about performance or special behaviors

Follow the documentation style convention for {language} (e.g., docstrings for Python, JSDoc for JavaScript)."""
    
    def __init__(self):
        """初始化 Prompt 模板"""
        logger.info("PromptTemplates initialized")
    
    def get_system_prompt(self, task_type: Optional[str] = None) -> str:
        """
        获取系统 Prompt
        
        Args:
            task_type: 任务类型（用于自定义系统 Prompt）
            
        Returns:
            系统 Prompt 文本
        """
        return self.SYSTEM_BASE
    
    def format_prompt(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        格式化 Prompt 模板
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            格式化后的 Prompt
        """
        template = getattr(self, template_name.upper(), None)
        
        if template is None:
            logger.error(f"Unknown template: {template_name}")
            return f"Error: Template '{template_name}' not found"
        
        try:
            # 格式化上下文
            if 'context' in kwargs and isinstance(kwargs['context'], dict):
                from ..utils.context_builder import ContextBuilder
                # 将上下文字典转换为格式化文本
                context_text = self._format_context(kwargs['context'])
                kwargs['context'] = context_text
            
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template parameter: {e}")
            raise ValueError(f"Missing required parameter: {e}")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        格式化上下文信息
        
        Args:
            context: 上下文字典
            
        Returns:
            格式化的上下文文本
        """
        parts = []
        
        if "current_file" in context:
            file_info = context["current_file"]
            parts.append(f"File: {file_info.get('path', 'Unknown')}")
            parts.append(f"Language: {file_info.get('language', 'Unknown')}")
        
        if "workspace" in context:
            ws = context["workspace"]
            parts.append(f"Workspace: {ws.get('name', 'Unknown')}")
            if ws.get("project_types"):
                parts.append(f"Project Type: {', '.join(ws['project_types'])}")
        
        if "selected_code" in context:
            parts.append("\nSelected Code:")
            parts.append(context["selected_code"].get("content", ""))
        
        return '\n'.join(parts) if parts else "No additional context"


# 全局 Prompt 模板实例
_global_templates: Optional[PromptTemplates] = None


def get_prompt_templates() -> PromptTemplates:
    """
    获取全局 Prompt 模板实例
    
    Returns:
        PromptTemplates 实例
    """
    global _global_templates
    
    if _global_templates is None:
        _global_templates = PromptTemplates()
    
    return _global_templates

