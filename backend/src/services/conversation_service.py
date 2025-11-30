"""对话服务

集成 LangChain Agent、MCP 客户端和 SSE 服务
处理完整的对话流程
"""
import asyncio
import re
from typing import AsyncGenerator, Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage

from src.services.langchain_agent import get_agent_service
from src.services.mcp_client import get_mcp_client
from src.services.message_service import MessageService
from src.services.sse_service import SSEService
from src.config.logging import get_logger

logger = get_logger(__name__)


class ConversationService:
    """对话服务类 - 使用 LangChain Agent"""

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
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
    ) -> AsyncGenerator[str, None]:
        """流式对话处理

        1. 获取历史上下文
        2. 调用 LangChain Agent 流式 API
        3. 实时流式返回文本片段
        4. 检测和生成图表
        5. 保存 assistant 消息和图表

        Args:
            session_id: 会话ID
            user_query: 用户查询

        Yields:
            str: SSE事件字符串
        """
        logger.info(f"开始流式对话 - 会话: {session_id}")

        try:
            # 获取历史上下文(最近10条消息)
            history_messages = await self.message_service.get_recent_messages_for_context(
                session_id=session_id,
                limit=10,
            )

            # 转换为 LangChain 消息格式
            chat_history = self._convert_to_langchain_messages(history_messages)

            # 流式调用 LangChain Agent
            full_content = ""
            async for chunk in self.agent_service.chat_stream(
                message=user_query,
                chat_history=chat_history,
                session_id=str(session_id),
            ):
                full_content += chunk

                # 发送文本片段事件
                yield await self.sse_service.send_message_chunk(
                    content=chunk,
                    is_final=False,
                )

            # 发送最终片段
            yield await self.sse_service.send_message_chunk(
                content="",
                is_final=True,
            )

            logger.info(f"LangChain Agent 响应完成 - 长度: {len(full_content)}")

            # 解析响应中的图表数据
            charts_data = self._extract_chart_data(full_content)

            # 保存assistant消息
            message = await self.message_service.create_message(
                session_id=session_id,
                role="assistant",
                content=full_content,
                metadata={  # 参数名保持为 metadata，内部会映射到 message_metadata
                    "model": "qwen-plus",
                    "tokens": len(full_content),
                    "chart_count": len(charts_data),
                    "powered_by": "langchain",
                }
            )

            await self.db.flush()
            await self.db.refresh(message)

            # 如果有图表数据,生成并保存图表
            chart_objects = []
            for i, chart_data in enumerate(charts_data):
                try:
                    # 调用MCP服务器生成图表配置
                    chart_config = await self.mcp_client.generate_chart(
                        data=chart_data["data"],
                        chart_type=chart_data.get("chart_type"),
                        title=chart_data.get("title"),
                    )

                    # 保存图表
                    chart = await self.message_service.add_chart_to_message(
                        message_id=message.id,
                        chart_type=chart_config.get("type", "unknown"),
                        chart_config=chart_config,
                        sequence=i,
                    )

                    chart_objects.append(chart)

                    # 发送图表就绪事件
                    yield await self.sse_service.send_chart_ready(
                        chart_id=str(chart.id),
                        chart_type=chart.chart_type,
                        chart_config=chart.chart_config,
                        sequence=i,
                    )

                except Exception as e:
                    logger.error(f"图表生成失败 - 序号: {i}, 错误: {e}")
                    # 继续处理其他图表,不中断流程

            # 提交事务
            await self.db.commit()

            # 发送消息完成事件
            yield await self.sse_service.send_message_complete(
                message_id=message.id,
                sequence=message.sequence,
                total_charts=len(chart_objects),
            )

            logger.info(
                f"对话完成 - "
                f"消息ID: {message.id}, "
                f"图表数: {len(chart_objects)}"
            )

        except Exception as e:
            logger.error(f"对话处理失败: {e}", exc_info=True)

            # 发送错误事件
            yield await self.sse_service.send_error(
                error_code="conversation_error",
                error_message=str(e),
            )

            # 回滚事务
            await self.db.rollback()
            raise

    def _convert_to_langchain_messages(
        self, history_messages: List[Dict[str, Any]]
    ) -> List:
        """将消息历史转换为 LangChain 消息格式

        Args:
            history_messages: 原始消息历史

        Returns:
            List: LangChain 消息列表
        """
        langchain_messages = []

        for msg in history_messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))

        return langchain_messages

    def _extract_chart_data(self, content: str) -> List[Dict[str, Any]]:
        """从AI响应中提取图表数据

        查找特定格式的JSON数据块,例如:
        ```json:chart
        {
          "data": [...],
          "chart_type": "bar",
          "title": "销售数据"
        }
        ```

        Args:
            content: AI响应文本

        Returns:
            List[dict]: 图表数据列表
        """
        charts = []

        # 匹配 ```json:chart ... ``` 代码块
        pattern = r'```json:chart\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            try:
                import json
                chart_data = json.loads(match)
                if "data" in chart_data and isinstance(chart_data["data"], list):
                    charts.append(chart_data)
                    logger.debug(f"提取到图表数据 - 类型: {chart_data.get('chart_type', 'auto')}")
            except json.JSONDecodeError as e:
                logger.warning(f"图表JSON解析失败: {e}")

        logger.info(f"从响应中提取到 {len(charts)} 个图表")
        return charts
