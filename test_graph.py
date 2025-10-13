import os
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
load_dotenv()

# Verify that the GROQ_API_KEY is loaded
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found. Please ensure it is set in your .env file.")

from graph.build_graph import build_graph
from langchain_core.messages import HumanMessage

def main():
    """Main function to run the graph test synchronously."""
    # Build the graph without a checkpointer
    graph = build_graph(checkpointer=None)

    # Define the initial state with a sample user message
    initial_state = {
        "messages": [HumanMessage(content="life has been soo hard on me lately. i dont knwo what i did to deserve it")],
        "user": {"id": 123, "name": "Test User"},
        "session": {"id": 456, "start_time": "2025-01-01T12:00:00"},
    }

    print("--- Invoking Graph ---")
    # Use the synchronous invoke method
    final_state = graph.invoke(initial_state)

    print("\n--- Final State ---")
    # The final state will contain the accumulated outputs of all nodes
    if final_state and final_state.get("messages"):
        print("\n--- Reasoning --- ")
        if final_state.get("reasoning"):
            reasoning = final_state["reasoning"][-1]
            print(f"Rationale: {reasoning.get('rationale', {}).get('summary')}")
            print(f"Need: {reasoning.get('need', {}).get('category')}")
            print(f"Micro-Goal: {reasoning.get('micro_goal', {}).get('type')}")

        print("\n--- Final Response --- ")
        # The last message in the list should be the AI's response
        print(final_state["messages"][-1].content)
    else:
        print("Could not find 'messages' key in the final state.")
        print("Full final state:", final_state)

if __name__ == "__main__":
    main()
