from pydantic import BaseModel
from typing import Optional, Literal

class ConversationStrategy(BaseModel):
    """Model for conversation strategy selection results.
    
    Attributes:
        strategy: The selected conversation strategy
        rationale: Explanation for why this strategy was chosen
    """
    strategy: Literal[
        'comfort', 'validate', 'distract_gently', 'reflect',
        'encourage', 'affirm', 'ask_deeper', 'hold_space',
        'celebrate', 'follow_their_lead', 'unknown'
    ]
    rationale: str

class ContentSeed(BaseModel):
    """Model for content seed generation results.
    
    Attributes:
        seed: The core message intention to express
        tag: Optional tag for follow-up modules
    """
    seed: str
    tag: Optional[Literal[
        'use_distraction_card', 'offer_pause', 'ask_safe_question',
        'shift_topic_gently', 'continue_softly'
    ]] = None
