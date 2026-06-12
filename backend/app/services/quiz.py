from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentQuestion, MasteryRecord
from app.models.content import Quiz, QuizAttempt
from app.models.curriculum import Concept
from app.schemas.assessment import AssessmentQuestionRead
from app.schemas.quiz import QuizAttemptSubmission, QuizCreate


class QuizService:
    @staticmethod
    def generate_quiz(db: Session, user_id: UUID, req: QuizCreate) -> tuple[Quiz, list[AssessmentQuestionRead]]:
        concept = db.scalar(select(Concept).where(Concept.id == req.concept_id))
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        from app.models.curriculum import LearnerProfile
        from app.models.enums import DifficultyLevel, QuestionType
        from app.services.llm import generate_personalized_quiz
        import uuid
        import json

        # Fetch profile
        profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
        if not profile:
            raise HTTPException(status_code=404, detail="Learner profile not found")

        # Fetch mastery score
        mastery_record = db.scalar(
            select(MasteryRecord).where(
                MasteryRecord.user_id == user_id,
                MasteryRecord.concept_id == req.concept_id
            )
        )
        mastery_level = round(mastery_record.mastery_score * 100) if mastery_record else 0

        # Generate personalized quiz questions using LLM (Prompt 3)
        profile_json = json.dumps(profile.structured_understanding or {})
        raw_questions = generate_personalized_quiz(
            concept_name=concept.name,
            concept_description=concept.description or "",
            learner_profile_json=profile_json,
            mastery_level=mastery_level
        )

        questions_with_uuid = []
        q_reads = []
        for rq in raw_questions:
            q_uuid = str(uuid.uuid4())
            rq_copy = dict(rq)
            rq_copy["uuid"] = q_uuid
            questions_with_uuid.append(rq_copy)

            type_str = rq.get("type", "mcq")
            if type_str == "mcq":
                q_type = QuestionType.MCQ
            elif type_str == "conceptual":
                q_type = QuestionType.SHORT_ANSWER
            else:
                q_type = QuestionType.CODING_EXERCISE

            choices = None
            if q_type == QuestionType.MCQ:
                options = rq.get("options", {})
                choices = [options.get("A", ""), options.get("B", ""), options.get("C", ""), options.get("D", "")]

            q_reads.append(
                AssessmentQuestionRead(
                    id=uuid.UUID(q_uuid),
                    concept_id=concept.id,
                    concept_slug=concept.slug,
                    concept_name=concept.name,
                    difficulty=DifficultyLevel.MEDIUM,
                    question_type=q_type,
                    prompt=rq.get("question", ""),
                    choices=choices,
                    starter_code=rq.get("sample_answer", "") if q_type == QuestionType.CODING_EXERCISE else None
                )
            )

        quiz = Quiz(
            user_id=user_id,
            concept_id=req.concept_id,
            learning_path_item_id=req.learning_path_item_id,
            title=f"Quiz: {concept.name}",
            quiz_type=req.quiz_type,
            question_count=len(questions_with_uuid),
            configuration={
                "dynamic_questions": questions_with_uuid,
                "is_dynamic": True
            }
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return quiz, q_reads

    @staticmethod
    def submit_quiz(db: Session, user_id: UUID, quiz_id: UUID, submission: QuizAttemptSubmission) -> QuizAttempt:
        quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user_id))
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        is_dynamic = quiz.configuration.get("is_dynamic", False)
        if is_dynamic:
            dynamic_questions = quiz.configuration.get("dynamic_questions", [])
            q_map = {q["uuid"]: q for q in dynamic_questions}
            total = len(dynamic_questions)
        else:
            question_ids = quiz.configuration.get("generated_question_ids", [])
            questions = db.scalars(
                select(AssessmentQuestion).where(AssessmentQuestion.id.in_(question_ids))
            ).all()
            q_map = {str(q.id): q for q in questions}
            total = len(question_ids)

        correct_count = 0
        feedback = []
        submitted_dict = {}

        for ans in submission.answers:
            qid = str(ans.question_id)
            submitted_dict[qid] = ans.answer
            
            if qid in q_map:
                if is_dynamic:
                    q = q_map[qid]
                    q_type = q.get("type", "mcq")
                    if q_type == "mcq":
                        expected = q.get("correct", "A")
                        opt_text = q.get("options", {}).get(expected, "")
                        is_correct = (
                            str(ans.answer).strip().upper() == expected.upper() or
                            str(ans.answer).strip().lower() == opt_text.strip().lower()
                        )
                        explanation = q.get("explanation", "")
                    else:
                        expected = q.get("sample_answer", "")
                        is_correct = len(str(ans.answer).strip()) > 0
                        explanation = q.get("evaluation_hint", "")
                else:
                    expected = q_map[qid].expected_answer
                    is_correct = (str(expected).strip().lower() == str(ans.answer).strip().lower())
                    explanation = q_map[qid].explanation

                if is_correct:
                    correct_count += 1
                
                feedback.append({
                    "question_id": qid,
                    "is_correct": is_correct,
                    "expected": expected,
                    "explanation": explanation
                })

        accuracy = correct_count / total if total > 0 else 0.0

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            score=correct_count,
            accuracy=accuracy,
            submitted_answers=submitted_dict,
            feedback_payload={"results": feedback},
            completed_at=datetime.utcnow()
        )
        db.add(attempt)
        
        # Update Mastery deterministically
        mastery_record = db.scalar(
            select(MasteryRecord).where(
                MasteryRecord.user_id == user_id, 
                MasteryRecord.concept_id == quiz.concept_id
            )
        )
        if not mastery_record:
            mastery_record = MasteryRecord(
                user_id=user_id,
                concept_id=quiz.concept_id,
                mastery_score=0.0
            )
            db.add(mastery_record)
            
        # The mathematical mastery formula
        old_score = mastery_record.mastery_score
        new_score = (old_score * 0.5) + (accuracy * 0.5)
        mastery_record.mastery_score = round(new_score, 4)
        mastery_record.quiz_accuracy = accuracy
        mastery_record.last_evaluated_at = datetime.utcnow()

        db.commit()
        db.refresh(attempt)
        
        # Module 9: Adaptive Replanning Trigger
        # If the student struggled on this quiz, immediately recalculate their learning path
        # so review nodes are injected before they can proceed.
        if accuracy < 0.6:
            from app.services.curriculum import adapt_learning_path_for_user
            adapt_learning_path_for_user(db, user_id)
        
        return attempt
