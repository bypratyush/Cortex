from __future__ import annotations

from datetime import datetime, UTC
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import MasteryRecord
from app.models.curriculum import Concept, ConceptPrerequisite, LearningPath, LearningPathItem
from app.models.enums import (
    LearningPathItemStatus,
    LearningPathItemType,
    LearningPathStatus,
    TargetLevel,
)
from app.schemas.curriculum import (
    CurriculumConceptSummary,
    CurriculumPlanResponse,
    LearningPathItemRead,
    LearningPathRead,
)
from app.services.onboarding import get_profile_or_404, get_user_or_404


DEFAULT_MASTERY_SCORE = 0.0


def generate_learning_path_for_user(db: Session, user_id: UUID) -> CurriculumPlanResponse:
    get_user_or_404(db, user_id)
    profile = get_profile_or_404(db, user_id)

    concepts = db.scalars(
        select(Concept)
        .where(
            Concept.domain_key == profile.domain_key,
            Concept.is_active.is_(True),
        )
        .options(
            selectinload(Concept.prerequisites).selectinload(
                ConceptPrerequisite.prerequisite_concept
            )
        )
        .order_by(Concept.concept_order.asc())
    ).all()

    if not concepts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No concepts are configured for this learner domain.",
        )

    mastery_records = db.scalars(
        select(MasteryRecord)
        .where(MasteryRecord.user_id == user_id)
        .options(selectinload(MasteryRecord.concept))
    ).all()
    mastery_by_concept_id = {
        record.concept_id: record.mastery_score
        for record in mastery_records
    }

    # Construct inputs for Prompt 4
    concept_by_name = {c.name: c for c in concepts}
    
    kg_dict = {}
    for c in concepts:
        kg_dict[c.name] = {
            "prerequisites": [],
            "unlocks": []
        }
    for c in concepts:
        for edge in c.prerequisites:
            prereq_name = edge.prerequisite_concept.name
            if prereq_name in kg_dict:
                kg_dict[c.name]["prerequisites"].append(prereq_name)
                kg_dict[prereq_name]["unlocks"].append(c.name)
                
    mastery_dict = {}
    for c in concepts:
        score = mastery_by_concept_id.get(c.id, 0.0)
        mastery_dict[c.name] = score

    # Call LLM curriculum engine (Prompt 4)
    from app.services.llm import generate_curriculum_roadmap
    import json
    roadmap_data = generate_curriculum_roadmap(
        goal=profile.goal.value if profile.goal else "Learn Python",
        mastery_scores_json=json.dumps(mastery_dict),
        knowledge_graph_json=json.dumps(kg_dict)
    )

    skipped_concepts: list[CurriculumConceptSummary] = []
    actionable_concepts: list[CurriculumConceptSummary] = []
    path_blueprint: list[tuple[Concept, LearningPathItemType, str]] = []

    # Map phases into the learning path
    for phase in roadmap_data.get("phases", []):
        phase_title = phase.get("title", "Logical Phase")
        for c_entry in phase.get("concepts", []):
            c_name = c_entry.get("name", "")
            status = c_entry.get("status", "upcoming")
            mastery_score = c_entry.get("mastery", 0) / 100.0
            
            # Find DB concept
            db_concept = None
            for name, c_obj in concept_by_name.items():
                if name.lower().strip() == c_name.lower().strip():
                    db_concept = c_obj
                    break
                    
            if not db_concept:
                continue
                
            reason = f"LLM assigned status '{status}' in phase '{phase_title}'. Estimated sessions: {c_entry.get('estimated_sessions', 1)}."
            
            summary = CurriculumConceptSummary(
                concept_id=db_concept.id,
                concept_slug=db_concept.slug,
                concept_name=db_concept.name,
                mastery_score=mastery_score,
                reason=reason
            )
            
            if status == "completed":
                skipped_concepts.append(summary)
            else:
                actionable_concepts.append(summary)
                # Determine type
                item_type = LearningPathItemType.LEARN
                if status == "in_progress" and mastery_score > 0.4:
                    item_type = LearningPathItemType.REVIEW
                path_blueprint.append((db_concept, item_type, reason))

    if not path_blueprint and concepts:
        db_concept = concepts[-1]
        fallback_reason = "All core concepts are currently mastered. Added a review checkpoint to keep momentum."
        summary = CurriculumConceptSummary(
            concept_id=db_concept.id,
            concept_slug=db_concept.slug,
            concept_name=db_concept.name,
            mastery_score=round(mastery_by_concept_id.get(db_concept.id, DEFAULT_MASTERY_SCORE), 4),
            reason=fallback_reason
        )
        actionable_concepts.append(summary)
        path_blueprint.append((db_concept, LearningPathItemType.REVIEW, fallback_reason))

    # Persist and serialize
    thresholds = _resolve_mastery_thresholds(profile.target_level)
    learning_path = _persist_learning_path(
        db=db,
        user_id=user_id,
        learner_profile_id=profile.id,
        domain_key=profile.domain_key,
        path_blueprint=path_blueprint,
        rationale=roadmap_data.get("reasoning", "Generated roadmap using LLM curriculum planner."),
        roadmap=roadmap_data
    )

    return CurriculumPlanResponse(
        user_id=user_id,
        domain_key=profile.domain_key,
        generated_at=datetime.now(UTC),
        mastery_thresholds=thresholds,
        skipped_concepts=skipped_concepts,
        actionable_concepts=actionable_concepts,
        learning_path=_serialize_learning_path(learning_path),
    )


def get_active_learning_path_for_user(db: Session, user_id: UUID) -> LearningPathRead:
    get_user_or_404(db, user_id)

    path = db.scalar(
        select(LearningPath)
        .where(
            LearningPath.user_id == user_id,
            LearningPath.is_active.is_(True),
        )
        .options(selectinload(LearningPath.items).selectinload(LearningPathItem.concept))
        .order_by(LearningPath.version.desc())
    )
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active learning path exists for this learner yet.",
        )
    return _serialize_learning_path(path)


def adapt_learning_path_for_user(db: Session, user_id: UUID) -> CurriculumPlanResponse:
    """
    Module 9: Adaptive Replanning.
    Re-evaluates the Learner Profile and Mastery Records, archives the current path, 
    and generates a new version. This inserts Review nodes for concepts whose mastery dropped.
    """
    return generate_learning_path_for_user(db, user_id)


def _persist_learning_path(
    db: Session,
    user_id: UUID,
    learner_profile_id: UUID,
    domain_key: str,
    path_blueprint: list[tuple[Concept, LearningPathItemType, str]],
    rationale: str,
    roadmap: dict | None = None
) -> LearningPath:
    current_active_paths = db.scalars(
        select(LearningPath).where(
            LearningPath.user_id == user_id,
            LearningPath.is_active.is_(True),
        )
    ).all()
    for path in current_active_paths:
        path.is_active = False
        path.status = LearningPathStatus.ARCHIVED

    latest_version = db.scalar(
        select(func.max(LearningPath.version)).where(LearningPath.user_id == user_id)
    ) or 0

    learning_path = LearningPath(
        user_id=user_id,
        learner_profile_id=learner_profile_id,
        domain_key=domain_key,
        status=LearningPathStatus.ACTIVE,
        version=latest_version + 1,
        is_active=True,
        rationale=rationale,
        roadmap=roadmap,
        started_at=datetime.now(UTC),
    )
    db.add(learning_path)
    db.flush()

    for position, (concept, item_type, reason) in enumerate(path_blueprint, start=1):
        item = LearningPathItem(
            learning_path_id=learning_path.id,
            concept_id=concept.id,
            position=position,
            item_type=item_type,
            status=LearningPathItemStatus.PENDING,
            unlock_condition=reason,
        )
        db.add(item)

    db.commit()
    db.refresh(learning_path)

    hydrated_path = db.scalar(
        select(LearningPath)
        .where(LearningPath.id == learning_path.id)
        .options(selectinload(LearningPath.items).selectinload(LearningPathItem.concept))
    )
    if hydrated_path is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Learning path was created but could not be reloaded.",
        )
    return hydrated_path


def _resolve_mastery_thresholds(target_level: TargetLevel) -> dict[str, float]:
    if target_level == TargetLevel.BEGINNER:
        return {"review": 0.45, "skip": 0.85}
    if target_level == TargetLevel.INTERMEDIATE:
        return {"review": 0.55, "skip": 0.9}
    if target_level == TargetLevel.ADVANCED:
        return {"review": 0.65, "skip": 0.93}
    return {"review": 0.7, "skip": 0.95}


def _build_path_rationale(actionable_count: int, skipped_count: int, thresholds: dict[str, float]) -> str:
    return (
        f"Generated deterministically from mastery thresholds "
        f"(review<{thresholds['review']:.2f}, skip>={thresholds['skip']:.2f}). "
        f"Actionable concepts: {actionable_count}. Skipped concepts: {skipped_count}."
    )


def _serialize_learning_path(path: LearningPath) -> LearningPathRead:
    sorted_items = sorted(path.items, key=lambda item: item.position)
    return LearningPathRead(
        id=path.id,
        user_id=path.user_id,
        learner_profile_id=path.learner_profile_id,
        domain_key=path.domain_key,
        status=path.status,
        version=path.version,
        is_active=path.is_active,
        rationale=path.rationale,
        roadmap=path.roadmap,
        started_at=path.started_at,
        completed_at=path.completed_at,
        created_at=path.created_at,
        updated_at=path.updated_at,
        items=[
            LearningPathItemRead(
                id=item.id,
                concept_id=item.concept_id,
                concept_slug=item.concept.slug,
                concept_name=item.concept.name,
                position=item.position,
                item_type=item.item_type,
                status=item.status,
                unlock_condition=item.unlock_condition,
            )
            for item in sorted_items
        ],
    )
