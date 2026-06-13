from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LessonStatus, QuizType

if TYPE_CHECKING:
    from app.models.curriculum import Concept, LearningPathItem
    from app.models.user import User


class Lesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lessons"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    learning_path_item_id: Mapped[UUID | None] = mapped_column(ForeignKey("learning_path_items.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"),
        default=LessonStatus.DRAFT,
        nullable=False,
    )
    content_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    personalization_context: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="lessons", passive_deletes=True)
    concept: Mapped["Concept"] = relationship(back_populates="lessons")
    learning_path_item: Mapped["LearningPathItem | None"] = relationship(back_populates="lessons")


class Quiz(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quizzes"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    learning_path_item_id: Mapped[UUID | None] = mapped_column(ForeignKey("learning_path_items.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quiz_type: Mapped[QuizType] = mapped_column(
        Enum(QuizType, name="quiz_type"),
        nullable=False,
    )
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    configuration: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="quizzes", passive_deletes=True)
    concept: Mapped["Concept"] = relationship(back_populates="quizzes")
    learning_path_item: Mapped["LearningPathItem | None"] = relationship(back_populates="quizzes")
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
    )


class QuizAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    submitted_answers: Mapped[dict | None] = mapped_column(JSON)
    feedback_payload: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None]

    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    user: Mapped["User"] = relationship(back_populates="quiz_attempts", passive_deletes=True)
