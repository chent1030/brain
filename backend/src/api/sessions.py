"""会话管理API端点

处理会话的创建、查询、更新和删除
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.config.database import get_db_session
from src.utils.auth import get_default_user_id
from src.services.session_service import SessionService
from src.models.session import Session
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic响应模型
class SessionResponse(BaseModel):
    """会话响应模型"""
    id: str
    user_id: int
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_session(cls, session: Session) -> "SessionResponse":
        """从ORM模型创建响应"""
        return cls(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            message_count=session.message_count,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse]
    has_more: bool


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: str = Field(..., description="新标题")


class SessionStatsResponse(BaseModel):
    """会话统计响应"""
    total_sessions: int
    total_messages: int


# API端点
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """创建新会话

    Args:
        request: 创建请求
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        SessionResponse: 创建的会话
    """
    service = SessionService(db)
    session = await service.create_session(
        user_id=user_id,
        title=request.title,
    )

    await db.commit()

    return SessionResponse.from_orm_session(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """获取会话详情

    Args:
        session_id: 会话ID
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        SessionResponse: 会话详情

    Raises:
        HTTPException: 会话不存在或无权限
    """
    service = SessionService(db)
    session = await service.get_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )

    return SessionResponse.from_orm_session(session)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    before: Optional[str] = Query(None, description="上一页最后一条的updated_at(ISO 8601格式)"),
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """获取用户会话列表(分页)

    使用键集分页,传递before参数获取下一页

    Args:
        limit: 每页数量
        before: 上一页最后一条的updated_at
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        SessionListResponse: 会话列表
    """
    # 解析before参数
    before_dt = None
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="before参数格式错误,应为ISO 8601格式"
            )

    service = SessionService(db)

    # 多获取1条用于判断是否有下一页
    sessions = await service.list_sessions(
        user_id=user_id,
        limit=limit + 1,
        before_updated_at=before_dt,
    )

    has_more = len(sessions) > limit
    if has_more:
        sessions = sessions[:limit]

    return SessionListResponse(
        sessions=[SessionResponse.from_orm_session(s) for s in sessions],
        has_more=has_more,
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    request: UpdateSessionRequest,
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """更新会话标题

    Args:
        session_id: 会话ID
        request: 更新请求
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        SessionResponse: 更新后的会话

    Raises:
        HTTPException: 会话不存在或无权限
    """
    service = SessionService(db)
    session = await service.update_session_title(
        session_id=session_id,
        user_id=user_id,
        title=request.title,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )

    await db.commit()

    return SessionResponse.from_orm_session(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """删除会话(软删除)

    Args:
        session_id: 会话ID
        user_id: 当前用户ID
        db: 数据库会话

    Raises:
        HTTPException: 会话不存在或无权限
    """
    service = SessionService(db)
    success = await service.soft_delete_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )

    await db.commit()


@router.get("/sessions/stats/summary", response_model=SessionStatsResponse)
async def get_session_stats(
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """获取用户会话统计

    Args:
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        SessionStatsResponse: 统计信息
    """
    service = SessionService(db)
    stats = await service.get_session_stats(user_id=user_id)

    return SessionStatsResponse(**stats)
