from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.tutor import TutorConversationCreate, TutorConversationRead, TutorMessageCreate, TutorMessageRead
from app.services.tutor import TutorService

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.post("/conversations", response_model=TutorConversationRead)
def start_conversation(
    req: TutorConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new Socratic tutoring conversation.
    Optionally send an initial message.
    """
    return TutorService.start_conversation(db, current_user.id, req)


@router.get("/conversations/{conversation_id}", response_model=TutorConversationRead)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve an entire tutoring conversation history.
    """
    return TutorService.get_conversation(db, current_user.id, conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[TutorMessageRead])
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all messages for a specific conversation.
    """
    conv = TutorService.get_conversation(db, current_user.id, conversation_id)
    return conv.messages


@router.post("/conversations/{conversation_id}/messages", response_model=list[TutorMessageRead])
def send_message(
    conversation_id: UUID,
    req: TutorMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the Socratic tutor. 
    Returns the user's message and the tutor's response (with adapted hint levels).
    """
    return TutorService.send_message(db, current_user.id, conversation_id, req)
