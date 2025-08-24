from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string

from .state import VeeState
from llms.safety import safety_triage
from llms.sensing import sense
from llms.planner import plan_next_move
from llms.drafter import draft
from llms.reviewer import review_bestie_draft, review_assistant_draft
from llms.assistant_drafter import get_assistant_drafter_chain
from llms.mode_decider import get_mode_decider_chain
import json
import re

# Import the Vee IR graph builder and its state
from .vee_ir import build_graph as build_vee_ir_graph, VeeIRState as VeeIRGraphState

# Helper Functions
# =========================================================================
def _get_formatted_messages(messages: List[HumanMessage | AIMessage]) -> List[Dict[str, str]]:
    """Formats messages into a list of dicts for LLM prompts."""
    formatted = []
    for m in messages:
        if isinstance(m, HumanMessage):
            formatted.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            formatted.append({"role": "assistant", "content": m.content})
    return formatted

# Graph Nodes
# =========================================================================

# 1. Core Pipeline Nodes (Sequential)
# -------------------------------------------------------------------------
def ingest_node(state: dict) -> dict:
    """Extracts the latest user message and saves it to the state."""
    messages = state["messages"]
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            state["last_user_text"] = m.content
            break
    return state

def safety_triage_node(state: dict) -> dict:
    """Runs safety triage on the latest user text and records the risk level."""
    text = state.get("last_user_text", "")
    tri = safety_triage(text)
    state["risk_level"] = tri.get("risk_level") if isinstance(tri, dict) else None
    return state

def sense_text_node(state: dict) -> dict:
    """Analyzes the user's text for emotional and conversational cues."""
    text = state.get("last_user_text", "")
    recent_msgs = state["messages"][-5:]
    conversation_history = get_buffer_string(recent_msgs)
    formatted_messages = _get_formatted_messages(recent_msgs)
    
    state["sensing"] = sense(text, conversation_history, formatted_messages)
    return state

def mode_decider_node(state: VeeState) -> VeeState:
    """Determines the mode ('bestie' or 'assistant') and saves it to the state."""
    print("---DECIDING MODE---")
    mode_decider_chain = get_mode_decider_chain()

    # Prepare the input for the chain
    sensing_data = json.dumps(state.get("sensing", {}), indent=2)
    conversation_history = "\n".join([f"{msg.type}: {msg.content}" for msg in state.get("messages", [])])
    latest_user_message = state.get("last_user_text", "")

    input_data = f"""Sensing Data:
    {sensing_data}

    Conversation History:
    {conversation_history}

    Latest User Message:
    {latest_user_message}""" 

    raw_mode_output = mode_decider_chain.invoke({"input": input_data}).lower()
    print(f"Raw mode output: {raw_mode_output}")

    # Clean up the output to get a valid mode
    if "assistant" in raw_mode_output:
        mode = "assistant"
    elif "bestie" in raw_mode_output:
        mode = "bestie"
    else:
        # Fallback to a default mode if neither is found
        mode = "bestie"
        print(f"Warning: Could not determine mode from output. Defaulting to '{mode}'.")

    print(f"Mode decided: {mode}")

    # Save the mode to the state for later routing
    state["mode"] = mode
    return state

def plan_next_move_node(state: VeeState) -> VeeState:
    """Runs the appropriate planner based on the mode stored in the state."""
    recent_msgs = state["messages"][-5:]
    conversation_history = get_buffer_string(recent_msgs)
    mode = state.get("mode", "bestie")
    latest_user_message = state.get("last_user_text", "")

    state["plan"] = plan_next_move(
        mode=mode,
        sensing=state["sensing"],
        conversation_history=conversation_history,
        latest_user_message=latest_user_message
    )
    return state

# 2. Expertise & Persona Nodes (Branched)
# -------------------------------------------------------------------------

# Assistant Mode Nodes
async def vee_information_guardian(state: VeeState) -> VeeState:
    """Invokes the Vee IR sub-graph to perform focused information retrieval."""
    print("---INVOKING VEE INFORMATION GUARDIAN SUBGRAPH---")

    # 1. Compile the Vee IR graph
    vee_ir_app = build_vee_ir_graph().compile()

    # 2. Extract the user query from the planner's state or fallback
    raw_query_data = state.get("plan", {}).get("question")
    if isinstance(raw_query_data, str):
        query = raw_query_data
    elif isinstance(raw_query_data, list) and raw_query_data and isinstance(raw_query_data[0], dict):
        query = raw_query_data[0].get("text", "")
    else:
        query = state.get("last_user_text", "")

    if not query:
        state["information_response"] = {"error": "Could not determine the research query."}
        return state

    # 3. Prepare the input for the Vee IR graph
    # 3. Prepare the input for the Vee IR graph, including conversation history
    ir_input_state: VeeIRGraphState = {
        "user_query": query,
        "pins": [],  # Future: Populate from main state
        "files": [], # Future: Populate from main state
        "memories": [], # Future: Populate from main state
        "conversation_history": state.get("messages", [])[-5:], # Pass last 5 messages
    }

    # 4. Invoke the sub-graph asynchronously
    final_ir_state = await vee_ir_app.ainvoke(ir_input_state, {"recursion_limit": 10})

    # 5. Store the structured answer in the main graph's state
    state["information_response"] = final_ir_state.get("structured_answer")

    print("---VEE INFORMATION GUARDIAN FINISHED---")
    return state

def assistant_drafter_node(state: dict) -> dict:
    """Invokes the assistant drafter chain to generate a response from research."""
    print("---RUNNING ASSISTANT DRAFTER---")
    # The structured response from the IR agent is the 'expert draft'
    information_response = state.get("information_response", {})
    expert_draft = information_response.get("answer", "")
    if not expert_draft:
        # If there's nothing to draft, return early
        return state

    drafter_chain = get_assistant_drafter_chain()
    history = state.get("messages", [])[-5:] # Pass last 5 messages

    # The final draft is saved back to the 'draft' key for the reviewer
    state["draft"] = drafter_chain.invoke(
        {"expert_draft": expert_draft, "conversation_history": history}
    )
    print("---ASSISTANT DRAFTER FINISHED---")
    return state

# Bestie Mode Node
def bestie_drafter_node(state: dict) -> dict:
    """Generates a response using the bestie persona ('Vee's Voice')."""
    recent_msgs = state["messages"][-5:]
    formatted_messages = _get_formatted_messages(recent_msgs)
    
    state["draft"] = draft(
        state["last_user_text"],
        state["sensing"],
        state["plan"],
        formatted_messages
    )
    return state
# 3. Finalization Nodes (Converged)
# -------------------------------------------------------------------------
def review_draft_node(state: dict) -> dict:
    """Reviews the draft for quality based on the conversation mode."""
    mode = state.get("mode", "bestie")
    draft = state.get("draft", "")

    print("---RUNNING REVIEWER---")
    print(draft)

    return state


def buttons_node(state: dict) -> dict:
    """Loads a default set of UI buttons into the state."""
    state["buttons"] = [
        [{"text": "Yes, that’s right", "data": "fit_yes"}, {"text": "Not quite", "data": "fit_no"}],
        [{"text": "Advice", "data": "mode_advice"}, {"text": "Just listening", "data": "mode_listen"}],
        [{"text": "Save", "data": "mem_save"}, {"text": "Don’t remember", "data": "mem_skip"}]
    ]
    return state

def persist_assistant_node(state: dict) -> dict:
    """Appends the final assistant message to the conversation history."""
    # We persist the original markdown draft, not the HTML formatted one,
    # to keep the history clean for the LLM.
    final_draft = state.get("draft", "")
    print(f"---PERSISTING ASSISTANT: Final draft: {final_draft}---")
    if final_draft:
        state["messages"].append(AIMessage(content=final_draft))
    return state
