"""
快速测试 DeepAgents 实现

这个脚本展示了如何在交互环境中使用 DeepAgents

运行: python quick_test.py
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置 UTF-8 编码 (Windows)
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')


def test_basic_chat():
    """测试基础聊天功能"""
    print("=" * 60)
    print("测试基础聊天功能")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        from src.agents import create_chat_agent, create_custom_tools
        from src.tools import ASTTools
        
        # 检查 API key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("\n[WARN] DASHSCOPE_API_KEY 未设置")
            print("       请在 .env 文件中设置 DASHSCOPE_API_KEY")
            print("       将使用演示模式（不调用真实 API）\n")
            return
        
        # 创建 LLM
        print("\n[1] 创建 LLM 客户端...")
        llm = ChatOpenAI(
            model=os.getenv("QWEN_MODEL", "qwen-turbo"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            temperature=0.7,
        )
        print("    ✓ LLM 客户端已创建")
        
        # 创建自定义工具（只需AST，文件系统由deepagents提供）
        print("\n[2] 创建自定义工具...")
        custom_tools = create_custom_tools(ast_tools=ASTTools())
        print(f"    ✓ 已创建 {len(custom_tools)} 个自定义工具 (AST分析)")
        print(f"    ✓ deepagents自动提供: ls, read_file, write_file, edit_file")
        print(f"      grep_search, glob_search, write_todos")
        
        # 创建 Agent
        print("\n[3] 创建聊天 Agent...")
        agent = create_chat_agent(llm, custom_tools)
        print(f"    ✓ Agent 类型: {type(agent).__name__}")
        print(f"    ✓ 有 invoke 方法: {hasattr(agent, 'invoke')}")
        
        # 测试调用
        print("\n[4] 测试 Agent 调用...")
        print("    问题: '你好，请介绍一下你的功能'")
        
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": "你好，请用中文简单介绍一下你的功能（50字以内）"
            }]
        })
        
        # 提取响应
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            print(f"\n    Agent 回复:\n    {response}\n")
        
        print("=" * 60)
        print("✓ 基础聊天测试成功！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_code_generation():
    """测试代码生成功能"""
    print("\n" + "=" * 60)
    print("测试代码生成功能")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        from src.agents import create_code_generator_agent, create_custom_tools
        from src.tools import ASTTools
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("\n[SKIP] DASHSCOPE_API_KEY 未设置，跳过此测试\n")
            return
        
        # 创建 LLM 和工具
        llm = ChatOpenAI(
            model=os.getenv("QWEN_MODEL", "qwen-turbo"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            temperature=0.7,
        )
        
        custom_tools = create_custom_tools(ast_tools=ASTTools())
        
        # 创建代码生成 Agent
        print("\n[1] 创建代码生成 Agent...")
        agent = create_code_generator_agent(llm, custom_tools)
        print("    ✓ Agent 已创建")
        
        # 测试生成简单函数
        print("\n[2] 请求生成 Fibonacci 函数...")
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": "生成一个 Python 函数来计算第 n 个 Fibonacci 数（使用递归）。只需要返回代码，不要解释。"
            }]
        })
        
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            print(f"\n    生成的代码:\n")
            print("    " + "\n    ".join(response.split("\n")[:20]))  # 只显示前 20 行
            if len(response.split("\n")) > 20:
                print("    ...")
        
        print("\n=" * 60)
        print("✓ 代码生成测试成功！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """交互模式"""
    print("\n" + "=" * 60)
    print("交互模式")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        from src.agents import create_chat_agent, create_custom_tools
        from src.tools import ASTTools
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("\n[ERROR] DASHSCOPE_API_KEY 未设置")
            print("请在 .env 文件中设置 DASHSCOPE_API_KEY\n")
            return
        
        # 创建 Agent
        print("\n正在初始化 Agent...")
        llm = ChatOpenAI(
            model=os.getenv("QWEN_MODEL", "qwen-turbo"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            temperature=0.7,
        )
        
        custom_tools = create_custom_tools(ast_tools=ASTTools())
        
        agent = create_chat_agent(llm, custom_tools)
        
        print("\n✓ Agent 已准备好！")
        print("\n你可以开始对话了。输入 'exit' 或 'quit' 退出。\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n再见！")
                    break
                
                if not user_input:
                    continue
                
                print("\nAgent 正在思考...\n")
                
                result = agent.invoke({
                    "messages": [{"role": "user", "content": user_input}]
                })
                
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    response = last_message.content if hasattr(last_message, 'content') else str(last_message)
                    print(f"Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
        
    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepAgents 快速测试")
    print("=" * 60)
    print("\n选择测试模式:")
    print("  1. 基础聊天测试")
    print("  2. 代码生成测试")
    print("  3. 交互模式")
    print("  4. 运行所有测试")
    print("  q. 退出")
    
    choice = input("\n请选择 (1-4 或 q): ").strip()
    
    if choice == '1':
        test_basic_chat()
    elif choice == '2':
        test_code_generation()
    elif choice == '3':
        interactive_mode()
    elif choice == '4':
        test_basic_chat()
        test_code_generation()
    elif choice.lower() == 'q':
        print("\n再见！")
    else:
        print("\n无效选择")


if __name__ == "__main__":
    main()

