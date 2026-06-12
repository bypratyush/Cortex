from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import GoalType, LearningStyle, MotivationType, TargetLevel, TimeCommitment
from app.schemas.common import CortexSchema
from app.schemas.users import UserRead


class LearnerProfileBase(CortexSchema):
    goal: GoalType
    target_level: TargetLevel
    time_commitment: TimeCommitment
    learning_style: LearningStyle
    motivation: MotivationType
    current_level_summary: str | None = Field(default=None, max_length=2000)
    domain_key: str = Field(default="python_programming", max_length=100)


class LearnerProfileUpsert(LearnerProfileBase):
    pass


class LearnerProfileRead(LearnerProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    structured_understanding: dict | None = Field(default=None)


class LearnerOnboardingResponse(CortexSchema):
    user: UserRead
    learner_profile: LearnerProfileRead

