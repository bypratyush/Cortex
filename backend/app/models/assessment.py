from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Float, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DifficultyLevel, QuestionType

if TYPE_CHECKING:
    from app.models.curriculum import Concept
    from app.models.user import User


class AssessmentQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_questions"

    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[str] | None] = mapped_column(JSON)
    expected_answer: Mapped[str | None] = mapped_column(Text)
    starter_code: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    concept: Mapped["Concept"] = relationship(back_populates="assessment_questions")
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(back_populates="question")


class AssessmentResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assessment_results"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    question_id: Mapped[UUID | None] = mapped_column(ForeignKey("assessment_questions.id"))
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"),
        nullable=False,
    )
    learner_response: Mapped[dict | None] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="assessment_results", passive_deletes=True)
    concept: Mapped["Concept"] = relationship(back_populates="assessment_results")
    question: Mapped["AssessmentQuestion | None"] = relationship(back_populates="assessment_results")


class MasteryRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mastery_records"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_mastery_records_user_concept"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quiz_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    practice_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_summary: Mapped[str | None] = mapped_column(String(500))
    last_evaluated_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="mastery_records", passive_deletes=True)
    concept: Mapped["Concept"] = relationship(back_populates="mastery_records")
