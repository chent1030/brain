"""消息管理API端点

处理消息的创建和查询
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.config.database import get_db_session
from src.utils.auth import get_default_user_id
from src.services.session_service import SessionService
from src.services.message_service import MessageService
from src.models.message import Message
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic响应模型
class ChartResponse(BaseModel):
    """图表响应模型"""
    id: str
    chart_type: str
    chart_config: dict
    sequence: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    session_id: str
    role: str
    content: str
    sequence: int
    metadata: Optional[dict]
    created_at: datetime
    charts: List[ChartResponse] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_message(cls, message: Message) -> "MessageResponse":
        """从ORM模型创建响应"""
        return cls(
            id=message.id,
            session_id=str(message.session_id),
            role=message.role,
            content=message.content,
            sequence=message.sequence,
            metadata=message.message_metadata,
            created_at=message.created_at,
            charts=[
                ChartResponse(
                    id=str(chart.id),
                    chart_type=chart.chart_type,
                    chart_config=chart.chart_config,
                    sequence=chart.sequence,
                    created_at=chart.created_at,
                )
                for chart in message.charts
            ] if message.charts else [],
        )


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]


class CreateMessageRequest(BaseModel):
    """创建消息请求"""
    content: str = Field(..., description="消息内容", min_length=1)


class CreateMessageResponse(BaseModel):
    """创建消息响应"""
    message_id: int
    session_id: str
    sequence: int


# API端点
@router.post("/sessions/{session_id}/messages", response_model=CreateMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: UUID,
    request: CreateMessageRequest,
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """发送用户消息

    创建一条用户消息,AI响应通过SSE流式返回

    Args:
        session_id: 会话ID
        request: 创建请求
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        CreateMessageResponse: 创建的消息信息

    Raises:
        HTTPException: 会话不存在或无权限
    """
    # 验证会话存在且用户有权限
    session_service = SessionService(db)
    session = await session_service.get_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )

    # 创建用户消息
    message_service = MessageService(db)
    message = await message_service.create_message(
        session_id=session_id,
        role="user",
        content=request.content,
    )

    await db.commit()

    logger.info(
        f"创建用户消息成功 - "
        f"会话: {session_id}, "
        f"消息ID: {message.id}"
    )

    return CreateMessageResponse(
        message_id=message.id,
        session_id=str(session_id),
        sequence=message.sequence,
    )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: UUID,
    limit: Optional[int] = Query(None, ge=1, le=200, description="限制数量"),
    after_sequence: Optional[int] = Query(None, ge=0, description="获取sequence大于此值的消息"),
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话的消息列表

    Args:
        session_id: 会话ID
        limit: 限制数量
        after_sequence: 获取sequence大于此值的消息(用于增量加载)
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        MessageListResponse: 消息列表(包含图表)

    Raises:
        HTTPException: 会话不存在或无权限
    """
    # 验证会话存在且用户有权限
    session_service = SessionService(db)
    session = await session_service.get_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )

    # 查询消息
    message_service = MessageService(db)
    messages = await message_service.list_messages(
        session_id=session_id,
        limit=limit,
        after_sequence=after_sequence,
        include_charts=True,
    )

    return MessageListResponse(
        messages=[MessageResponse.from_orm_message(m) for m in messages]
    )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """获取单条消息详情

    Args:
        message_id: 消息ID
        db: 数据库会话

    Returns:
        MessageResponse: 消息详情(包含图表)

    Raises:
        HTTPException: 消息不存在
    """
    message_service = MessageService(db)
    message = await message_service.get_message(
        message_id=message_id,
        include_charts=True,
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"消息不存在: {message_id}"
        )

    return MessageResponse.from_orm_message(message)
