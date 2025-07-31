from pydantic import BaseModel
from typing import Optional

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
