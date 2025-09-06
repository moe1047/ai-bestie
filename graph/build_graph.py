from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from .state import VeeState
from .nodes import (
    ingest_node, safety_triage_node, sense_text_node, mode_decider_node, 
    bestie_drafter_node, buttons_node, persist_assistant_node, 
    vee_information_guardian
)
from .edges import mode_decider_edge

def build_graph(checkpointer):
    """Build the Vee conversation workflow graph.

    Returns:
        A compiled LangGraph workflow with a SQLite checkpointer.
    """
    workflow = StateGraph(VeeState)

    # 1. Define Nodes
    # =========================================================================
    # Core pipeline nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("safety", safety_triage_node)
    workflow.add_node("perception", sense_text_node)
    workflow.add_node("mode_decider", mode_decider_node)

    # Expertise and Persona nodes
    workflow.add_node("vee_information_guardian", vee_information_guardian)
    workflow.add_node("bestie_drafter", bestie_drafter_node)

    # Finalization nodes
    workflow.add_node("load_buttons", buttons_node)
    workflow.add_node("persist_assistant", persist_assistant_node)

    # 2. Define Edges
    # =========================================================================
    workflow.set_entry_point("ingest")

    # Core flow
    workflow.add_edge("ingest", "safety")
    workflow.add_edge("safety", "perception")
    workflow.add_edge("perception", "mode_decider")

    # Mode-based routing (to the unified planner)
    workflow.add_conditional_edges(
        "mode_decider",
        mode_decider_edge,
        {
            "assistant": "vee_information_guardian",  # Assistant mode uses the IR agent
            "bestie": "bestie_drafter",          # Bestie mode goes direct to drafting
        }
    )

    # Converge paths to final steps
    workflow.add_edge("vee_information_guardian", "persist_assistant")  # End assistant flow here
    workflow.add_edge("bestie_drafter", "load_buttons")
    workflow.add_edge("load_buttons", "persist_assistant")

    # 3. Compile the graph
    # =========================================================================
    return workflow.compile(checkpointer=checkpointer)