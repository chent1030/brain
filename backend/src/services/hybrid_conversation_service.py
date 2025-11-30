"""混合模式对话服务

支持三种模式:
1. pure_deep_research: 纯 Deep Research 模式
2. pure_langchain: 纯 LangChain Agent 模式
3. hybrid: 混合模式 (LangChain Agent + Deep Research 工具)
"""
import asyncio
import re
from typing import AsyncGenerator, Optional, List, Dict, Any, Literal
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
# 不再需要 LangChain messages

from src.services.deep_research_client import get_deep_research_client
from src.services.langchain_agent import get_agent_service
from src.services.mcp_client import get_mcp_client
from src.services.message_service import MessageService
from src.services.sse_service import SSEService
from src.config.logging import get_logger

logger = get_logger(__name__)


class ConversationMode(str, Enum):
    """对话模式枚举"""
    PURE_DEEP_RESEARCH = "pure_deep_research"  # 纯 Deep Research
    PURE_LANGCHAIN = "pure_langchain"          # 纯 LangChain
    HYBRID = "hybrid"                           # 混合模式 (推荐)


class HybridConversationService:
    """混合模式对话服务类"""

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.deep_research_client = get_deep_research_client()
        self.agent_service = get_agent_service(
            model_name="qwen-plus",
            temperature=0.7,
            streaming=True,
        )
        self.mcp_client = get_mcp_client()
        self.message_service = MessageService(db)
        self.sse_service = SSEService()

    async def stream_conversation(
        self,
        session_id: UUID,
        user_query: str,
        mode: ConversationMode = ConversationMode.HYBRID,
    ) -> AsyncGenerator[str, None]:
        """流式对话处理 (支持多种模式)

        Args:
            session_id: 会话ID
            user_query: 用户查询
            mode: 对话模式

        Yields:
            str: SSE事件字符串
        """
        logger.info(f"开始流式对话 - 会话: {session_id}, 模式: {mode.value}")

        if mode == ConversationMode.PURE_DEEP_RESEARCH:
            # 纯 Deep Research 模式
            async for event in self._stream_pure_deep_research(session_id, user_query):
                yield event

        elif mode == ConversationMode.PURE_LANGCHAIN:
            # 纯 LangChain 模式 (不包含 Deep Research 工具)
            async for event in self._stream_pure_langchain(session_id, user_query):
                yield event

        else:  # HYBRID
            # 混合模式 (LangChain Agent 可以调用 Deep Research)
            async for event in self._stream_hybrid(session_id, user_query):
                yield event

    async def _stream_pure_deep_research(
        self,
        session_id: UUID,
        user_query: str,
    ) -> AsyncGenerator[str, None]:
        """纯 Deep Research 模式"""
        try:
            history = await self.message_service.get_recent_messages_for_context(
                session_id=session_id,
                limit=10,
            )

            full_content = ""
            async for chunk in self.deep_research_client.stream_chat(
                query=user_query,
                session_history=history,
            ):
                full_content += chunk
                yield await self.sse_service.send_message_chunk(
                    content=chunk,
                    is_final=False,
                )

            yield await self.sse_service.send_message_chunk(
                content="",
                is_final=True,
            )

            # 保存消息和处理图表
            async for event in self._save_message_and_charts(
                session_id, full_content, "deep_research"
            ):
                yield event

        except Exception as e:
            logger.error(f"Deep Research 模式失败: {e}", exc_info=True)
            yield await self.sse_service.send_error(
                error_code="deep_research_error",
                error_message=str(e),
            )
            await self.db.rollback()
            raise

    async def _stream_pure_langchain(
        self,
        session_id: UUID,
        user_query: str,
    ) -> AsyncGenerator[str, None]:
        """纯 LangChain 模式 (不包含 Deep Research)"""
        try:
            history_messages = await self.message_service.get_recent_messages_for_context(
                session_id=session_id,
                limit=10,
            )
            # 转换为通义 API 格式
            chat_history = self._convert_to_tongyi_messages(history_messages)

            full_content = ""
            async for chunk in self.agent_service.chat_stream(
                message=user_query,
                chat_history=chat_history,
                session_id=str(session_id),
            ):
                full_content += chunk
                yield await self.sse_service.send_message_chunk(
                    content=chunk,
                    is_final=False,
                )

            yield await self.sse_service.send_message_chunk(
                content="",
                is_final=True,
            )

            # 保存消息和处理图表
            # 从Agent服务获取图表信息，而不是从消息内容提取
            async for event in self._save_message_and_charts_from_agent(
                session_id, full_content, "langchain"
            ):
                yield event

        except Exception as e:
            logger.error(f"LangChain 模式失败: {e}", exc_info=True)
            yield await self.sse_service.send_error(
                error_code="langchain_error",
                error_message=str(e),
            )
            await self.db.rollback()
            raise

    async def _stream_hybrid(
        self,
        session_id: UUID,
        user_query: str,
    ) -> AsyncGenerator[str, None]:
        """混合模式 (LangChain Agent + Deep Research 工具)"""
        # 混合模式使用 LangChain Agent，但包含 Deep Research 工具
        # Agent 会根据需要自动选择是否调用 Deep Research
        async for event in self._stream_pure_langchain(session_id, user_query):
            yield event

    async def _save_message_and_charts(
        self,
        session_id: UUID,
        full_content: str,
        mode: str,
    ) -> AsyncGenerator[str, None]:
        """保存消息和处理图表"""
        try:
            # 解析图表数据
            charts_data = self._extract_chart_data(full_content)

            # 保存消息
            message = await self.message_service.create_message(
                session_id=session_id,
                role="assistant",
                content=full_content,
                metadata={
                    "mode": mode,
                    "model": "qwen-plus" if mode == "langchain" else "qwen-max",
                    "tokens": len(full_content),
                    "chart_count": len(charts_data),
                }
            )

            await self.db.flush()
            await self.db.refresh(message)

            # 生成并保存图表
            chart_objects = []
            for i, chart_data in enumerate(charts_data):
                try:
                    # 检查图表数据格式
                    if "type" in chart_data and chart_data["type"] == "image":
                        # 新格式：已经有URL，直接保存
                        chart_config = {
                            "type": "image",
                            "url": chart_data["url"],
                            "tool": chart_data.get("tool", "unknown"),
                        }
                        chart_type = chart_data.get("chart_type", "image")
                    else:
                        # 旧格式：需要调用MCP生成图表
                        chart_config = await self.mcp_client.generate_chart(
                            data=chart_data["data"],
                            chart_type=chart_data.get("chart_type"),
                            title=chart_data.get("title"),
                        )
                        chart_type = chart_config.get("type", "unknown")

                    chart = await self.message_service.add_chart_to_message(
                        message_id=message.id,
                        chart_type=chart_type,
                        chart_config=chart_config,
                        sequence=i,
                    )

                    chart_objects.append(chart)

                    yield await self.sse_service.send_chart_ready(
                        chart_id=str(chart.id),
                        chart_type=chart.chart_type,
                        chart_config=chart.chart_config,
                        sequence=i,
                    )

                except Exception as e:
                    logger.error(f"图表生成失败: {e}", exc_info=True)

            await self.db.commit()

            yield await self.sse_service.send_message_complete(
                message_id=message.id,
                sequence=message.sequence,
                total_charts=len(chart_objects),
            )

        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)
            raise

    async def _save_message_and_charts_from_agent(
        self,
        session_id: UUID,
        full_content: str,
        mode: str,
    ) -> AsyncGenerator[str, None]:
        """保存消息和处理图表（从Agent服务获取图表信息）"""
        try:
            # 从Agent服务获取图表信息
            charts_data = self.agent_service.get_generated_charts()

            # 保存消息
            message = await self.message_service.create_message(
                session_id=session_id,
                role="assistant",
                content=full_content,
                metadata={
                    "mode": mode,
                    "model": "qwen-plus" if mode == "langchain" else "qwen-max",
                    "tokens": len(full_content),
                    "chart_count": len(charts_data),
                }
            )

            await self.db.flush()
            await self.db.refresh(message)

            # 保存图表（直接使用Agent记录的图表信息）
            chart_objects = []
            for i, chart_info in enumerate(charts_data):
                try:
                    chart = await self.message_service.add_chart_to_message(
                        message_id=message.id,
                        chart_type=chart_info.get("chart_type", "image"),
                        chart_config=chart_info,  # 直接使用图表信息
                        sequence=i,
                    )

                    chart_objects.append(chart)

                    yield await self.sse_service.send_chart_ready(
                        chart_id=str(chart.id),
                        chart_type=chart.chart_type,
                        chart_config=chart.chart_config,
                        sequence=i,
                    )

                    logger.info(f"图表已保存: {chart.chart_type}")

                except Exception as e:
                    logger.error(f"图表保存失败: {e}", exc_info=True)

            await self.db.commit()

            yield await self.sse_service.send_message_complete(
                message_id=message.id,
                sequence=message.sequence,
                total_charts=len(chart_objects),
            )

        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)
            raise

    def _convert_to_tongyi_messages(
        self, history_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """将消息历史转换为通义 API 消息格式"""
        tongyi_messages = []
        for msg in history_messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                tongyi_messages.append({"role": role, "content": content})
        return tongyi_messages

    def _extract_chart_data(self, content: str) -> List[Dict[str, Any]]:
        """从AI响应中提取图表数据

        支持两种格式：
        1. 旧格式（需要MCP生成）：{"data": [...], "chart_type": "...", "title": "..."}
        2. 新格式（已由MCP生成）：{"type": "image", "url": "...", "chart_type": "..."}
        """
        charts = []
        pattern = r'```json:chart\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            try:
                import json
                chart_data = json.loads(match)

                # 支持两种格式
                if "type" in chart_data and chart_data["type"] == "image":
                    # 新格式：已经由MCP生成的图表URL
                    charts.append(chart_data)
                elif "data" in chart_data and isinstance(chart_data["data"], list):
                    # 旧格式：包含原始数据，需要调用MCP生成
                    charts.append(chart_data)
                else:
                    logger.warning(f"未知的图表数据格式: {chart_data}")

            except json.JSONDecodeError as e:
                logger.warning(f"图表JSON解析失败: {e}")

        return charts


# 保持向后兼容
ConversationService = HybridConversationService
