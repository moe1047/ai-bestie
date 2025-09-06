from __future__ import annotations
from typing import List, Literal, TypedDict, Dict, Any, NotRequired
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

# ===============================
# State Definition
# ===============================
class VeeInformationIntent(TypedDict):
    """Represents the output of the information intent classifier."""
    intent: Literal["Learn", "Solve", "Create", "Update", "Reflect"]
    reasoning: str

class SubTask(BaseModel):
    """A single sub-task for the goal."""
    text: str = Field(description="A single, atomic sub-task.")

class UnifiedGoal(BaseModel):
    """Represents the unified goal and its breakdown."""
    goal: str = Field(description="The user's high-level goal.")
    sub_tasks: List[SubTask] = Field(description="A list of atomic sub-tasks.")
    clarification_needed: bool = Field(description="Whether the user needs to provide more information.")
    missing_info: List[str] = Field(description="A list of questions to ask the user for clarification.")

class Plan(BaseModel):
    """Represents the plan for generating the response."""
    note: str = Field(description="A high-level note for the generator.")
    tasks: List[Dict[str, Any]] = Field(description="A list of tasks for the generator.")
    clarification_needed: bool = Field(description="Whether clarification is still needed.")
    missing_info: List[str] = Field(description="A list of missing information.")

class VeeIRState(TypedDict, total=False):
    """Defines the state for the Information Guardian graph."""
    # Inputs
    user_query: str
    conversation_history: List[SystemMessage | HumanMessage]
    word_limit: NotRequired[int]

    # Pipeline state
    information_intent: VeeInformationIntent
    unified_goal: UnifiedGoal
    plan: Dict[str, Any]
    
    # Final output
    final_answer: str
