import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class User(SharedModel):
    __tablename__ = "users"

    discord_user_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)

    messages: Mapped[list["Message"]] = relationship(back_populates="user")


class Message(SharedModel):
    __tablename__ = "messages"

    discord_message_id: Mapped[str] = mapped_column(String, nullable=False)
    discord_user_id: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(768), nullable=True, unique=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="messages")
    channel: Mapped["Channel"] = relationship(back_populates="messages")

    __table_args__ = (
        Index(
            "ix_messages_embedding_vector_cosine",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding_vector": "vector_cosine_ops"},
        ),
        Index(
            "ix_messages_embedding_vector_l2",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding_vector": "vector_l2_ops"},
        ),
    )


class Guild(SharedModel):
    __tablename__ = "guilds"

    discord_guild_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)

    agents: Mapped[list["Agent"]] = relationship(back_populates="guild")
    channels: Mapped[list["Channel"]] = relationship(back_populates="guild")


class Channel(SharedModel):
    __tablename__ = "channels"

    discord_channel_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    guild_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False
    )

    agent: Mapped["Agent"] = relationship(back_populates="channel")
    guild: Mapped["Guild"] = relationship(back_populates="channels")
    messages: Mapped[list["Message"]] = relationship(back_populates="channel")


class Agent(SharedModel):
    __tablename__ = "agents"

    instruction: Mapped[str] = mapped_column(Text, nullable=True)
    discord_user_id: Mapped[str] = mapped_column(String, nullable=False)

    guild_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False
    )

    guild: Mapped["Guild"] = relationship(back_populates="agents")
    channel: Mapped["Channel"] = relationship(back_populates="agent")
