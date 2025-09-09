from pydantic import BaseModel, Field
from typing import List, Literal

class ResponseComponent(BaseModel):
    """Defines a single component of a conversational response."""
    type: Literal[
        "validate", 
        "reflect", 
        "share_insight", 
        "normalize", 
        "ask_open_question", 
        "ask_clarifying_question"
    ] = Field(..., description="The specific conversational action to take.")
    focus: str = Field(..., description="A brief, specific instruction for the drafter on what to focus on for that component.")

class BestiePlan(BaseModel):
    """Defines the conversational plan for the Bestie persona's response."""
    strategy_note: str = Field(..., description="A concise, high-level summary of the conversational goal for this turn.")
    response_components: List[ResponseComponent] = Field(..., min_items=2, max_items=3, description="An array of 2-3 components that will make up the final message.")
