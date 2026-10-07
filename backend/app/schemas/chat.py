from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(default='', max_length=1000)
    conversation_id: UUID | None = None
    request_id: UUID
    action: Literal['message', 'confirm', 'cancel'] = 'message'
    confirmation_id: UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    request_id: str
    conversation_id: str
    history: list[dict]
    confirmation: dict | None = None
    appointment_id: int | None = None
    booking_path: str = '/dashboard/customer#my-appointments'
    timezone: str
