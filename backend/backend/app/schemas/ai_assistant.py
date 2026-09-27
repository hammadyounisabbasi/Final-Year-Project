from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message author: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language question or prompt")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Recent conversation turns for context-aware multi-turn conversations")


class AIChatResponse(BaseModel):
    success: bool
    response: str
    provider: Optional[str] = None
    student_name: Optional[str] = None


class FeeAISource(BaseModel):
    title: str
    url: str = ""
    retrieved_at: Optional[str] = None
    score: Optional[float] = None


class FeeAIChatResponse(AIChatResponse):
    sources: List[FeeAISource] = Field(default_factory=list)


class AIGreetingResponse(BaseModel):
    success: bool
    greeting: str
    student_name: str
    first_name: str


# ------------------------------------------------------------------
# Teacher AI Academic Agent schemas
# ------------------------------------------------------------------

class TeacherAIGreetingResponse(BaseModel):
    success: bool
    greeting: str
    teacher_name: str
    first_name: str
    designation: Optional[str] = None


class TeacherAIChatResponse(BaseModel):
    success: bool
    response: str
    provider: Optional[str] = None
    teacher_name: Optional[str] = None
