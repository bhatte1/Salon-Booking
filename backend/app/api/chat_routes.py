from uuid import uuid4
from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.customer_chat import require_customer
from app.services.booking_chat import answer_booking_chat, load_conversation

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('', response_model=ChatResponse)
def customer_chat(payload: ChatRequest, response: Response,
                  current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_customer(current_user)
    request_id = str(uuid4())
    response.headers['X-Request-ID'] = request_id
    if not rate_limiter.allow(f'chat:{current_user.id}', limit=20, window_seconds=60):
        raise HTTPException(429, 'Too many chat requests. Please try again shortly.')
    return answer_booking_chat(payload, db, current_user, request_id)


@router.get('/{conversation_id}')
def read_conversation(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_customer(current_user)
    conversation = load_conversation(db, current_user, conversation_id)
    return {'conversation_id': conversation.id, 'history': conversation.history, 'confirmation': conversation.draft.get('confirmation'), 'timezone': settings.salon_timezone}
