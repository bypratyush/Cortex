from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TutorConversationStatus, TutorMessageRole
from app.models.tutoring import TutorConversation, TutorMessage
from app.schemas.tutor import TutorConversationCreate, TutorMessageCreate


def generate_socratic_response_stub(user_message: str, hint_level: int, concept_name: str) -> str:
    """
    Deterministic stub representing the LLM generation.
    In the real implementation, this constructs a strict prompt telling the LLM
    how much to reveal based on the `hint_level`.
    """
    if hint_level == 0:
        return f"I see you're working on {concept_name}. Before I give you the answer, what do you think is the first step?"
    elif hint_level == 1:
        return f"You're on the right track with {concept_name}. Consider how loops might help here. What kind of loop would you use?"
    elif hint_level == 2:
        return f"Let's narrow it down. A `for` loop would be perfect here. Can you write a simple `for` loop?"
    else:
        return f"Okay, here is the answer for {concept_name}: You should use a `for` loop like this: `for item in items:`."


class TutorService:
    @staticmethod
    def start_conversation(db: Session, user_id: UUID, req: TutorConversationCreate) -> TutorConversation:
        conversation = TutorConversation(
            user_id=user_id,
            concept_id=req.concept_id,
            learning_path_item_id=req.learning_path_item_id,
            status=TutorConversationStatus.ACTIVE,
            last_message_at=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        if req.initial_message:
            TutorService.send_message(
                db, 
                user_id, 
                conversation.id, 
                TutorMessageCreate(content=req.initial_message, referenced_concept_id=req.concept_id)
            )
            # Refresh to load messages
            conversation = db.scalar(
                select(TutorConversation)
                .where(TutorConversation.id == conversation.id)
                .options(selectinload(TutorConversation.messages))
            )

        return conversation

    @staticmethod
    def send_message(db: Session, user_id: UUID, conversation_id: UUID, req: TutorMessageCreate) -> list[TutorMessage]:
        conversation = db.scalar(
            select(TutorConversation)
            .where(TutorConversation.id == conversation_id, TutorConversation.user_id == user_id)
            .options(selectinload(TutorConversation.messages))
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 1. Add User Message
        user_msg = TutorMessage(
            conversation_id=conversation.id,
            referenced_concept_id=req.referenced_concept_id or conversation.concept_id,
            role=TutorMessageRole.LEARNER,
            content=req.content,
            hint_level=0
        )
        db.add(user_msg)

        # 2. Determine Attempt Count and Hint Level
        learner_message_count = sum(1 for m in conversation.messages if m.role == TutorMessageRole.LEARNER)
        attempt_count = learner_message_count + 1
        hint_level = attempt_count

        # 3. Get Concept Name for Context
        concept_name = "this topic"
        if conversation.concept:
            concept_name = conversation.concept.name

        # 4. Fetch Learner Profile structured understanding
        from app.models.curriculum import LearnerProfile
        import json
        profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
        profile_json = json.dumps(profile.structured_understanding or {}) if profile else "{}"

        # 5. Format Conversation History (including current message)
        conversation_history = [
            {"role": "learner" if m.role == TutorMessageRole.LEARNER else "tutor", "content": m.content}
            for m in conversation.messages
        ]
        conversation_history.append({"role": "learner", "content": req.content})

        # 6. Generate Socratic Tutor Response
        from app.services.llm import generate_socratic_response
        assistant_content = generate_socratic_response(
            learner_profile_json=profile_json,
            concept=concept_name,
            conversation_history=conversation_history,
            attempt_count=attempt_count
        )

        # 7. Add Tutor Message
        assistant_msg = TutorMessage(
            conversation_id=conversation.id,
            referenced_concept_id=req.referenced_concept_id or conversation.concept_id,
            role=TutorMessageRole.TUTOR,
            content=assistant_content,
            hint_level=hint_level
        )
        db.add(assistant_msg)

        conversation.last_message_at = datetime.utcnow()
        db.commit()
        
        db.refresh(user_msg)
        db.refresh(assistant_msg)

        return [user_msg, assistant_msg]

    @staticmethod
    def get_conversation(db: Session, user_id: UUID, conversation_id: UUID) -> TutorConversation:
        conversation = db.scalar(
            select(TutorConversation)
            .where(TutorConversation.id == conversation_id, TutorConversation.user_id == user_id)
            .options(selectinload(TutorConversation.messages))
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
