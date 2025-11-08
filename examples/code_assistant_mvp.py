"""MVP: 基础代码助手 Agent 示例

这是一个类似 Cursor 的代码助手的基础实现。
展示了如何使用 deepagents 创建一个能够读取、理解和修改代码的 Agent。
"""
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from deepagents import create_deep_agent

# Load environment variables
load_dotenv()

# System prompt for code assistant
code_assistant_prompt = """You are an expert code assistant similar to Cursor IDE.

Your capabilities:
1. **Read and understand code**: Read files, understand code structure and logic
2. **Generate code**: Create new code based on requirements and best practices
3. **Modify code**: Edit existing code while preserving functionality
4. **Explain code**: Explain what code does, how it works, and why
5. **Search code**: Find code patterns, functions, classes across the codebase

**Important Guidelines:**
- Always read relevant files first to understand context
- When modifying code, preserve existing functionality unless explicitly asked to change it
- Follow the project's coding style and conventions
- Make incremental, safe changes
- Test your understanding by reading related files before making changes
- Use the file system tools (ls, read_file, write_file, edit_file, grep) effectively

**Workflow:**
1. Understand the request
2. Explore the codebase to find relevant files
3. Read and understand the code
4. Plan your changes
5. Make the changes
6. Verify the changes are correct

You have access to file system tools through deepagents' built-in FilesystemMiddleware.
Use these tools to navigate and modify the codebase."""

# Create the code assistant agent
code_assistant = create_deep_agent(
    model=ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        temperature=0.7,
    ),
    system_prompt=code_assistant_prompt,
    # deepagents automatically includes FilesystemMiddleware with tools:
    # - ls: List files
    # - read_file: Read file contents
    # - write_file: Write new files
    # - edit_file: Edit existing files
    # - grep: Search for patterns
)


def example_usage():
    """示例：如何使用代码助手"""
    
    # 示例 1: 读取和理解代码
    print("=== 示例 1: 读取和理解代码 ===")
    result = code_assistant.invoke({
        "messages": [{
            "role": "user",
            "content": "请读取 examples/research_agent.py 文件，并解释它的主要功能"
        }]
    })
    print(result["messages"][-1].content)
    print("\n")
    
    # 示例 2: 生成新代码
    print("=== 示例 2: 生成新代码 ===")
    result = code_assistant.invoke({
        "messages": [{
            "role": "user",
            "content": """创建一个新的 Python 文件 examples/utils.py，包含以下功能：
1. 一个函数 calculate_fibonacci(n)，计算斐波那契数列的第 n 项
2. 一个函数 is_prime(n)，判断一个数是否为质数
3. 添加适当的文档字符串和类型提示"""
        }]
    })
    print(result["messages"][-1].content)
    print("\n")
    
    # 示例 3: 修改现有代码
    print("=== 示例 3: 修改现有代码 ===")
    result = code_assistant.invoke({
        "messages": [{
            "role": "user",
            "content": """在 examples/utils.py 中添加错误处理：
- calculate_fibonacci 函数应该处理负数输入
- is_prime 函数应该处理小于 2 的情况"""
        }]
    })
    print(result["messages"][-1].content)
    print("\n")
    
    # 示例 4: 搜索代码
    print("=== 示例 4: 搜索代码 ===")
    result = code_assistant.invoke({
        "messages": [{
            "role": "user",
            "content": "在 examples 目录中搜索所有使用 'create_deep_agent' 的文件"
        }]
    })
    print(result["messages"][-1].content)


if __name__ == "__main__":
    print("=" * 60)
    print("代码助手 Agent (MVP)")
    print("=" * 60)
    print("\n这个示例展示了基础代码助手的功能。")
    print("取消注释下面的代码来运行示例：\n")
    
    # 取消注释以运行示例
    # example_usage()
    
    # 或者交互式使用
    print("交互式使用：")
    print("1. 导入: from examples.code_assistant_mvp import code_assistant")
    print("2. 调用: result = code_assistant.invoke({'messages': [{'role': 'user', 'content': '你的问题'}]})")
    print("3. 查看结果: print(result['messages'][-1].content)")

