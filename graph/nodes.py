from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string

from .state import VeeState
from llms.perceive import perceive
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from memory import crud, schemas
from llms.vee_self import reply as vee_self_reply
from datetime import datetime

# Import the Vee IR graph builder and its state
# from .vee_ir import build_graph as build_vee_ir_graph, VeeIRState as VeeIRGraphState # Commented out as vee_information_guardian is not used


# Graph Nodes
# =========================================================================


# 1. Core Pipeline Nodes (Sequential)
# -------------------------------------------------------------------------


from langchain_core.runnables import ConfigurableField

def persist_user_message(state: dict) -> dict:
    """Extracts the last user message and saves it directly to the database."""
    print("\n--- PERSIST USER MESSAGE ---")
    messages = state["messages"]
    # TODO: Implement dynamic session management instead of hardcoding session_id.
    session_id = 1
    if not session_id:
        print("Warning: 'session' not found in state for persist_user_message. Skipping message persistence.")
        return state

    # 1. Find the latest user message from the messages list
    if not messages or not isinstance(messages[-1], HumanMessage):
        print("Warning: Last message is not a user message. Skipping persistence.")
        return state
    last_user_message = messages[-1]

    # 2. Save the message directly to the database
    message_data = schemas.Message(
        id=0,  # Will be set by DB
        session_id=session_id,
        role="user",
        content=last_user_message.content,
        timestamp=datetime.now(timezone.utc),
        mode=None, # Mode is not determined at this stage
    )

    message_id = crud.add_message(message_data)
    print(f"Saved user message (ID: {message_id}): '{last_user_message.content[:50]}...'")

    # Ensure 'persisted_messages' is initialized
    if "persisted_messages" not in state or not isinstance(state["persisted_messages"], list):
        state["persisted_messages"] = []

    # Append the new message to the list, now including the ID
    new_message_record = message_data.dict()
    new_message_record["id"] = message_id
    state["persisted_messages"].append(new_message_record)

    return state



def perception_node(state: dict) -> dict:
    """Runs the full perception stack on the latest user message and conversation history."""
    print("\n--- 3. PERCEPTION NODE ---")

    # 1. Prepare the context for the perception model
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], HumanMessage):
        print("Warning: Last message is not a user message in perception_node.")
        return state
    last_user_message = messages[-1]

    conversation_history = get_buffer_string(state.get("messages", [])[-10:])

    timestamp = state.get("persisted_messages", [])[-1].get("timestamp", datetime.now(timezone.utc))

    context = {
        "latest_message": {
            "timestamp_utc": timestamp.isoformat(),
            "channel": "text",
            "text": last_user_message.content,
            "paralinguistics": { "pitch": None, "energy": None, "pause_ms": None }
        },
        "conversation_last_10": conversation_history,
        "user_profile": {
            "name": "Moe",
        },
        "session_summaries_last_2": [] # Hardcoded as empty for now
    }

    # 2. Call the perception function
    sense_result = perceive(context)
    if "senses" not in state or not isinstance(state["senses"], list):
        state["senses"] = []
    state["senses"].append(sense_result)

    # Also store key perception results in the top-level state for easier access
    state["risk_level"] = sense_result.get("safety", {}).get("risk_level", "none")

    # 3. Save the sensing data to the database
    try:
        last_persisted_message = state.get("persisted_messages", [])[-1]
        message_id = last_persisted_message.get("id")

        if message_id:
            sensing_data = schemas.SensingData(
                message_id=message_id,
                dialogue_act=sense_result.get("discourse", {}).get("dialogue_act", [None])[0],
                primary_intent=sense_result.get("intent", {}).get("primary"),
                sub_intent=sense_result.get("intent", {}).get("sub"),
                sentiment=sense_result.get("affect", {}).get("sentiment"),
                valence=sense_result.get("affect", {}).get("valence"),
                arousal=sense_result.get("affect", {}).get("arousal"),
                risk_level=sense_result.get("safety", {}).get("risk_level"),
                distress_hint=sense_result.get("safety", {}).get("distress_hint"),
                inference=sense_result.get("pragmatics", {}).get("inference"),
                needs_clarification=sense_result.get("pragmatics", {}).get("needs_clarification"),
                sarcasm_possible=sense_result.get("pragmatics", {}).get("sarcasm_possible"),
                raw_output=str(sense_result), # Store the raw dict as a string
            )
            sensing_id = crud.create_sensing_data(sensing_data)
            print(f"Saved sensing data (ID: {sensing_id}) for message (ID: {message_id}).")
        else:
            print("Warning: Could not find message_id in persisted_messages. Skipping sensing data persistence.")
    except (IndexError, KeyError) as e:
        print(f"Error accessing persisted message data: {e}. Skipping sensing data persistence.")


    print(f"Sense data: {sense_result}\n")
    return state


def vee_self_node(state: dict) -> dict:
    """Generates the AI's response using the Vee Self model."""
    print("\n--- VEE SELF NODE ---")

    # 1. Assemble the context for the Vee Self prompt
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], HumanMessage):
        print("Warning: Last message is not a user message in vee_self_node.")
        return state
    last_user_message = messages[-1]

    session_id = 1
    # conversation_history = get_buffer_string(state.get("messages", [])[-10:])
    conversation_history = crud.get_recent_messages_as_string(session_id, limit=10, timezone_str="Europe/London")

    sense_data = state.get("senses", [{}])[-1]

    # Get current time in the specified timezone
    london_tz = ZoneInfo("Europe/London")
    now_in_london = datetime.now(london_tz)

    timestamp = state.get("persisted_messages", [])[-1].get("timestamp", datetime.now(timezone.utc))

    context = {
        "latest_message": {
            "timestamp_utc": timestamp.isoformat(),
            "channel": "text",
            "text": last_user_message.content,
        },
        "conversation_last_10": conversation_history,
        "your_human_companion_information": {
            "name": "Moe",
            "timezone": "Europe/London",
            "locale": "en-GB",
            "his_current_time": now_in_london.strftime("%H:%M"),
            "his_current_date": now_in_london.strftime("%Y-%m-%d"),
            "his_current_day": now_in_london.strftime("%A"),
            "channel_you_both_communicating_on": "Telegram",
        },
        "perception_data": sense_data
    }

    # 2. Call the reply function
    final_response = vee_self_reply(context)
    print(f"Vee Self generation complete. Final response: '{final_response[:100]}...'" )

    # 3. Persist the AI's response to the database
    # TODO: Implement dynamic session management instead of hardcoding session_id.
    session_id = 1
    if session_id:
        ai_message_data = schemas.Message(
            session_id=session_id,
            role="vee",
            content=final_response,
            timestamp=datetime.now(timezone.utc),
            # TODO: Implement proper mode handling.
            mode=state.get("mode"),
        )
        ai_message_id = crud.add_message(ai_message_data)
        print(f"Saved AI message (ID: {ai_message_id}): '{final_response[:50]}...'")

        # Append the persisted AI message to the state for consistency
        ai_message_record = ai_message_data.dict()
        ai_message_record["id"] = ai_message_id
        state["persisted_messages"].append(ai_message_record)
    else:
        print("Warning: 'session' not found in state. Skipping AI message persistence.")

    # 4. Append the AI's response to the messages list for the next turn
    messages = state.get("messages", []) + [AIMessage(content=final_response)]
    return {"messages": messages}


# async def vee_information_guardian(state: VeeState) -> VeeState:
#     """Invokes the Vee IR sub-graph to perform focused information retrieval."""
#     print("\n--- 6a. VEE INFORMATION GUARDIAN NODE ---")
#
#     # 1. Compile the Vee IR graph
#     # Note: Compiling the graph on every invocation might be inefficient.
#     # Consider moving this to a higher level if performance becomes an issue.
#     vee_ir_app = build_vee_ir_graph().compile()
#
#     # 2. Extract the latest user query from the state
#     query = state.get("last_user_text")
#     if not query:
#         print("Error: 'last_user_text' not found in state.")
#         state["draft"] = (
#             "I'm sorry, I had trouble understanding your request. Could you please rephrase?"
#         )
#         return state
#
#     # 3. Prepare the input for the Vee IR graph
#     ir_input_state: VeeIRGraphState = {
#         "user_query": query,
#         "conversation_history": state.get("messages", [])[-5:],
#     }
#     print(f"Invoking IR graph with state: user_query='{ir_input_state['user_query']}'")
#
#     # 4. Invoke the sub-graph asynchronously
#     try:
#         final_ir_state = await vee_ir_app.ainvoke(
#             ir_input_state, {"recursion_limit": 15}
#         )
#         # 5. Store the final answer in the main graph's 'draft' state
#         state["draft"] = final_ir_state.get("final_answer")
#         print(
#             f"Vee IR subgraph finished. Final answer: '{state.get('draft', '')[:50]}...'\n"
#         )
#     except Exception as e:
#         print(f"Error invoking Vee IR subgraph: {e}")
#         state["draft"] = (
#             "I encountered an issue while trying to find that information. Could you try asking in a different way?"
#         )
#
#     return state

# def buttons_node(state: dict) -> dict:
#     """Loads a default set of UI buttons into the state."""
#     print("\n--- 7. BUTTONS NODE ---")
#     state["buttons"] = [
#         [
#             {"text": "Yes, that’s right", "data": "fit_yes"},
#             {"text": "Not quite", "data": "fit_no"},
#         ],
#         [
#             {"text": "Advice", "data": "mode_advice"},
#             {"text": "Just listening", "data": "mode_listen"},
#         ],
#         [
#             {"text": "Save", "data": "mem_save"},
#             {"text": "Don’t remember", "data": "mem_skip"},
#         ],
#     ]
#     print("Button loading complete.\n")
#     return state
