from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime


class User(BaseModel):
    id: int
    telegram_chat_id: int
    name: str
    context: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        orm_mode = True


class Session(BaseModel):
    id: int
    user_id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    summary: Optional[str] = None

    class Config:
        orm_mode = True


class SensingData(BaseModel):
    id: int = 0
    message_id: int
    dialogue_act: Optional[str] = None
    primary_intent: Optional[str] = None
    sub_intent: Optional[str] = None
    sentiment: Optional[str] = None
    valence: Optional[float] = None
    arousal: Optional[float] = None
    risk_level: str
    distress_hint: Optional[bool] = None
    inference: Optional[str] = None
    needs_clarification: Optional[bool] = None
    sarcasm_possible: Optional[bool] = None
    raw_output: Optional[str] = None

    class Config:
        orm_mode = True


class Message(BaseModel):
    id: int = 0
    session_id: int
    role: str
    content: str
    timestamp: datetime.datetime
    mode: Optional[str] = None

    class Config:
        orm_mode = True
