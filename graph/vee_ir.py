# -*- coding: utf-8 -*-
"""
Vee-IR (Information Guardian) - Reworked Multi-Step Graph

This file implements a sophisticated, multi-step LangGraph agent for information
retrieval. It breaks down the task into distinct stages to ensure responses are
accurate, compact, and aligned with user intent.

Key Components:
- State: `VeeIRState` defines the data structure for the pipeline.
- Prompts: A suite of prompts for each stage of the process.
- Nodes: Functions for each step (Classifier, Planner, Generator, etc.).
- Graph: A sequential workflow connecting the nodes.
"""
from __future__ import annotations

import json
import re
from typing import List, Literal, TypedDict, Dict, Any, NotRequired

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages.utils import get_buffer_string
from langchain_core.output_parsers import PydanticOutputParser
from llms.ir import (
    classify_intent,
    extract_goal,
    plan_ir_response,
    generate_knowledge,
)
from pydantic import BaseModel, Field
from models.vee_ir import (
    VeeInformationIntent,
    SubTask,
    UnifiedGoal,
    Plan,
    VeeIRState,
)
from utils.formatter import format_for_telegram
from utils.file_io import load_prompt

# Load environment variables
load_dotenv()

# ===============================
# Prompts
# ===============================





# ===============================
# Graph Nodes
# ===============================
def node_classify_intent(state: VeeIRState) -> VeeIRState:
    """Classifier (Intent Router)"""
    print("\n--- Classify Intent Node ---")

    recent_messages = state.get("conversation_history", [])[-5:]
    conversation_history_str = get_buffer_string(recent_messages)

    intent_data = classify_intent(
        conversation_history=conversation_history_str, user_query=state["user_query"]
    )
    state["information_intent"] = intent_data

    print(
        f"State after classification: intent='{state.get('information_intent', {}).get('intent')}'"
    )
    return state


def node_unified_goal_extractor(state: VeeIRState) -> VeeIRState:
    """Extracts the user's goal and breaks it down into sub-tasks."""
    print("\n--- Unified Goal Extractor Node ---")

    recent_messages = state.get("conversation_history", [])[-5:]
    conversation_history_str = get_buffer_string(recent_messages)

    goal_data = extract_goal(
        conversation_history=conversation_history_str,
        user_query=state["user_query"],
        user_intent=state["information_intent"]["intent"],
    )
    state["unified_goal"] = goal_data

    print(
        f"State after goal extraction: goal='{state.get('unified_goal', {}).get('goal')}'"
    )
    return state


def node_plan_response(state: VeeIRState) -> VeeIRState:
    """Planner Module"""
    print("\n--- Plan Response Node ---")

    recent_messages = state.get("conversation_history", [])[-5:]
    conversation_history_str = get_buffer_string(recent_messages)

    sub_task_list = [
        f"- {task['text']}" for task in state["unified_goal"].get("sub_tasks", [])
    ]
    sub_tasks_str = "\n".join(sub_task_list)

    plan_data = plan_ir_response(
        conversation_history=conversation_history_str,
        user_query=state["user_query"],
        user_intent=state["information_intent"]["intent"],
        goal=state["unified_goal"]["goal"],
        sub_tasks=sub_tasks_str,
    )
    state["plan"] = plan_data

    print(f"State after planning: plan_note='{state.get('plan', {}).get('note')}'")
    return state


def node_knowledge_generator(state: VeeIRState) -> VeeIRState:
    """Generator Module"""
    print("\n--- Knowledge Generator Node ---")

    plan_str = json.dumps(state["plan"], indent=2)
    recent_messages = state.get("conversation_history", [])[-5:]
    conversation_history_str = get_buffer_string(recent_messages)

    response = generate_knowledge(
        conversation_history=conversation_history_str, plan=plan_str
    )

    formatted_answer = format_for_telegram(response)
    state["final_answer"] = formatted_answer

    print(
        f"State after generation: final_answer='{state.get('final_answer', '')[:50]}...'"
    )
    return state


# ===============================
# Graph Assembly
# ===============================
def build_graph() -> StateGraph:
    """Builds the Information Guardian LangGraph state machine."""
    graph = StateGraph(VeeIRState)
    graph.add_node("classifier", node_classify_intent)
    graph.add_node("unified_goal_extractor", node_unified_goal_extractor)
    graph.add_node("planner", node_plan_response)
    graph.add_node("knowledge_generator", node_knowledge_generator)

    graph.add_edge(START, "classifier")
    graph.add_edge("classifier", "unified_goal_extractor")
    graph.add_edge("unified_goal_extractor", "planner")
    graph.add_edge("planner", "knowledge_generator")
    graph.add_edge("knowledge_generator", END)

    return graph
