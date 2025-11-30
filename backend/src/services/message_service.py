"""消息服务

处理消息的创建、查询和图表关联逻辑
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.message import Message, MessageRole
from src.models.chart import Chart
from src.config.logging import get_logger

logger = get_logger(__name__)


class MessageService:
    """消息服务类"""

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def create_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> Message:
        """创建新消息

        Args:
            session_id: 会话ID
            role: 消息角色('user' | 'assistant')
            content: 消息内容
            metadata: 元数据(可选)

        Returns:
            Message: 创建的消息对象

        Note:
            sequence会由数据库触发器自动设置
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
            sequence=0,  # 触发器会自动设置正确的sequence
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        logger.info(
            f"创建消息成功 - "
            f"会话: {session_id}, "
            f"角色: {role}, "
            f"序号: {message.sequence}"
        )
        return message

    async def get_message(
        self,
        message_id: int,
        include_charts: bool = False,
    ) -> Optional[Message]:
        """获取消息详情

        Args:
            message_id: 消息ID
            include_charts: 是否预加载图表列表

        Returns:
            Optional[Message]: 消息对象,不存在返回None
        """
        query = select(Message).where(Message.id == message_id)

        if include_charts:
            query = query.options(selectinload(Message.charts))

        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if message:
            logger.debug(f"获取消息成功 - ID: {message_id}")
        else:
            logger.warning(f"消息不存在 - ID: {message_id}")

        return message

    async def list_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
        after_sequence: Optional[int] = None,
        include_charts: bool = True,
    ) -> List[Message]:
        """获取会话的消息列表

        Args:
            session_id: 会话ID
            limit: 限制数量(可选)
            after_sequence: 获取sequence大于此值的消息(用于增量加载)
            include_charts: 是否预加载图表

        Returns:
            List[Message]: 消息列表,按sequence升序
        """
        query = select(Message).where(Message.session_id == session_id)

        if after_sequence is not None:
            query = query.where(Message.sequence > after_sequence)

        query = query.order_by(Message.sequence.asc())

        if limit:
            query = query.limit(limit)

        if include_charts:
            query = query.options(selectinload(Message.charts))

        result = await self.db.execute(query)
        messages = result.scalars().all()

        logger.info(
            f"查询消息列表 - "
            f"会话: {session_id}, "
            f"返回: {len(messages)} 条"
        )
        return list(messages)

    async def add_chart_to_message(
        self,
        message_id: int,
        chart_type: str,
        chart_config: dict,
        sequence: int = 0,
    ) -> Chart:
        """为消息添加图表

        Args:
            message_id: 消息ID
            chart_type: 图表类型
            chart_config: 图表配置(AntV G2格式)
            sequence: 图表在消息中的序号

        Returns:
            Chart: 创建的图表对象
        """
        chart = Chart(
            message_id=message_id,
            chart_type=chart_type,
            chart_config=chart_config,
            sequence=sequence,
        )

        self.db.add(chart)
        await self.db.flush()
        await self.db.refresh(chart)

        logger.info(
            f"添加图表成功 - "
            f"消息: {message_id}, "
            f"类型: {chart_type}, "
            f"序号: {sequence}"
        )
        return chart

    async def add_multiple_charts(
        self,
        message_id: int,
        charts_data: List[dict],
    ) -> List[Chart]:
        """为消息批量添加图表

        Args:
            message_id: 消息ID
            charts_data: 图表数据列表,每个元素包含:
                - chart_type: 图表类型
                - chart_config: 图表配置
                - sequence: 序号(可选)

        Returns:
            List[Chart]: 创建的图表对象列表
        """
        charts = []
        for i, chart_data in enumerate(charts_data):
            chart = Chart(
                message_id=message_id,
                chart_type=chart_data["chart_type"],
                chart_config=chart_data["chart_config"],
                sequence=chart_data.get("sequence", i),
            )
            charts.append(chart)

        self.db.add_all(charts)
        await self.db.flush()

        for chart in charts:
            await self.db.refresh(chart)

        logger.info(
            f"批量添加图表成功 - "
            f"消息: {message_id}, "
            f"数量: {len(charts)}"
        )
        return charts

    async def get_recent_messages_for_context(
        self,
        session_id: UUID,
        limit: int = 10,
    ) -> List[dict]:
        """获取最近的消息用于对话上下文

        返回格式适合传递给Deep Research API

        Args:
            session_id: 会话ID
            limit: 最多获取多少条消息

        Returns:
            List[dict]: 消息列表,格式为[{"role": "user", "content": "..."}, ...]
        """
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.sequence.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # 反转顺序(最旧的在前)
        messages = list(reversed(messages))

        # 转换为API格式
        context = [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

        logger.debug(
            f"获取对话上下文 - "
            f"会话: {session_id}, "
            f"消息数: {len(context)}"
        )
        return context
