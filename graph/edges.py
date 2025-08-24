import json
from .state import VeeState
from llms.mode_decider import get_mode_decider_chain
from llms.expertise_router import get_expertise_router_chain
from langchain_core.messages.utils import get_buffer_string

def mode_decider_edge(state: VeeState) -> str:
    """Reads the mode from the state and returns it for routing."""
    mode = state.get("mode", "bestie") # Default to bestie if not found
    return mode

def expertise_router_edge(state: VeeState) -> str:
    """
    Classify the user's intent and route to the appropriate sub-graph.
    """
    print("---ROUTING EXPERTISE---")
    expertise_chain = get_expertise_router_chain()

    user_text = state.get("last_user_text", "")
    # Get recent messages for history
    recent_msgs = state["messages"][-5:] if len(state["messages"]) >= 5 else state["messages"]
    history = get_buffer_string(recent_msgs)

    # Invoke the chain
    expertise_result = expertise_chain.invoke({
        "user_text": user_text,
        "history": history
    })

    print(f"Expertise decided: {expertise_result}")
    
    # Return the result for routing
    return expertise_result.strip().lower()

def post_planning_router_edge(state: VeeState) -> str:
    """Routes the workflow after the planning step based on the saved mode."""
    print("---ROUTING POST-PLANNING---")
    mode = state.get("mode")
    print(f"Routing based on mode: {mode}")
    
    # The return value is used by the conditional edge to route
    # to the correct next step based on the mode.
    return mode
