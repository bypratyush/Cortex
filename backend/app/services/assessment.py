from __future__ import annotations

from collections import defaultdict
from datetime import datetime, UTC
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import AssessmentQuestion, AssessmentResult, MasteryRecord
from app.models.curriculum import Concept, LearnerProfile
from app.schemas.assessment import (
    AssessmentQuestionRead,
    AssessmentResultRead,
    AssessmentSubmissionRequest,
    AssessmentSubmissionResponse,
    AssessmentSessionRead,
    MasteryRecordRead,
)
from app.services.onboarding import get_profile_or_404, get_user_or_404


DEFAULT_ASSESSMENT_QUESTION_LIMIT = 12


def get_assessment_questions_for_user(
    db: Session,
    user_id: UUID,
    limit: int = DEFAULT_ASSESSMENT_QUESTION_LIMIT,
) -> AssessmentSessionRead:
    get_user_or_404(db, user_id)
    profile = get_profile_or_404(db, user_id)

    questions = db.scalars(
        select(AssessmentQuestion)
        .join(AssessmentQuestion.concept)
        .where(
            Concept.domain_key == profile.domain_key,
            AssessmentQuestion.is_active.is_(True),
            Concept.is_active.is_(True),
        )
        .options(selectinload(AssessmentQuestion.concept))
        .order_by(Concept.concept_order.asc(), AssessmentQuestion.difficulty.asc())
        .limit(limit)
    ).all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment questions are configured for this learner domain.",
        )

    return AssessmentSessionRead(
        user_id=user_id,
        domain_key=profile.domain_key,
        question_count=len(questions),
        questions=[
            AssessmentQuestionRead(
                id=question.id,
                concept_id=question.concept_id,
                concept_slug=question.concept.slug,
                concept_name=question.concept.name,
                difficulty=question.difficulty,
                question_type=question.question_type,
                prompt=question.prompt,
                choices=question.choices,
                starter_code=question.starter_code,
            )
            for question in questions
        ],
    )


def submit_assessment_for_user(
    db: Session,
    user_id: UUID,
    payload: AssessmentSubmissionRequest,
) -> AssessmentSubmissionResponse:
    get_user_or_404(db, user_id)
    profile = get_profile_or_404(db, user_id)

    submitted_question_ids = [answer.question_id for answer in payload.answers]
    if not submitted_question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one answer is required.",
        )

    if len(set(submitted_question_ids)) != len(submitted_question_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate question IDs were submitted.",
        )

    questions = db.scalars(
        select(AssessmentQuestion)
        .join(AssessmentQuestion.concept)
        .where(
            AssessmentQuestion.id.in_(submitted_question_ids),
            Concept.domain_key == profile.domain_key,
        )
        .options(selectinload(AssessmentQuestion.concept))
    ).all()

    questions_by_id = {question.id: question for question in questions}
    missing_ids = [question_id for question_id in submitted_question_ids if question_id not in questions_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more submitted questions do not belong to this learner domain.",
        )

    assessed_at = datetime.now(UTC)
    concept_scores: dict[UUID, list[float]] = defaultdict(list)
    concept_evidence: dict[UUID, list[str]] = defaultdict(list)
    result_payloads: list[AssessmentResultRead] = []
    correct_answers = 0

    for submitted_answer in payload.answers:
        question = questions_by_id[submitted_answer.question_id]
        is_correct = _is_answer_correct(question.expected_answer, submitted_answer.answer)
        score = 1.0 if is_correct else 0.0
        if is_correct:
            correct_answers += 1

        result = AssessmentResult(
            user_id=user_id,
            concept_id=question.concept_id,
            question_id=question.id,
            difficulty=question.difficulty,
            question_type=question.question_type,
            learner_response={"answer": submitted_answer.answer},
            is_correct=is_correct,
            score=score,
            assessed_at=assessed_at,
        )
        db.add(result)

        concept_scores[question.concept_id].append(score)
        concept_evidence[question.concept_id].append(
            f"{question.concept.name}: {'correct' if is_correct else 'incorrect'}"
        )

        result_payloads.append(
            AssessmentResultRead(
                question_id=question.id,
                concept_id=question.concept_id,
                concept_slug=question.concept.slug,
                concept_name=question.concept.name,
                difficulty=question.difficulty,
                question_type=question.question_type,
                answer=submitted_answer.answer,
                expected_answer=question.expected_answer,
                is_correct=is_correct,
                score=score,
                explanation=question.explanation,
                assessed_at=assessed_at,
            )
        )

    mastery_payloads: list[MasteryRecordRead] = []
    for concept_id, scores in concept_scores.items():
        question = next(
            question for question in questions if question.concept_id == concept_id
        )
        average_score = round(sum(scores) / len(scores), 4)
        confidence = round(min(1.0, len(scores) / 3), 4)

        mastery_record = db.scalar(
            select(MasteryRecord).where(
                MasteryRecord.user_id == user_id,
                MasteryRecord.concept_id == concept_id,
            )
        )
        if mastery_record is None:
            mastery_record = MasteryRecord(user_id=user_id, concept_id=concept_id)
            db.add(mastery_record)

        mastery_record.mastery_score = average_score
        mastery_record.quiz_accuracy = average_score
        mastery_record.practice_accuracy = 0.0
        mastery_record.consistency_score = confidence
        mastery_record.confidence = confidence
        mastery_record.evidence_summary = "; ".join(concept_evidence[concept_id])[:500]
        mastery_record.last_evaluated_at = assessed_at

        mastery_payloads.append(
            MasteryRecordRead(
                concept_id=concept_id,
                concept_slug=question.concept.slug,
                concept_name=question.concept.name,
                mastery_score=average_score,
                quiz_accuracy=average_score,
                practice_accuracy=0.0,
                consistency_score=confidence,
                confidence=confidence,
                evidence_summary=mastery_record.evidence_summary,
                last_evaluated_at=assessed_at,
            )
        )

    # Generate the assessment results summary for the LLM
    results_list = []
    for concept_id, evidence in concept_evidence.items():
        for item in evidence:
            results_list.append(f"- {item}")
    assessment_results_str = "\n".join(results_list)

    # Call LLM profile analysis service (Prompt 1)
    from app.services.llm import analyze_learner_profile
    structured_data = analyze_learner_profile(
        goal=profile.goal.value if profile.goal else "",
        motivation=profile.motivation.value if profile.motivation else "",
        learning_style=profile.learning_style.value if profile.learning_style else "",
        target_proficiency=profile.target_level.value if profile.target_level else "",
        assessment_results=assessment_results_str
    )

    profile.structured_understanding = structured_data
    db.add(profile)
    db.commit()

    total_questions = len(payload.answers)
    overall_score = round(correct_answers / total_questions, 4)

    mastery_payloads.sort(key=lambda record: record.concept_name.lower())
    result_payloads.sort(key=lambda result: result.concept_name.lower())

    return AssessmentSubmissionResponse(
        user_id=user_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        overall_score=overall_score,
        results=result_payloads,
        mastery=mastery_payloads,
    )


def get_mastery_snapshot_for_user(db: Session, user_id: UUID) -> list[MasteryRecordRead]:
    get_user_or_404(db, user_id)
    get_profile_or_404(db, user_id)

    mastery_records = db.scalars(
        select(MasteryRecord)
        .join(MasteryRecord.concept)
        .where(MasteryRecord.user_id == user_id)
        .options(selectinload(MasteryRecord.concept))
        .order_by(Concept.concept_order.asc())
    ).all()

    return [
        MasteryRecordRead(
            concept_id=record.concept_id,
            concept_slug=record.concept.slug,
            concept_name=record.concept.name,
            mastery_score=record.mastery_score,
            quiz_accuracy=record.quiz_accuracy,
            practice_accuracy=record.practice_accuracy,
            consistency_score=record.consistency_score,
            confidence=record.confidence,
            evidence_summary=record.evidence_summary,
            last_evaluated_at=record.last_evaluated_at,
        )
        for record in mastery_records
    ]


def _is_answer_correct(expected_answer: str | None, submitted_answer: str) -> bool:
    if expected_answer is None:
        return False
    return _normalize_answer(expected_answer) == _normalize_answer(submitted_answer)


def _normalize_answer(value: str) -> str:
    return " ".join(value.strip().casefold().split())
