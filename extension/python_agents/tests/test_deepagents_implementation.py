"""
测试新的 deepagents 实现

运行: python test_deepagents_implementation.py
"""
import os
import sys

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

def test_imports():
    """测试模块导入"""
    print("[TEST] Testing imports...")
    try:
        # Test new agent imports
        from src.agents import (
            create_custom_tools,
            create_code_generator_agent,
            create_chat_agent,
            create_code_explainer_agent,
            create_refactoring_agent,
        )
        print("[PASS] All agent functions imported successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deepagents_available():
    """测试 deepagents 是否可用"""
    print("\n[TEST] Testing deepagents availability...")
    try:
        from deepagents import create_deep_agent
        print("[PASS] deepagents is available")
        return True
    except ImportError as e:
        print(f"[WARN] deepagents not installed: {e}")
        print("       Run: uv pip install deepagents>=0.2.5")
        return False


def test_custom_tools():
    """测试自定义工具创建"""
    print("\n[TEST] Testing custom tools creation...")
    try:
        from src.agents import create_custom_tools
        from src.tools import ASTTools
        
        ast_tools = ASTTools()
        
        tools = create_custom_tools(ast_tools=ast_tools)
        
        print(f"[PASS] Created {len(tools)} custom tools (AST analysis)")
        for tool in tools:
            print(f"       - {tool.name}: {tool.description[:50]}...")
        
        print(f"[INFO] FileTools and SearchTools removed - deepagents provides:")
        print(f"       - ls, read_file, write_file, edit_file")
        print(f"       - grep_search, glob_search")
        return True
    except Exception as e:
        print(f"[FAIL] Custom tools error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_creation():
    """测试 Agent 创建"""
    print("\n[TEST] Testing agent creation...")
    try:
        from langchain_openai import ChatOpenAI
        from src.agents import create_chat_agent, create_custom_tools
        from src.tools import ASTTools
        
        # 创建一个虚拟 LLM（不需要真实 API key 来测试创建）
        llm = ChatOpenAI(
            model="qwen-turbo",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="dummy_key_for_testing",
            temperature=0.7,
        )
        
        # 创建工具（只需要 AST，文件系统由 deepagents 提供）
        ast_tools = ASTTools()
        custom_tools = create_custom_tools(ast_tools=ast_tools)
        
        # 创建 agent
        agent = create_chat_agent(llm, custom_tools)
        
        print(f"[PASS] Chat agent created: {type(agent)}")
        print(f"       Agent has 'invoke' method: {hasattr(agent, 'invoke')}")
        print(f"       Custom tools: {len(custom_tools)} (AST analysis)")
        print(f"       Built-in tools: ls, read_file, write_file, edit_file,")
        print(f"                       grep_search, glob_search, write_todos")
        
        return True
    except Exception as e:
        print(f"[FAIL] Agent creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pyproject_dependencies():
    """检查 pyproject.toml 依赖"""
    print("\n[TEST] Checking pyproject.toml dependencies...")
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = [
            ("deepagents>=0.2.5", "deepagents version"),
            ("langchain>=1.0.2", "langchain version"),
            ("langchain-openai", "langchain-openai"),
        ]
        
        all_ok = True
        for check, desc in checks:
            if check.split(">=")[0] in content or check.split(",")[0] in content:
                print(f"[PASS] {desc} found")
            else:
                print(f"[WARN] {desc} not found in pyproject.toml")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"[FAIL] Error reading pyproject.toml: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Testing New DeepAgents Implementation")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("Imports", test_imports()))
    results.append(("DeepAgents Available", test_deepagents_available()))
    results.append(("PyProject Dependencies", test_pyproject_dependencies()))
    results.append(("Custom Tools", test_custom_tools()))
    results.append(("Agent Creation", test_agent_creation()))
    
    # 总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

