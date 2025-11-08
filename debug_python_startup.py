"""
诊断脚本 - 检查 Python 环境和依赖
"""
import sys
import subprocess
from pathlib import Path

# Windows 编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("=" * 60)
print("Vibe Coding - Python 环境诊断")
print("=" * 60)

# 1. 检查 Python 版本
print(f"\n1. Python 版本: {sys.version}")
print(f"   Python 路径: {sys.executable}")

# 2. 检查 uv 是否安装
print("\n2. 检查 uv 命令...")
try:
    result = subprocess.run(['uv', '--version'], capture_output=True, text=True, timeout=5)
    print(f"   ✓ uv 版本: {result.stdout.strip()}")
except FileNotFoundError:
    print("   ✗ uv 未安装或不在 PATH 中")
    print("   请运行: pip install uv")
except Exception as e:
    print(f"   ✗ uv 检查失败: {e}")

# 3. 检查项目结构
print("\n3. 检查项目结构...")
project_root = Path(__file__).parent
python_agents = project_root / "python_agents"
agent_server = python_agents / "src" / "agent_server.py"

print(f"   项目根目录: {project_root}")
print(f"   python_agents 目录: {python_agents}")
print(f"   - 存在: {'✓' if python_agents.exists() else '✗'}")
print(f"   agent_server.py: {agent_server}")
print(f"   - 存在: {'✓' if agent_server.exists() else '✗'}")

# 4. 检查 Python 依赖
print("\n4. 检查 Python 依赖...")
required_packages = ['deepagents', 'langchain', 'langchain_openai', 'langchain_core']

for package in required_packages:
    try:
        __import__(package)
        print(f"   ✓ {package}")
    except ImportError:
        print(f"   ✗ {package} 未安装")

# 5. 尝试启动 agent_server
print("\n5. 测试启动 agent_server.py...")
if agent_server.exists():
    print(f"   运行命令: uv run python {agent_server}")
    try:
        # 只运行几秒钟看看是否有错误
        process = subprocess.Popen(
            ['uv', 'run', 'python', str(agent_server)],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("   进程已启动，等待 3 秒...")
        import time
        time.sleep(3)
        
        # 检查进程状态
        if process.poll() is None:
            print("   ✓ 进程仍在运行（正常）")
            process.terminate()
            process.wait(timeout=5)
        else:
            print(f"   ✗ 进程已退出，退出码: {process.returncode}")
            stdout, stderr = process.communicate()
            if stdout:
                print(f"   stdout: {stdout[:200]}")
            if stderr:
                print(f"   stderr: {stderr[:200]}")
    except Exception as e:
        print(f"   ✗ 启动失败: {e}")
else:
    print("   ✗ agent_server.py 不存在")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)

# 建议
print("\n建议:")
print("1. 如果 uv 未安装: pip install uv")
print("2. 如果依赖未安装: cd python_agents && uv sync")
print("3. 如果进程启动失败，查看上面的错误信息")

