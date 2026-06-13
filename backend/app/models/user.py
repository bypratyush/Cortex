from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.analytics import Analytics
    from app.models.assessment import AssessmentResult, MasteryRecord
    from app.models.content import Lesson, Quiz, QuizAttempt
    from app.models.curriculum import LearnerProfile, LearningPath
    from app.models.tutoring import TutorConversation


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    auth_provider: Mapped[str | None] = mapped_column(String(50))
    auth_subject: Mapped[str | None] = mapped_column(String(255), unique=True)

    learner_profile: Mapped["LearnerProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    learning_paths: Mapped[list["LearningPath"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    mastery_records: Mapped[list["MasteryRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    tutor_conversations: Mapped[list["TutorConversation"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    analytics: Mapped["Analytics | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
