"""
简单的聊天测试脚本
用于触发 Python 后端断点

使用方法：
1. 选择调试配置："🐛 Debug Python Backend"
2. 在 agent_server.py 的 chat() 方法设置断点（第 145 行）
3. 按 F5 启动调试
4. 切换到当前文件
5. 选择调试配置："🔍 Debug Current Python File"
6. 再按 F5 运行此测试脚本
7. 断点会在 agent_server 中触发！
"""
import sys
import json
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agent_server import AgentServer


def test_chat_with_breakpoint():
    """测试聊天功能（会触发断点）"""
    print("=" * 60)
    print("测试聊天功能")
    print("=" * 60)
    
    # 创建 Agent 服务器
    workspace_root = str(Path(__file__).parent.parent.parent.parent)
    server = AgentServer(workspace_root)
    
    # 测试参数
    params = {
        "message": "你好，我是测试用户",
        "conversation_id": "test-001",
        "context": {},
        "stream": False
    }
    
    print(f"\n发送消息: {params['message']}")
    print("如果你在 agent_server.py:145 设置了断点，代码会在这里暂停！\n")
    
    # 调用 chat 方法（会触发断点）
    result = server.chat(params)
    
    print("\n收到响应:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    test_chat_with_breakpoint()



