from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    GoalType,
    LearningPathItemStatus,
    LearningPathItemType,
    LearningPathStatus,
    LearningStyle,
    MotivationType,
    TargetLevel,
    TimeCommitment,
)

if TYPE_CHECKING:
    from app.models.assessment import AssessmentQuestion, AssessmentResult, MasteryRecord
    from app.models.content import Lesson, Quiz
    from app.models.tutoring import TutorConversation, TutorMessage
    from app.models.user import User


class LearnerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learner_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    domain_key: Mapped[str] = mapped_column(String(100), default="python_programming", nullable=False)
    goal: Mapped[GoalType] = mapped_column(Enum(GoalType, name="goal_type"), nullable=False)
    target_level: Mapped[TargetLevel] = mapped_column(
        Enum(TargetLevel, name="target_level"),
        nullable=False,
    )
    time_commitment: Mapped[TimeCommitment] = mapped_column(
        Enum(TimeCommitment, name="time_commitment"),
        nullable=False,
    )
    learning_style: Mapped[LearningStyle] = mapped_column(
        Enum(LearningStyle, name="learning_style"),
        nullable=False,
    )
    motivation: Mapped[MotivationType] = mapped_column(
        Enum(MotivationType, name="motivation_type"),
        nullable=False,
    )
    current_level_summary: Mapped[str | None] = mapped_column(Text)
    structured_understanding: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="learner_profile")
    learning_paths: Mapped[list["LearningPath"]] = relationship(back_populates="learner_profile")


class Concept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "concepts"
    __table_args__ = (
        UniqueConstraint("domain_key", "slug", name="uq_concepts_domain_slug"),
    )

    domain_key: Mapped[str] = mapped_column(String(100), default="python_programming", nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    concept_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prerequisites: Mapped[list["ConceptPrerequisite"]] = relationship(
        foreign_keys="ConceptPrerequisite.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan",
    )
    unlocked_by: Mapped[list["ConceptPrerequisite"]] = relationship(
        foreign_keys="ConceptPrerequisite.prerequisite_concept_id",
        back_populates="prerequisite_concept",
        cascade="all, delete-orphan",
    )
    assessment_questions: Mapped[list["AssessmentQuestion"]] = relationship(back_populates="concept")
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(back_populates="concept")
    mastery_records: Mapped[list["MasteryRecord"]] = relationship(back_populates="concept")
    learning_path_items: Mapped[list["LearningPathItem"]] = relationship(back_populates="concept")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="concept")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="concept")
    tutor_conversations: Mapped[list["TutorConversation"]] = relationship(back_populates="concept")
    tutor_messages: Mapped[list["TutorMessage"]] = relationship(back_populates="referenced_concept")


class ConceptPrerequisite(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "concept_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "concept_id",
            "prerequisite_concept_id",
            name="uq_concept_prerequisites_pair",
        ),
        CheckConstraint("concept_id <> prerequisite_concept_id", name="ck_concept_not_self"),
    )

    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    prerequisite_concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)

    concept: Mapped["Concept"] = relationship(
        foreign_keys=[concept_id],
        back_populates="prerequisites",
    )
    prerequisite_concept: Mapped["Concept"] = relationship(
        foreign_keys=[prerequisite_concept_id],
        back_populates="unlocked_by",
    )


class LearningPath(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_paths"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    learner_profile_id: Mapped[UUID | None] = mapped_column(ForeignKey("learner_profiles.id"))
    domain_key: Mapped[str] = mapped_column(String(100), default="python_programming", nullable=False)
    status: Mapped[LearningPathStatus] = mapped_column(
        Enum(LearningPathStatus, name="learning_path_status"),
        default=LearningPathStatus.DRAFT,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    roadmap: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="learning_paths")
    learner_profile: Mapped["LearnerProfile | None"] = relationship(back_populates="learning_paths")
    items: Mapped[list["LearningPathItem"]] = relationship(
        back_populates="learning_path",
        cascade="all, delete-orphan",
    )


class LearningPathItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_path_items"
    __table_args__ = (
        UniqueConstraint("learning_path_id", "position", name="uq_learning_path_items_position"),
    )

    learning_path_id: Mapped[UUID] = mapped_column(ForeignKey("learning_paths.id"), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    item_type: Mapped[LearningPathItemType] = mapped_column(
        Enum(LearningPathItemType, name="learning_path_item_type"),
        nullable=False,
    )
    status: Mapped[LearningPathItemStatus] = mapped_column(
        Enum(LearningPathItemStatus, name="learning_path_item_status"),
        default=LearningPathItemStatus.PENDING,
        nullable=False,
    )
    unlock_condition: Mapped[str | None] = mapped_column(Text)

    learning_path: Mapped["LearningPath"] = relationship(back_populates="items")
    concept: Mapped["Concept"] = relationship(back_populates="learning_path_items")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="learning_path_item")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="learning_path_item")
    tutor_conversations: Mapped[list["TutorConversation"]] = relationship(
        back_populates="learning_path_item"
    )
