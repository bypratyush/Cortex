from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Lesson
from app.models.curriculum import Concept, LearnerProfile, LearningPathItem
from app.models.enums import LearningStyle, LessonStatus


def generate_lesson_content(concept_name: str, concept_desc: str, style: LearningStyle, goal: str, target_level: str, background: str | None = None) -> dict:
    from app.services.llm import LLMService
    from app.agents.lesson_prompts import get_lesson_system_prompt, get_lesson_user_prompt

    system_prompt = get_lesson_system_prompt()
    user_prompt = get_lesson_user_prompt(
        concept_name=concept_name,
        concept_desc=concept_desc,
        style=style.value,
        goal=goal,
        target_level=target_level,
        background=background
    )

    try:
        return LLMService.generate_json(system_prompt, user_prompt)
    except Exception as e:
        print("Falling back to deterministic stub due to error:", e)
        # Fallback to stub
        return {
            "title": f"Mastering {concept_name}",
            "sections": [
                {
                    "type": "explanation",
                    "content": f"Welcome to the lesson on {concept_name}. {concept_desc}\n\n*Note: AI Generation failed, falling back to static content.*"
                },
                {
                    "type": "analogy",
                    "content": f"Think of {concept_name} like a tool in your toolbox."
                },
                {
                    "type": "examples",
                    "items": [{"type": "code", "content": f"# Example of {concept_name}\nprint('Hello {concept_name}')", "output": f"Hello {concept_name}"}]
                }
            ]
        }


class LessonService:
    @staticmethod
    def generate_lesson(
        db: Session,
        user_id: UUID,
        concept_id: UUID,
        learning_path_item_id: UUID | None = None
    ) -> Lesson:
        # 1. Fetch Profile
        profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
        if not profile:
            raise HTTPException(status_code=404, detail="Learner profile not found")

        # 2. Fetch Concept
        concept = db.scalar(select(Concept).where(Concept.id == concept_id))
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        # 3. Generate Content Payload (Using LLM)
        content_payload = generate_lesson_content(
            concept_name=concept.name,
            concept_desc=concept.description or "",
            style=profile.learning_style,
            goal=profile.goal.value,
            target_level=profile.target_level.value,
            background=profile.current_level_summary
        )

        personalization_context = {
            "learning_style": profile.learning_style.value,
            "goal": profile.goal.value,
            "target_level": profile.target_level.value
        }

        # 4. Create Lesson Record
        lesson = Lesson(
            user_id=user_id,
            concept_id=concept_id,
            learning_path_item_id=learning_path_item_id,
            title=concept.name,
            status=LessonStatus.DRAFT,
            content_payload=content_payload,
            personalization_context=personalization_context
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        
        return lesson

    @staticmethod
    def get_lesson(db: Session, lesson_id: UUID, user_id: UUID) -> Lesson:
        lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == user_id))
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson

    @staticmethod
    def complete_lesson(db: Session, lesson_id: UUID, user_id: UUID) -> Lesson:
        lesson = LessonService.get_lesson(db, lesson_id, user_id)
        if lesson.status != LessonStatus.COMPLETED:
            lesson.status = LessonStatus.COMPLETED
            lesson.completed_at = datetime.utcnow()
            
            # If part of a learning path, mark item as completed
            if lesson.learning_path_item_id:
                lpi = db.scalar(select(LearningPathItem).where(LearningPathItem.id == lesson.learning_path_item_id))
                if lpi:
                    from app.models.enums import LearningPathItemStatus
                    lpi.status = LearningPathItemStatus.COMPLETED
            
            db.commit()
            db.refresh(lesson)
        return lesson
