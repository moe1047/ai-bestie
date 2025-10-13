from typing import Dict, List, Optional, Any, Union
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, AIMessage


class VeeState(MessagesState):
    """State for Vee's conversation workflow.

    Attributes:
        sensing (Dict): Emotion/intent detection results
        draft (str): The generated response draft.
        buttons (List): A list of UI buttons to be displayed.
        mode (str): The current operational mode ('bestie' or 'assistant').
        last_user_text (str): The latest message from the user.
        risk_level (str): Safety triage level for the latest user input.
    """

    # Intent classification
    intent: Dict[str, Any] = {}

    # Perception stack output, a list of all sense results
    senses: List[Dict[str, Any]] = []

    # Acting (response generation)
    draft: str = ""
    buttons: List[List[Dict[str, str]]] = []

    # Mode selected by the mode_decider
    mode: Optional[str] = None
    mode_history: List[str] = []
    mode_decision: Dict[str, Any] = {}

    # Safety triage result for latest input
    risk_level: Optional[str] = None

    plan: List[Dict[str, Any]] = []
    execution_result: Dict[str, Any] = {}

    # User and Session Management
    user: Optional[Dict[str, Any]] = None
    session: Optional[Dict[str, Any]] = None
    persisted_messages: List[Dict[str, Any]] = []
    reasoning: List[Dict[str, Any]] = []

