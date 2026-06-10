from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.enums import LearningPathItemStatus, LearningPathItemType, LearningPathStatus
from app.schemas.common import CortexSchema


class CurriculumConceptSummary(CortexSchema):
    concept_id: UUID
    concept_slug: str
    concept_name: str
    mastery_score: float | None = None
    reason: str


class LearningPathItemRead(CortexSchema):
    id: UUID
    concept_id: UUID
    concept_slug: str
    concept_name: str
    position: int
    item_type: LearningPathItemType
    status: LearningPathItemStatus
    unlock_condition: str | None


class LearningPathRead(CortexSchema):
    id: UUID
    user_id: UUID
    learner_profile_id: UUID | None
    domain_key: str
    status: LearningPathStatus
    version: int
    is_active: bool
    rationale: str | None
    roadmap: dict | None = None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[LearningPathItemRead]


class CurriculumPlanResponse(CortexSchema):
    user_id: UUID
    domain_key: str
    generated_at: datetime
    mastery_thresholds: dict[str, float]
    skipped_concepts: list[CurriculumConceptSummary]
    actionable_concepts: list[CurriculumConceptSummary]
    learning_path: LearningPathRead

