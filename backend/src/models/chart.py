"""Chart模型 - 图表表"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import BigInteger, String, Integer, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, JSONB

from src.models.base import Base


class Chart(Base):
    """图表模型

    存储MCP服务器(@antv/mcp-server-chart)生成的图表配置
    一条assistant消息可能包含多个图表
    """
    __tablename__ = 'charts'

    # 主键
    id: Mapped[UUID] = mapped_column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # 外键
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('messages.id', ondelete='CASCADE'),
        nullable=False
    )

    # 图表信息
    chart_type: Mapped[str] = mapped_column(String(50), nullable=False)
    chart_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, server_default='0', nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )

    # 关系
    message: Mapped["Message"] = relationship("Message", back_populates="charts")

    # 索引定义
    __table_args__ = (
        Index('idx_charts_message', 'message_id', 'sequence'),
        Index('idx_charts_type', 'chart_type'),
    )

    def __repr__(self) -> str:
        return f"<Chart(id={self.id}, message_id={self.message_id}, type='{self.chart_type}', sequence={self.sequence})>"

    @property
    def config_summary(self) -> str:
        """返回配置摘要用于调试"""
        config_keys = list(self.chart_config.keys()) if self.chart_config else []
        return f"Chart config keys: {', '.join(config_keys)}"
