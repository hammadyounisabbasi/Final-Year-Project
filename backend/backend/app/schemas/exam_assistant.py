from typing import Literal

from pydantic import BaseModel, Field


class ExamAssistantSessionCreate(BaseModel):
    """Optional client hint used only to restore an unexpired server session."""

    session_id: str | None = Field(None, min_length=16, max_length=80)


class ExamAssistantChatRequest(BaseModel):
    session_id: str = Field(..., min_length=16, max_length=80)
    message: str = Field(..., min_length=1, max_length=4000)


class ExamAssistantExportRequest(BaseModel):
    session_id: str = Field(..., min_length=16, max_length=80)
    document_type: Literal["date_sheet", "seating_plan"]
    format: Literal["pdf", "docx"]
