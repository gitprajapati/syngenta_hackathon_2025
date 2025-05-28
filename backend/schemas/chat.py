# schemas/chat.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessageSchema(BaseModel): 
    role: str
    content: str

    class Config:
        orm_mode = True 
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    conversation_id: int
    history: List[ChatMessageSchema] 

