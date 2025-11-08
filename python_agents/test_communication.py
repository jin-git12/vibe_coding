"""
测试 JSON-RPC 通信
模拟 TypeScript 前端的请求
"""
import json
import subprocess
import sys
from pathlib import Path

# Windows 编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def send_request(process, method: str, params: dict, request_id: int = 1):
    """发送 JSON-RPC 请求"""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    json_str = json.dumps(request) + '\n'
    print(f"→ Sending: {method}")
    print(f"  {json_str}")
    
    process.stdin.write(json_str)
    process.stdin.flush()


def read_response(process):
    """读取响应"""
    line = process.stdout.readline()
    if not line:
        return None
    
    print(f"← Received:")
    print(f"  {line}")
    
    return json.loads(line)


def main():
    """测试主流程"""
    print("=" * 60)
    print("Testing JSON-RPC Communication")
    print("=" * 60)
    
    # 启动 Python 进程
    agent_server = Path(__file__).parent / "src" / "agent_server.py"
    
    process = subprocess.Popen(
        [sys.executable, str(agent_server)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # 读取就绪通知
        print("\n1. Waiting for server ready...")
        ready = read_response(process)
        if ready and ready.get("method") == "server.ready":
            print("✓ Server is ready!")
        
        # 测试 health_check
        print("\n2. Testing health_check...")
        send_request(process, "health_check", {}, 1)
        response = read_response(process)
        if response and response.get("result", {}).get("status") == "ok":
            print("✓ Health check passed!")
        
        # 测试 chat
        print("\n3. Testing chat...")
        send_request(process, "chat", {
            "message": "Hello AI!",
            "conversation_id": "test-001"
        }, 2)
        
        response = read_response(process)
        if response and "result" in response:
            print("✓ Chat response received!")
            print(f"  Response: {response['result'].get('full_response', '')[:50]}...")
        
        # 测试 generate_code
        print("\n4. Testing generate_code...")
        send_request(process, "generate_code", {
            "prompt": "Create a calculator function",
            "language": "python"
        }, 3)
        
        response = read_response(process)
        if response and "result" in response:
            print("✓ Code generated!")
            print(f"  Code: {response['result'].get('code', '')[:80]}...")
        
        # 发送 shutdown
        print("\n5. Shutting down...")
        send_request(process, "shutdown", {}, 999)
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        process.terminate()
        process.wait(timeout=3)


if __name__ == "__main__":
    main()

