from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from utils.perception_chains import create_emotion_detection_chain
from utils.planning_chains import create_strategy_selection_chain, create_content_seed_chain
from utils.acting_chains import create_response_modulation_chain
from .state import VeeState

def analyze_emotion(state: VeeState) -> VeeState:
    """Analyze emotions in the conversation and update state.
    
    Args:
        state: Current VeeState
        
    Returns:
        Updated VeeState with new perception data
    """
    # Get last message and history
    messages = state["messages"]
    current_message = messages[-1].content if messages else ""
    
    # Create and run emotion detection chain
    chain = create_emotion_detection_chain()
    recent_history = [m.content for m in (messages[-3:] if len(messages) >= 3 else messages)]
    result = chain.invoke({
        "conversation_history": "\n".join(recent_history),
        "current_message": current_message
    })
    
    # Store current perception state before updating
    current_perception = state["perception"]["current"].copy()
    if current_perception["emotion"]:  # If there's existing data
        current_perception["timestamp"] = datetime.now().isoformat()
        state["perception"]["history"].append(current_perception)
    
    # Update current perception
    state["perception"]["current"].update({
        "emotion": result.emotion,
        "tone": result.tone,
        "notes": result.notes,
        "timestamp": datetime.now().isoformat()
    })
    
    return state

def select_strategy(state: VeeState) -> VeeState:
    """Select conversation strategy based on current state.
    
    Args:
        state: Current VeeState
        
    Returns:
        Updated VeeState with new planning data
    """
    # Get required inputs
    messages = state["messages"]
    current_message = messages[-1].content if messages else ""
    recent_history = messages[-3:] if len(messages) >= 3 else messages
    
    # Create and run strategy selection chain
    chain = create_strategy_selection_chain()
    result = chain.invoke({
        "current_message": current_message,
        "emotion_analysis": state["perception"]["current"],
        "conversation_history": recent_history
    })
    
    # Ensure strategy is lowercase
    result.strategy = result.strategy.lower()
    
    # Store current planning state before updating
    current_planning = state["planning"]["current"].copy()
    if current_planning["strategy"]:  # If there's existing data
        current_planning["timestamp"] = datetime.now().isoformat()
        state["planning"]["history"].append(current_planning)
    
    # Update current planning
    state["planning"]["current"].update({
        "strategy": result.strategy,
        "rationale": result.rationale,
        "timestamp": datetime.now().isoformat()
    })
    
    return state

def generate_content_seed(state: VeeState) -> VeeState:
    """Generate content seed based on selected strategy.
    
    Args:
        state: Current VeeState
        
    Returns:
        Updated VeeState with content seed
    """
    # Get required inputs
    messages = state["messages"]
    recent_history = messages[-3:] if len(messages) >= 3 else messages
    
    # Create and run content seed chain
    chain = create_content_seed_chain()
    result = chain.invoke({
        "strategy": state["planning"]["current"],
        "emotion_analysis": state["perception"]["current"],
        "conversation_history": recent_history
    })
    
    # Update planning state with content seed
    state["planning"]["current"].update({
        "content_seed": result.seed,
        "tag": result.tag,
        "timestamp": datetime.now().isoformat()
    })
    
    return state

def modulate_response(state: VeeState) -> VeeState:
    """Generate and modulate the final response.
    
    Args:
        state: Current VeeState
        
    Returns:
        Updated VeeState with new AI message
    """
    # Get required inputs
    messages = state["messages"]
    recent_history = messages[-8:] if len(messages) >= 8 else messages
    
    # Create and run response modulation chain
    chain = create_response_modulation_chain()
    result = chain.invoke({
        "content_seed": state["planning"]["current"]["content_seed"],
        "emotion_analysis": f"Emotion: {state['perception']['current']['emotion']}, Tone: {state['perception']['current']['tone']}",
        "conversation_history": recent_history
    })
    
    # Append modulated response to messages
    state["messages"].append(AIMessage(content=result))
    
    return state
