import uuid

from sqlalchemy import (
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .core.database import Base


class SharedModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DiscordAgent(SharedModel):
    __tablename__ = "discord_agents"

    server_id: Mapped[str] = mapped_column(String, nullable=False)
    channel_id: Mapped[str] = mapped_column(String, nullable=False)
    discord_user_id: Mapped[str] = mapped_column(String, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=True)
