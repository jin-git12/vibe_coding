"""Test script to verify the research agent can be created and run."""
import os
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Check required environment variables
required_env_vars = {
    "TAVILY_API_KEY": "Tavily API key for web search",
    "DASHSCOPE_API_KEY": "DashScope API key for Qwen model",
}

missing_vars = []
for var, description in required_env_vars.items():
    if not os.getenv(var):
        missing_vars.append(f"  - {var}: {description}")

if missing_vars:
    print("WARNING: Missing required environment variables:")
    print("\n".join(missing_vars))
    print("\nPlease set these in your .env file or environment.")
    print("You can create a .env file in the project root with:")
    print("  TAVILY_API_KEY=your_tavily_key")
    print("  DASHSCOPE_API_KEY=your_dashscope_key")
    print("  QWEN_MODEL=qwen-turbo  # Optional, defaults to qwen-turbo")
    sys.exit(1)

print("OK: All required environment variables are set!")
print("\nTesting agent creation...")

try:
    # Add current directory to path for imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from research_agent import agent
    print(f"OK: Agent created successfully!")
    print(f"   Agent type: {type(agent).__name__}")
    print("\nYou can now run the agent using:")
    print("  uv run python examples/run_research_agent.py")
    print("\nOr use it programmatically:")
    print("  from examples.research_agent import agent")
    print("  result = agent.invoke({'messages': [{'role': 'user', 'content': 'Your question'}]})")
except Exception as e:
    print(f"ERROR: Error creating agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

