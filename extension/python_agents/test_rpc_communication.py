"""
测试 JSON-RPC 前后端通信
模拟 TypeScript 扩展与 Python 后端的交互
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path

# 设置开发模式
os.environ["DEV_MODE"] = "true"
os.environ["WORKSPACE_ROOT"] = str(Path.cwd())
os.environ["LOG_LEVEL"] = "INFO"

def test_rpc_communication():
    """测试 RPC 通信"""
    print("=" * 60)
    print("Testing JSON-RPC Communication")
    print("=" * 60)
    
    # 启动 Python 进程
    print("\n[1] Starting Python agent server...")
    
    # 使用虚拟环境的 Python
    python_path = Path(".venv/Scripts/python.exe")
    if not python_path.exists():
        python_path = Path(".venv/bin/python")  # Linux/Mac
    
    server_path = Path("src/agent_server.py")
    
    process = subprocess.Popen(
        [str(python_path), str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    print("[OK] Process started")
    
    # 等待服务器启动
    print("\n[2] Waiting for server to be ready...")
    time.sleep(2)
    
    # 测试健康检查
    print("\n[3] Testing health_check...")
    health_check_request = {
        "jsonrpc": "2.0",
        "method": "health_check",
        "params": {},
        "id": 1
    }
    
    try:
        # 发送请求
        request_json = json.dumps(health_check_request) + "\n"
        print(f"Sending: {health_check_request}")
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # 读取响应（带超时）
        import select
        
        # 给一些时间让服务器响应
        time.sleep(1)
        
        # 读取输出
        response_line = process.stdout.readline()
        
        if response_line:
            response = json.loads(response_line)
            print(f"[OK] Received response: {json.dumps(response, indent=2)}")
            
            if "result" in response:
                result = response["result"]
                print(f"\n[SUCCESS] Health check passed!")
                print(f"  Status: {result.get('status')}")
                print(f"  Workspace: {result.get('workspace')}")
                print(f"  Available methods: {len(result.get('methods', []))}")
                return True
            else:
                print(f"\n[ERROR] No result in response")
                return False
        else:
            print("\n[ERROR] No response received")
            
            # 读取 stderr 查看错误
            stderr = process.stderr.read()
            if stderr:
                print(f"\nStderr output:\n{stderr}")
            
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Communication failed: {e}")
        
        # 尝试读取错误输出
        try:
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"\nServer error output:\n{stderr_output}")
        except:
            pass
        
        return False
    
    finally:
        # 关闭进程
        print("\n[4] Shutting down server...")
        try:
            shutdown_request = {
                "jsonrpc": "2.0",
                "method": "shutdown",
                "params": {},
                "id": 2
            }
            process.stdin.write(json.dumps(shutdown_request) + "\n")
            process.stdin.flush()
        except:
            pass
        
        process.terminate()
        process.wait(timeout=3)
        print("[OK] Server stopped")


def test_agent_invocation():
    """测试 Agent 调用"""
    print("\n" + "=" * 60)
    print("Testing Agent Invocation")
    print("=" * 60)
    
    # 直接测试 Agent Server
    print("\n[1] Testing Agent Server directly...")
    
    sys.path.insert(0, str(Path("src")))
    
    try:
        from agent_server import AgentServer
        
        print("[OK] AgentServer imported")
        
        # 创建服务器实例
        print("\n[2] Creating AgentServer instance...")
        server = AgentServer(workspace_root=str(Path.cwd()))
        print("[OK] AgentServer created")
        
        # 测试健康检查
        print("\n[3] Testing health_check method...")
        result = server.health_check({})
        print(f"[OK] Health check result: {result.get('status')}")
        
        # 测试聊天（如果 LLM 可用）
        if server.chat_agent:
            print("\n[4] Testing chat method...")
            chat_result = server.chat({
                "message": "Hello, this is a test",
                "conversation_id": "test-conv",
                "stream": False
            })
            
            if "error" not in chat_result:
                print("[OK] Chat method works!")
                response = chat_result.get("full_response", "")[:100]
                print(f"  Response preview: {response}...")
            else:
                print(f"[WARN] Chat returned error: {chat_result.get('error')}")
        else:
            print("\n[4] [WARN] Chat agent not available (LLM not configured)")
        
        print("\n[SUCCESS] Agent invocation test passed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Agent invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n[TEST] Testing Vibe Coding Backend\n")
    
    # 测试 1: RPC 通信
    rpc_success = test_rpc_communication()
    
    # 测试 2: Agent 调用
    agent_success = test_agent_invocation()
    
    # 总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"RPC Communication: {'[PASS]' if rpc_success else '[FAIL]'}")
    print(f"Agent Invocation:  {'[PASS]' if agent_success else '[FAIL]'}")
    
    if rpc_success and agent_success:
        print("\n[SUCCESS] All tests passed! Frontend and backend are ready to communicate.")
    else:
        print("\n[WARNING] Some tests failed. Please check the error messages above.")
    
    sys.exit(0 if (rpc_success and agent_success) else 1)

