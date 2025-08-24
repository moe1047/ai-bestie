from typing import Dict, List, Optional, Any, Union
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, AIMessage

class VeeState(MessagesState):
    """State for Vee's conversation workflow.
    
    Attributes:
        session (Dict): Session metadata and context
        user (Dict): User state and preferences
        sensing (Dict): Emotion/intent detection results
        planning (Dict): Strategy and content planning
        acting (Dict): Response generation and modulation
        risk_level (str): Safety triage level for latest user input
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
        "chat_id": None,
    }
    
    # Sensing (emotion/intent detection)
    sensing: Dict[str,Any] = {}
    
    # Planning (strategy & content)
    plan: Dict[str,Any] = {}
    
    # Acting (response generation)
    draft: str = ""
    care: Dict[str, float] | Dict[str,Any] = {}
    buttons: List[List[Dict[str,str]]] = []

    # Mode selected by the mode_decider
    mode: Optional[str] = None
    
    # Workflow control
    next_node: Optional[str] = None
    checkpoint: Optional[str] = None

    # Convenience cache of the latest user text extracted by node_ingest
    last_user_text: Optional[str] = None

    # Safety triage result for latest input
    risk_level: Optional[str] = None

    # Output from the information guardian sub-graph
    information_response: Optional[dict] = None