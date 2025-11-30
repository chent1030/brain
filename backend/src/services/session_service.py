"""会话服务

处理会话的创建、查询、更新和删除逻辑
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.session import Session
from src.models.message import Message
from src.config.logging import get_logger

logger = get_logger(__name__)


class SessionService:
    """会话服务类"""

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def create_session(
        self,
        user_id: int,
        title: Optional[str] = None,
    ) -> Session:
        """创建新会话

        Args:
            user_id: 用户ID
            title: 会话标题(可选)

        Returns:
            Session: 创建的会话对象
        """
        session = Session(
            user_id=user_id,
            title=title or "新对话",
        )

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        logger.info(f"创建会话成功 - ID: {session.id}, 用户: {user_id}")
        return session

    async def get_session(
        self,
        session_id: UUID,
        user_id: int,
        include_messages: bool = False,
    ) -> Optional[Session]:
        """获取会话详情

        Args:
            session_id: 会话ID
            user_id: 用户ID(权限验证)
            include_messages: 是否预加载消息列表

        Returns:
            Optional[Session]: 会话对象,不存在或无权限返回None
        """
        query = select(Session).where(
            and_(
                Session.id == session_id,
                Session.user_id == user_id,
                Session.deleted_at.is_(None),
            )
        )

        if include_messages:
            query = query.options(selectinload(Session.messages))

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"获取会话成功 - ID: {session_id}")
        else:
            logger.warning(f"会话不存在或无权限 - ID: {session_id}, 用户: {user_id}")

        return session

    async def list_sessions(
        self,
        user_id: int,
        limit: int = 20,
        before_updated_at: Optional[datetime] = None,
    ) -> List[Session]:
        """获取用户会话列表(分页)

        使用键集分页(keyset pagination)优化性能

        Args:
            user_id: 用户ID
            limit: 每页数量
            before_updated_at: 上一页最后一条的updated_at(用于分页)

        Returns:
            List[Session]: 会话列表,按updated_at降序
        """
        query = (
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.deleted_at.is_(None),
                )
            )
            .order_by(Session.updated_at.desc())
            .limit(limit)
        )

        if before_updated_at:
            query = query.where(Session.updated_at < before_updated_at)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        logger.info(f"查询会话列表 - 用户: {user_id}, 返回: {len(sessions)} 条")
        return list(sessions)

    async def update_session_title(
        self,
        session_id: UUID,
        user_id: int,
        title: str,
    ) -> Optional[Session]:
        """更新会话标题

        Args:
            session_id: 会话ID
            user_id: 用户ID(权限验证)
            title: 新标题

        Returns:
            Optional[Session]: 更新后的会话对象,失败返回None
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return None

        session.title = title
        await self.db.flush()
        await self.db.refresh(session)

        logger.info(f"更新会话标题 - ID: {session_id}, 标题: {title}")
        return session

    async def soft_delete_session(
        self,
        session_id: UUID,
        user_id: int,
    ) -> bool:
        """软删除会话

        Args:
            session_id: 会话ID
            user_id: 用户ID(权限验证)

        Returns:
            bool: 是否删除成功
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        session.deleted_at = datetime.utcnow()
        await self.db.flush()

        logger.info(f"软删除会话 - ID: {session_id}")
        return True

    async def get_session_stats(
        self,
        user_id: int,
    ) -> dict:
        """获取用户会话统计

        Args:
            user_id: 用户ID

        Returns:
            dict: 统计信息
        """
        # 总会话数
        total_query = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.deleted_at.is_(None),
            )
        )
        total_result = await self.db.execute(total_query)
        total_count = len(total_result.scalars().all())

        # 总消息数
        message_count_query = select(Session.message_count).where(
            and_(
                Session.user_id == user_id,
                Session.deleted_at.is_(None),
            )
        )
        message_result = await self.db.execute(message_count_query)
        total_messages = sum(message_result.scalars().all())

        return {
            "total_sessions": total_count,
            "total_messages": total_messages,
        }
