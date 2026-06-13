from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TutorConversationStatus, TutorMessageRole
from app.models.tutoring import TutorConversation, TutorMessage
from app.schemas.tutor import TutorConversationCreate, TutorMessageCreate


def generate_socratic_response(messages_context: list[dict], hint_level: int, concept_name: str) -> str:
    from app.services.llm import LLMService
    from app.agents.tutor_prompts import get_tutor_system_prompt
    
    system_prompt = get_tutor_system_prompt(concept_name=concept_name, hint_level=hint_level)

    try:
        return LLMService.generate_text(system_prompt=system_prompt, messages=messages_context)
    except Exception as e:
        print("Falling back to tutor stub due to error:", e)
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

        # 2. Determine Hint Level
        # Count previous user messages in this conversation to determine how frustrated they might be
        user_message_count = sum(1 for m in conversation.messages if m.role == TutorMessageRole.LEARNER)
        # Assuming every 2 messages they need a higher hint
        hint_level = min(user_message_count // 2, 3) 

        # 3. Get Concept Name for Context
        concept_name = "this topic"
        if conversation.concept:
            concept_name = conversation.concept.name

        # Format history for Bedrock Converse API: [{"role": "user"|"assistant", "content": [{"text": "..."}]}]
        messages_context = []
        for m in conversation.messages:
            bedrock_role = "user" if m.role == TutorMessageRole.LEARNER else "assistant"
            messages_context.append({"role": bedrock_role, "content": [{"text": m.content}]})
            
        messages_context.append({"role": "user", "content": [{"text": req.content}]})

        # 4. Generate LLM Response (Using AWS Bedrock)
        assistant_content = generate_socratic_response(messages_context, hint_level, concept_name)

        # 5. Add Assistant Message
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
