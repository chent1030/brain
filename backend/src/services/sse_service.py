"""SSE流式响应服务

生成SSE事件流,包括消息片段、图表就绪、完成等事件
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from enum import Enum

from src.config.logging import get_logger

logger = get_logger(__name__)


class SSEEventType(str, Enum):
    """SSE事件类型"""
    MESSAGE_CHUNK = "message_chunk"
    CHART_READY = "chart_ready"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"
    PING = "ping"


class SSEService:
    """SSE服务类"""

    @staticmethod
    def format_sse_event(
        event_type: str,
        data: Dict[str, Any],
        event_id: str = None,
    ) -> str:
        """格式化SSE事件

        Args:
            event_type: 事件类型
            data: 事件数据
            event_id: 事件ID(可选)

        Returns:
            str: 格式化的SSE消息（UTF-8编码的字符串）
        """
        lines = []

        if event_id:
            lines.append(f"id: {event_id}")

        lines.append(f"event: {event_type}")
        # 使用 ensure_ascii=False 保留中文字符
        lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        lines.append("")  # 空行表示事件结束

        return "\n".join(lines) + "\n"

    @staticmethod
    async def send_message_chunk(
        content: str,
        is_final: bool = False,
    ) -> str:
        """发送消息片段事件

        Args:
            content: 文本内容片段
            is_final: 是否为最后一个片段

        Returns:
            str: SSE事件字符串
        """
        return SSEService.format_sse_event(
            event_type=SSEEventType.MESSAGE_CHUNK.value,  # 使用 .value 获取字符串值
            data={
                "content": content,
                "is_final": is_final,
            }
        )

    @staticmethod
    async def send_chart_ready(
        chart_id: str,
        chart_type: str,
        chart_config: Dict[str, Any],
        sequence: int,
    ) -> str:
        """发送图表就绪事件

        Args:
            chart_id: 图表ID
            chart_type: 图表类型
            chart_config: 图表配置
            sequence: 图表序号

        Returns:
            str: SSE事件字符串
        """
        return SSEService.format_sse_event(
            event_type=SSEEventType.CHART_READY.value,
            data={
                "chart_id": chart_id,
                "chart_type": chart_type,
                "chart_config": chart_config,
                "sequence": sequence,
            }
        )

    @staticmethod
    async def send_message_complete(
        message_id: int,
        sequence: int,
        total_charts: int = 0,
    ) -> str:
        """发送消息完成事件

        Args:
            message_id: 消息ID
            sequence: 消息序号
            total_charts: 图表总数

        Returns:
            str: SSE事件字符串
        """
        return SSEService.format_sse_event(
            event_type=SSEEventType.MESSAGE_COMPLETE.value,
            data={
                "message_id": message_id,
                "sequence": sequence,
                "total_charts": total_charts,
            }
        )

    @staticmethod
    async def send_error(
        error_code: str,
        error_message: str,
    ) -> str:
        """发送错误事件

        Args:
            error_code: 错误代码
            error_message: 错误消息

        Returns:
            str: SSE事件字符串
        """
        return SSEService.format_sse_event(
            event_type=SSEEventType.ERROR.value,
            data={
                "error_code": error_code,
                "error_message": error_message,
            }
        )

    @staticmethod
    async def send_ping() -> str:
        """发送心跳事件(保持连接)

        Returns:
            str: SSE事件字符串
        """
        return SSEService.format_sse_event(
            event_type=SSEEventType.PING.value,
            data={"timestamp": asyncio.get_event_loop().time()}
        )

    @staticmethod
    async def generate_keepalive() -> AsyncGenerator[str, None]:
        """生成保持连接的心跳事件

        每30秒发送一次ping事件

        Yields:
            str: ping事件
        """
        while True:
            await asyncio.sleep(30)
            yield await SSEService.send_ping()
