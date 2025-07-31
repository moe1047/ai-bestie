from typing import Dict, List, Optional, Any, Union
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, AIMessage

class VeeState(MessagesState):
    """State for Vee's conversation workflow.
    
    Attributes:
        session (Dict): Session metadata and context
        user (Dict): User state and preferences
        perception (Dict): Emotion detection results
        planning (Dict): Strategy and content planning
        acting (Dict): Response generation and modulation
        next_node (str): Next node to execute
        checkpoint (str): State serialization timestamp
    """
    
    # Session info
    session: Dict[str, Any] = {
        "start_time": None,
        "last_update": None,
        "context": {}
    }
    
    # User state
    user: Dict[str, Any] = {
        "name": None,
        "phone_number": None,
    }
    
    # Perception (emotion detection)
    perception: Dict[str, Any] = {
        "current": {  # Current emotional state
            "emotion": None,
            "tone": None,
            "notes": None,
            "timestamp": None
        },
        "history": []  # List of past emotional states with timestamps
    }
    
    # Planning (strategy & content)
    planning: Dict[str, Any] = {
        "current": {  # Current planning state
            "strategy": None,
            "rationale": None,
            "content_seed": None,
            "tag": None,
            "timestamp": None
        },
        "history": []  # List of past planning decisions with timestamps
    }
    
    # Acting (response generation)
    acting: Dict[str, Any] = {}
    
    # Workflow control
    next_node: Optional[str] = None
    checkpoint: Optional[str] = None