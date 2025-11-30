"""SSE流式传输API端点

处理AI响应的实时流式传输
支持多种对话模式
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_session
from src.utils.auth import get_default_user_id
from src.services.session_service import SessionService
from src.services.hybrid_conversation_service import (
    HybridConversationService,
    ConversationMode,
)
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/sessions/{session_id}/stream")
async def stream_conversation(
    session_id: UUID,
    query: str,
    mode: Optional[str] = Query(
        default="hybrid",
        description="对话模式: pure_deep_research, pure_langchain, hybrid (推荐)"
    ),
    user_id: int = Depends(get_default_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """SSE流式传输AI响应

    客户端应该用EventSource连接此端点

    Args:
        session_id: 会话ID
        query: 用户查询(作为query参数传递)
        mode: 对话模式
            - pure_deep_research: 纯 Deep Research (适合深度研究)
            - pure_langchain: 纯 LangChain Agent (适合工具调用)
            - hybrid: 混合模式 (推荐，Agent 可调用 Deep Research)
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        StreamingResponse: SSE流式响应

    Raises:
        HTTPException: 会话不存在或无权限

    事件类型:
        - message_chunk: 文本片段 {content: str, is_final: bool}
        - chart_ready: 图表就绪 {chart_id: str, chart_type: str, chart_config: dict, sequence: int}
        - message_complete: 消息完成 {message_id: int, sequence: int, total_charts: int}
        - error: 错误 {error_code: str, error_message: str}
        - ping: 心跳(保持连接) {timestamp: float}
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

    # 验证模式
    try:
        conversation_mode = ConversationMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的模式: {mode}，支持: pure_deep_research, pure_langchain, hybrid"
        )

    logger.info(
        f"开始SSE流式传输 - "
        f"会话: {session_id}, "
        f"模式: {mode}, "
        f"查询: {query[:50]}..."
    )

    # 创建对话服务并开始流式响应
    conversation_service = HybridConversationService(db)

    async def event_generator():
        """SSE事件生成器"""
        try:
            async for event in conversation_service.stream_conversation(
                session_id=session_id,
                user_query=query,
                mode=conversation_mode,
            ):
                # 确保事件是字符串并编码为 UTF-8 bytes
                if isinstance(event, str):
                    yield event.encode('utf-8')
                else:
                    yield event
        except Exception as e:
            logger.error(f"SSE流生成错误: {e}", exc_info=True)
            # 发送错误事件后关闭连接
            from src.services.sse_service import SSEService
            error_event = await SSEService.send_error(
                error_code="stream_error",
                error_message=str(e),
            )
            yield error_event.encode('utf-8')

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )
