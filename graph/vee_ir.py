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
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from models.vee_ir import (
    VeeInformationIntent,
    SubTask,
    UnifiedGoal,
    Plan,
    VeeIRState,
)
from utils.formatter import format_for_telegram

# Load environment variables
load_dotenv()

# ===============================
# Prompts
# ===============================

def load_prompt(file_name: str) -> str:
    """Loads a prompt from the vee_ir prompts directory."""
    import os
    # Assumes vee_ir.py is in ai-bestie/graph, and prompts are in ai-bestie/prompts/vee_ir
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # This path goes up one level from 'graph' and then into 'prompts/vee_ir'
    prompt_path = os.path.join(current_dir, '..', 'prompts', 'vee_ir', file_name)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # A fallback or more robust error handling could be implemented here
        return f"Error: Prompt file '{file_name}' not found."

CLASSIFIER_PROMPT = load_prompt('classifier_prompt.md')
UNIFIED_GOAL_EXTRACTOR_PROMPT = load_prompt('unified_goal_extractor_prompt.md')
PLANNER_PROMPT = load_prompt('planner_prompt.md')
KNOWLEDGE_GENERATOR_PROMPT = load_prompt('knowledge_generator_prompt.md')

# ===============================
# LLM Client
# ===============================
def make_llm(model: str = "gpt-4o", temperature: float = 0.0) -> ChatOpenAI:
    """Factory for the chat model."""
    return ChatOpenAI(model=model, temperature=temperature)

# ===============================
# Graph Nodes
# ===============================
def node_classify_intent(state: VeeIRState) -> VeeIRState:
    """Classifier (Intent Router)"""
    print("\n--- Classify Intent Node ---")
    print(f"Received state keys: {list(state.keys())}")
    
    llm = make_llm()
    
    # Get the last 5 messages for context
    recent_messages = state.get("conversation_history", [])[-5:]
    conversation_history_str = get_buffer_string(recent_messages)
    
    prompt_input = f"""Conversation History:
{conversation_history_str}

Latest user message: {state['user_query']}"""
    
    prompt = f"{CLASSIFIER_PROMPT}\n\n{prompt_input}"
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Parse the JSON output from the classifier
    try:
        intent_data = json.loads(response.content.strip())
        state["information_intent"] = intent_data
    except (json.JSONDecodeError, KeyError):
        # Handle cases where the output is not valid JSON or is missing keys
        # For now, we'll fall back to a default or handle the error
        print("Error: Could not parse intent from LLM response.")
        # Set a default or raise an error, depending on desired behavior
        state["information_intent"] = {"intent": "Learn", "reasoning": "Fallback due to parsing error."}
        
    print(f"State after classification: intent='{state.get('information_intent', {}).get('intent')}'")
    return state

def node_unified_goal_extractor(state: VeeIRState) -> VeeIRState:
    """Extracts the user's goal and breaks it down into sub-tasks."""
    print("\n--- Unified Goal Extractor Node ---")
    print(f"Received state keys: {list(state.keys())}")

    llm = make_llm()

    parser = PydanticOutputParser(pydantic_object=UnifiedGoal)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", UNIFIED_GOAL_EXTRACTOR_PROMPT),
        ("human", "* Latest user message: {user_query}\n* Classified intent: {user_intent}")
    ])
    
    chain = prompt_template | llm | parser

    try:
        goal_data = chain.invoke({
            "user_query": state['user_query'],
            "user_intent": state['information_intent']['intent']
        })
        state["unified_goal"] = goal_data.model_dump()

    except Exception as e:
        print(f"Error: Could not parse unified goal from LLM response: {e}")
        state["unified_goal"] = {
            "goal": "Fallback Goal",
            "sub_tasks": [],
            "clarification_needed": True,
            "missing_info": ["Could not process request."]
        }

    print(f"State after goal extraction: goal='{state.get('unified_goal', {}).get('goal')}'")
    return state

def node_plan_response(state: VeeIRState) -> VeeIRState:
    """Planner Module"""
    print("\n--- Plan Response Node ---")
    print(f"Received state keys: {list(state.keys())}")

    llm = make_llm()
    
    sub_task_list = [f"- {task['text']}" for task in state["unified_goal"].get("sub_tasks", [])]
    sub_tasks_str = "\n".join(sub_task_list)

    user_query = state["user_query"]
    user_intent = state["information_intent"]["intent"]
    goal = state["unified_goal"].get("goal", "")

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", PLANNER_PROMPT),
        ("human", "Here is the context for the plan:\n\n* Latest user message: {user_query}\n* Classified intent: {user_intent}\n* Extracted goal: {goal}\n* Extracted sub-tasks:\n{sub_tasks}")
    ])
    
    chain = prompt_template | llm
    
    parser = PydanticOutputParser(pydantic_object=Plan)
    chain = prompt_template | llm | parser

    try:
        plan_data = chain.invoke({
            "user_query": user_query,
            "user_intent": user_intent,
            "goal": goal,
            "sub_tasks": sub_tasks_str
        })
        state["plan"] = plan_data.model_dump()

    except Exception as e:
        print(f"Error: Could not parse plan from LLM response: {e}")
        # Fallback plan
        state["plan"] = {
            "note": "Fallback plan due to a parsing error.",
            "tasks": [],
            "clarification_needed": True,
            "missing_info": ["Could not process the planning step."]
        }
        
    print(f"State after planning: plan_note='{state.get('plan', {}).get('note')}'")
    return state
def node_knowledge_generator(state: VeeIRState) -> VeeIRState:
    """Generator Module"""
    print("\n--- Knowledge Generator Node ---")
    print(f"Received state keys: {list(state.keys())}")
    
    llm = make_llm(temperature=0.4)

    plan_str = json.dumps(state["plan"], indent=2)

    prompt = KNOWLEDGE_GENERATOR_PROMPT.replace("{plan}", plan_str)

    response = llm.invoke([HumanMessage(content=prompt)])
    formatted_answer = format_for_telegram(response.content.strip())
    state["final_answer"] = formatted_answer
    
    print(f"State after generation: final_answer='{state.get('final_answer', '')[:50]}...'")
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
