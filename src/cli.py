import sys
import os

# Ensure the root of the project is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from src.agents.main_agent import main_graph

def run_chat_cli():
    print("==================================================")
    print("   R2CELL RAG Chatbot (gemma4:31b-cloud)          ")
    print("==================================================")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    # Define a persistent conversation session via config thread ID
    config = {"configurable": {"thread_id": "cli-session-1"}}

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break
            
            # 1. Package input in HumanMessage format
            input_state = {"messages": [HumanMessage(content=user_input)]}
            
            # 2. Invoke the compiled graph with persistent thread context
            print("AI: ", end="", flush=True)
            
            # We can stream intermediate node transitions or stream final values
            # For simplicity, we can print the updates from nodes as they happen
            response_state = main_graph.invoke(input_state, config=config)
            
            # The last message in the returned state is the model's response
            last_msg = response_state["messages"][-1]
            print(last_msg.content)
            print() # Print newline
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    run_chat_cli()
