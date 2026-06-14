from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import TutorConversationStatus, TutorMessageRole

if TYPE_CHECKING:
    from app.models.curriculum import Concept, LearningPathItem
    from app.models.user import User


class TutorConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tutor_conversations"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[UUID | None] = mapped_column(ForeignKey("concepts.id"))
    learning_path_item_id: Mapped[UUID | None] = mapped_column(ForeignKey("learning_path_items.id"))
    status: Mapped[TutorConversationStatus] = mapped_column(
        Enum(TutorConversationStatus, name="tutor_conversation_status"),
        default=TutorConversationStatus.ACTIVE,
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(Text)
    last_message_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="tutor_conversations", passive_deletes=True)
    concept: Mapped["Concept | None"] = relationship(back_populates="tutor_conversations")
    learning_path_item: Mapped["LearningPathItem | None"] = relationship(
        back_populates="tutor_conversations"
    )
    messages: Mapped[list["TutorMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class TutorMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tutor_messages"

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("tutor_conversations.id", ondelete="CASCADE"), nullable=False)
    referenced_concept_id: Mapped[UUID | None] = mapped_column(ForeignKey("concepts.id"))
    role: Mapped[TutorMessageRole] = mapped_column(
        Enum(TutorMessageRole, name="tutor_message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hint_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    conversation: Mapped["TutorConversation"] = relationship(back_populates="messages")
    referenced_concept: Mapped["Concept | None"] = relationship(back_populates="tutor_messages")
