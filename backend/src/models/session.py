"""Session模型 - 会话表"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import BigInteger, String, Integer, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID

from src.models.base import Base


class Session(Base):
    """会话模型

    一个会话包含多条用户和AI的对话消息
    支持软删除(deleted_at)用于30天保留策略
    """
    __tablename__ = 'sessions'

    # 主键
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # 外键
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    # 会话信息
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, server_default='0', nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.sequence"
    )

    # 索引定义
    __table_args__ = (
        Index(
            'idx_sessions_user_updated',
            'user_id', 'updated_at',
            postgresql_where=(deleted_at.is_(None))
        ),
        Index(
            'idx_sessions_deleted',
            'deleted_at',
            postgresql_where=(deleted_at.isnot(None))
        ),
        Index(
            'idx_sessions_created_brin',
            'created_at',
            postgresql_using='brin'
        ),
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, message_count={self.message_count})>"

    @property
    def is_deleted(self) -> bool:
        """检查会话是否已被软删除"""
        return self.deleted_at is not None
