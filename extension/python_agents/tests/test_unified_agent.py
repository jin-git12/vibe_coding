"""
测试统一 Agent 架构
"""
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_unified_agent_import():
    """测试统一 agent 可以正常导入"""
    try:
        from agents import create_unified_chat_agent, create_custom_tools
        print("[OK] Successfully imported create_unified_chat_agent and create_custom_tools")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_custom_tools():
    """测试自定义工具创建"""
    try:
        from agents import create_custom_tools
        
        # 不提供 ast_tools，应该返回空列表
        tools = create_custom_tools(ast_tools=None)
        assert tools == [], f"Expected empty list, got {tools}"
        print("[OK] Custom tools created successfully (no AST tools)")
        return True
    except Exception as e:
        print(f"[FAIL] Custom tools test failed: {e}")
        return False


def test_agent_server_structure():
    """测试 AgentServer 基本结构"""
    try:
        from agent_server import AgentServer
        
        # 检查 AgentServer 类是否有必要的方法
        required_methods = ['chat', 'generate_code', 'explain_code', 'refactor_code']
        
        for method in required_methods:
            assert hasattr(AgentServer, method), f"AgentServer missing method: {method}"
        
        print(f"[OK] AgentServer has all required methods: {', '.join(required_methods)}")
        return True
    except Exception as e:
        print(f"[FAIL] AgentServer structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_architecture():
    """验证统一架构的完整性"""
    print("\n=== Unified Agent Architecture Tests ===\n")
    
    tests = [
        ("Import Test", test_unified_agent_import),
        ("Custom Tools", test_custom_tools),
        ("AgentServer Structure", test_agent_server_structure),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Running: {name}...")
        result = test_func()
        results.append(result)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {passed}/{total} passed")
    print(f"{'='*50}\n")
    
    if passed == total:
        print("SUCCESS: All tests passed! Unified architecture is configured correctly.")
        return True
    else:
        print("WARNING: Some tests failed. Please check configuration.")
        return False


if __name__ == "__main__":
    success = test_unified_architecture()
    sys.exit(0 if success else 1)

