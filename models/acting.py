from pydantic import BaseModel

class ModulatedResponse(BaseModel):
    """Model for response modulation results.
    
    Attributes:
        message: The final, modulated message to send to the user
    """
    message: str
