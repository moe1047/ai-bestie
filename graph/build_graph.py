from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from .state import VeeState
from langgraph.graph import END
from .nodes import (
    persist_user_message,
    perception_node,
    vee_self_node,
)


def build_graph(checkpointer=None):
    """Build the Vee conversation workflow graph.

    Returns:
        A compiled LangGraph workflow with a SQLite checkpointer.
    """
    workflow = StateGraph(VeeState)

    # 1. Define Nodes
    # =========================================================================
    workflow.add_node("persist", persist_user_message)
    workflow.add_node("perceive", perception_node)
    workflow.add_node("vee_self", vee_self_node)

    # 2. Define Edges
    # =========================================================================
    workflow.set_entry_point("persist")
    workflow.add_edge("persist", "perceive")
    workflow.add_edge("perceive", "vee_self")
    workflow.add_edge("vee_self", END)

    # 3. Compile the graph
    # =========================================================================
    return workflow.compile(checkpointer=checkpointer)
