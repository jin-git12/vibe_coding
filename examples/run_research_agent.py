"""Simple script to run the research agent interactively."""
import asyncio
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

from research_agent import agent


def main():
    """Run the agent interactively."""
    print("=" * 60)
    print("Deep Research Agent")
    print("=" * 60)
    print("\nAgent initialized successfully!")
    print(f"Model: Qwen (configured via QWEN_MODEL env var)")
    print("\nYou can now interact with the agent.")
    print("Example: 'What is LangGraph?'")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if not user_input:
                continue
            
            print("\nAgent is thinking...\n")
            
            # Invoke the agent
            result = agent.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })
            
            # Get the last message from the agent
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    print(f"Agent: {last_message.content}\n")
                else:
                    print(f"Agent: {last_message}\n")
            else:
                print(f"Agent: {result}\n")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

