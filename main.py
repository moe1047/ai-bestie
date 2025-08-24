import asyncio
import datetime
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv
from typing import TypedDict, List

from graph.minimal_mind_agents import (
    web_search_agent,
    fact_checker_agent,
    responder_agent,
    supervisor_node
)

# Load environment variables
load_dotenv()

# Define the state for our minimal mind
class MinimalMindState(TypedDict):
    query: str
    current_date: str
    search_results: List[dict]
    analysis: str
    next_agent: str

def get_minimal_mind_graph():
    """Builds the graph for the Minimal Viable Mind."""
    # 1. Define the graph
    graph = StateGraph(MinimalMindState)

    # 2. Add the nodes
    graph.add_node("web_search", web_search_agent)
    graph.add_node("fact_checker", fact_checker_agent)
    graph.add_node("responder", responder_agent)
    graph.add_node("supervisor", supervisor_node)

    # 3. Define the edges
    graph.set_entry_point("web_search")
    graph.add_edge("web_search", "supervisor")
    graph.add_edge("fact_checker", "supervisor")
    graph.add_edge("responder", "supervisor")

    # 4. Conditional routing from the supervisor
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state["next_agent"],
        {
            "fact_checker": "fact_checker",
            "responder": "responder",
            "FINISH": END,
        },
    )

    # 5. Compile the graph
    minimal_mind_graph = graph.compile()
    return minimal_mind_graph

async def run_graph():
    """Runs the Minimal Viable Mind graph and streams intermediate states for debugging."""
    graph = get_minimal_mind_graph()
    
    # Get the current date
    current_date = datetime.date.today().isoformat()

    # Use astream to get intermediate steps. We'll merge the states
    # to build up the final state object, which will contain all the fields.
    final_state = {}
    async for state in graph.astream({
        "query": "Who is the current president of the United States?",
        "current_date": current_date
    }):
        print("---STREAM---")
        for key, value in state.items():
            print(f"Node: {key}")
            print(f"Value: {value}\n")
        print("\n====================\n")
        final_state.update(state)

    # The final response is in the 'responder' key of the last state object.
    print("---FINAL RESPONSE---")
    print(final_state.get('responder', 'No final response generated.'))

if __name__ == "__main__":
    asyncio.run(run_graph())
