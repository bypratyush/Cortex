from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Lesson
from app.models.curriculum import Concept, LearnerProfile, LearningPathItem
from app.models.enums import LearningStyle, LessonStatus


def generate_lesson_content(concept_name: str, concept_desc: str, style: LearningStyle) -> dict:
    """
    Deterministic stub for lesson generation.
    In the future, this is where we call the LLM to generate the explanation/analogy.
    """
    base_explanation = f"Welcome to the lesson on {concept_name}. {concept_desc}"
    
    analogy = f"Think of {concept_name} like a tool in your toolbox."
    if style == LearningStyle.VISUAL:
        analogy = f"Imagine a blueprint. {concept_name} is the foundational structure."
    elif style == LearningStyle.PRACTICE_BASED:
        analogy = f"Like learning to ride a bike, {concept_name} requires hands-on repetition."
        
    examples = []
    if style == LearningStyle.EXAMPLES_FIRST:
        examples.append({"type": "code", "content": f"# Example of {concept_name}\nprint('Hello {concept_name}')"})
    
    return {
        "title": f"Mastering {concept_name}",
        "sections": [
            {
                "type": "explanation",
                "content": base_explanation,
            },
            {
                "type": "analogy",
                "content": analogy,
            },
            {
                "type": "examples",
                "items": examples,
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

        # 3. Fetch Mastery Level
        from app.models.assessment import MasteryRecord
        import json
        
        mastery_record = db.scalar(
            select(MasteryRecord).where(
                MasteryRecord.user_id == user_id,
                MasteryRecord.concept_id == concept_id
            )
        )
        mastery_level = round(mastery_record.mastery_score * 100) if mastery_record else 0

        # Serialize structured understanding profile
        profile_json = json.dumps(profile.structured_understanding or {})

        # Call LLM personalization engine (Prompt 2)
        from app.services.llm import generate_personalized_lesson
        content_payload = generate_personalized_lesson(
            concept_name=concept.name,
            concept_description=concept.description or "",
            learner_profile_json=profile_json,
            mastery_level=mastery_level
        )
        content_payload["title"] = f"Mastering {concept.name}"

        personalization_context = {
            "learning_style": profile.learning_style.value,
            "goal": profile.goal.value,
            "target_level": profile.target_level.value,
            "mastery_level": mastery_level
        }

        # 4. Create Lesson Record
        lesson = Lesson(
            user_id=user_id,
            concept_id=concept_id,
            learning_path_item_id=learning_path_item_id,
            title=content_payload["title"],
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
