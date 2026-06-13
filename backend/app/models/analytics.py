from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Analytics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_analytics_user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lessons_completed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quizzes_attempted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="analytics", passive_deletes=True)
