from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class PlanBlocks(BaseModel):
    opening: str = Field(..., description="Describe what to mirror/validate/celebrate (no phrasing).")
    core: str = Field(..., description="Describe the single question/choice or tiny step to propose (no phrasing).")
    micro_plan: List[str] = Field(default=[], description="Optional list of up to 3 micro-plan bullet points.")
    close: str = Field(..., description="Describe the one offer or affirmation (no phrasing).")
    safety_bridge: Optional[str] = Field(None, description="If needed, describe the brief handoff rationale or de-escalation.")

class Offer(BaseModel):
    type: str = Field(..., description="The type of offer being made.")
    content: str = Field(..., description="One-line description of the offer (no final phrasing).")

class Style(BaseModel):
    tone: str
    pacing: str
    emoji_style: str
    word_limit: int
    budget: Dict[str, int]

class Plan(BaseModel):
    goal_type: str
    blocks: PlanBlocks
    offer: Offer
    style: Style
    notes: str

class VeePlan(BaseModel):
    plan: Plan
