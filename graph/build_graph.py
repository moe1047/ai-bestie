from typing import Dict, Any
from datetime import datetime
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage
from .state import VeeState
from .nodes import analyze_emotion, select_strategy, generate_content_seed, modulate_response
from langgraph.checkpoint.memory import InMemorySaver
def build_graph() -> Graph:
    """Build the Vee conversation workflow graph.
    
    Returns:
        Compiled LangGraph workflow
    """
    # Create workflow definition
    workflow = StateGraph(VeeState)
    
    # Add nodes
    workflow.add_node("analyze_emotion", analyze_emotion)
    workflow.add_node("select_strategy", select_strategy)
    workflow.add_node("generate_content_seed", generate_content_seed)
    workflow.add_node("modulate_response", modulate_response)
    
    # Define linear edges
    workflow.add_edge("analyze_emotion", "select_strategy")
    workflow.add_edge("select_strategy", "generate_content_seed")
    workflow.add_edge("generate_content_seed", "modulate_response")
    workflow.add_edge("modulate_response", "__end__")
    
    # Set entry point
    workflow.set_entry_point("analyze_emotion")
    # Create memory saver for state persistence
    store = InMemorySaver()
    # Compile
    return workflow.compile(store)

def get_default_state() -> VeeState:
    """Create a default state with initial user message.
    
    Returns:
        VeeState initialized with default values
    """
    # Create initial state
    state = VeeState(
        messages=[
            HumanMessage(content="Hi")
        ],
        session={
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "context": {}
        },
        user={
            "name": None,
            "phone_number": None
        },
        perception={
            "current": {
                "emotion": None,
                "tone": None,
                "notes": None,
                "timestamp": None
            },
            "history": []
        },
        planning={
            "current": {
                "strategy": None,
                "rationale": None,
                "content_seed": None,
                "tag": None,
                "timestamp": None
            },
            "history": []
        },
        acting={},
        next_node=None,
        checkpoint=datetime.now().isoformat()
    )
    
    return state