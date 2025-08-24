from pydantic import BaseModel, Field
from typing import Optional, List

class EmotionAnalysisResult(BaseModel):
    """Model for emotion analysis results.
    
    Attributes:
        emotion: The primary emotion detected
        tone: How the emotion is expressed
        notes: Optional additional context or observations
    """
    emotion: str
    tone: str
    notes: Optional[str]


class EmotionScore(BaseModel):
    label: str
    score: float = Field(ge=0.0, le=1.0)


class Intent(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)


class PerceptionResult(BaseModel):
    """Structured perception output for emotions, intent, uncertainty, and needs."""
    emotions: List[EmotionScore]
    intent: Intent
    uncertainty: float = Field(ge=0.0, le=1.0)
    needs: List[str] = []
    tone: Optional[str] = None
    notes: Optional[str] = None
