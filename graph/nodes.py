from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string

from .state import VeeState
from llms.safety import safety_triage
from llms.sensing import sense
from llms.planner import plan_next_move
from llms.drafter import draft
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
    print("\n--- 1. INGEST NODE ---")
    messages = state["messages"]
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            state["last_user_text"] = m.content
            break
    print(f"Ingest complete. Last user text: '{state.get('last_user_text', '')[:50]}...'\n")
    return state

def safety_triage_node(state: dict) -> dict:
    """Runs safety triage on the latest user text and records the risk level."""
    print("\n--- 2. SAFETY TRIAGE NODE ---")
    text = state.get("last_user_text", "")
    tri = safety_triage(text)
    state["risk_level"] = tri.get("risk_level") if isinstance(tri, dict) else None
    print(f"Safety triage complete. Risk level: {state.get('risk_level')}\n")
    return state

def sense_text_node(state: dict) -> dict:
    """Analyzes the user's text for emotional and conversational cues."""
    print("\n--- 3. SENSE TEXT NODE ---")
    text = state.get("last_user_text", "")
    recent_msgs = state["messages"][-5:]
    conversation_history = get_buffer_string(recent_msgs)
    formatted_messages = _get_formatted_messages(recent_msgs)
    
    state["sensing"] = sense(text, conversation_history, formatted_messages)
    print(f"Sensing complete. Sensing data present: {'sensing' in state}\n")
    return state

def mode_decider_node(state: VeeState) -> VeeState:
    """Determines the mode ('bestie' or 'assistant') and saves it to the state."""
    print("\n--- 4. MODE DECIDER NODE ---")
    mode_decider_chain = get_mode_decider_chain()

    # Prepare the input for the chain
    sensing_data = json.dumps(state.get("sensing", {}), indent=2)
    conversation_history = "\n".join([f"{msg.type}: {msg.content}" for msg in state.get("messages", [])[-5:]])
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

    print(f"Mode decided: {mode}\n")

    # Save the mode to the state for later routing
    state["mode"] = mode
    return state

def plan_next_move_node(state: VeeState) -> VeeState:
    """Runs the appropriate planner based on the mode stored in the state."""
    print("\n--- 5. PLAN NEXT MOVE NODE ---")
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
    print(f"Planning complete. Plan created for mode: {state.get('mode')}. Plan content: {str(state.get('plan', {}))[:100]}...\n")
    return state

# 2. Expertise & Persona Nodes (Branched)
# -------------------------------------------------------------------------

# Assistant Mode Nodes
async def vee_information_guardian(state: VeeState) -> VeeState:
    """Invokes the Vee IR sub-graph to perform focused information retrieval."""
    print("\n--- 6a. VEE INFORMATION GUARDIAN NODE ---")

    # 1. Compile the Vee IR graph
    # Note: Compiling the graph on every invocation might be inefficient.
    # Consider moving this to a higher level if performance becomes an issue.
    vee_ir_app = build_vee_ir_graph().compile()

    # 2. Extract the latest user query from the state
    query = state.get("last_user_text")
    if not query:
        print("Error: 'last_user_text' not found in state.")
        state["draft"] = "I'm sorry, I had trouble understanding your request. Could you please rephrase?"
        return state

    # 3. Prepare the input for the Vee IR graph
    ir_input_state: VeeIRGraphState = {
        "user_query": query,
        "conversation_history": state.get("messages", [])[-5:],
    }
    print(f"Invoking IR graph with state: user_query='{ir_input_state['user_query']}'")

    # 4. Invoke the sub-graph asynchronously
    try:
        final_ir_state = await vee_ir_app.ainvoke(ir_input_state, {"recursion_limit": 15})
        # 5. Store the final answer in the main graph's 'draft' state
        state["draft"] = final_ir_state.get("final_answer")
        print(f"Vee IR subgraph finished. Final answer: '{state.get('draft', '')[:50]}...'\n")
    except Exception as e:
        print(f"Error invoking Vee IR subgraph: {e}")
        state["draft"] = "I encountered an issue while trying to find that information. Could you try asking in a different way?"

    return state

# Bestie Mode Node
def bestie_drafter_node(state: dict) -> dict:
    """Generates a response using the bestie persona ('Vee's Voice')."""
    print("\n--- 6b. BESTIE DRAFTER NODE ---")
    recent_msgs = state["messages"][-5:]
    formatted_messages = _get_formatted_messages(recent_msgs)
    
    # Extract the core content seed from the plan to provide cleaner context
    plan_object = state.get("plan", {})
    content_seed = plan_object.get("content_seed", "")

    state["draft"] = draft(
        state["last_user_text"],
        state["sensing"],
        content_seed,  # Pass the clean content seed instead of the raw plan
        formatted_messages
    )
    print(f"Bestie drafting complete. Draft: '{state.get('draft', '')[:50]}...'\n")
    return state
# 3. Finalization Nodes (Converged)
# -------------------------------------------------------------------------


def buttons_node(state: dict) -> dict:
    """Loads a default set of UI buttons into the state."""
    print("\n--- 7. BUTTONS NODE ---")
    state["buttons"] = [
        [{"text": "Yes, that’s right", "data": "fit_yes"}, {"text": "Not quite", "data": "fit_no"}],
        [{"text": "Advice", "data": "mode_advice"}, {"text": "Just listening", "data": "mode_listen"}],
        [{"text": "Save", "data": "mem_save"}, {"text": "Don’t remember", "data": "mem_skip"}]
    ]
    print("Button loading complete.\n")
    return state

def persist_assistant_node(state: dict) -> dict:
    """Appends the final assistant message(s) to the conversation history."""
    print("\n--- 8. PERSIST ASSISTANT NODE ---")
    final_draft = state.get("draft", "")
    print(f"Persisting draft: '{final_draft[:50]}...'\n")
    state["messages"].append(AIMessage(content=final_draft))
    return state
