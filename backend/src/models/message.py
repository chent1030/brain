"""Message模型 - 消息表"""
from datetime import datetime
from uuid import UUID
from enum import Enum
from sqlalchemy import BigInteger, String, Text, Integer, TIMESTAMP, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB

from src.models.base import Base


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """消息模型

    存储用户和AI的对话消息
    支持流式消息和元数据(tokens, model等)
    """
    __tablename__ = 'messages'

    # 主键
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 外键
    session_id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey('sessions.id', ondelete='CASCADE'),
        nullable=False
    )

    # 消息内容
    role: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("role IN ('user', 'assistant')", name='check_messages_role'),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 序列和元数据
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    message_metadata: Mapped[dict | None] = mapped_column('metadata', JSONB, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )

    # 关系
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    charts: Mapped[list["Chart"]] = relationship(
        "Chart",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="Chart.sequence"
    )

    # 索引定义
    __table_args__ = (
        Index('idx_messages_session_sequence', 'session_id', 'sequence'),
        Index('idx_messages_session_created', 'session_id', 'created_at'),
        Index('idx_messages_created_brin', 'created_at', postgresql_using='brin'),
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', sequence={self.sequence}, content='{content_preview}')>"

    @property
    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self.role == MessageRole.USER.value

    @property
    def is_assistant_message(self) -> bool:
        """检查是否为助手消息"""
        return self.role == MessageRole.ASSISTANT.value
