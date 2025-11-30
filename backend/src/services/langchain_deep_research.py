"""Deep Research 作为 LangChain 工具

将通义 Deep Research 功能包装为 LangChain 工具
可以在 LangChain Agent 中调用 Deep Research
"""
import asyncio
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.services.deep_research_client import get_deep_research_client
from src.config.logging import get_logger

logger = get_logger(__name__)


class DeepResearchInput(BaseModel):
    """Deep Research 工具输入模型"""

    query: str = Field(
        description="需要深度研究的问题或主题"
    )
    max_tokens: Optional[int] = Field(
        default=4096,
        description="最大生成 token 数"
    )


class DeepResearchTool(BaseTool):
    """Deep Research 工具

    用于深度研究和分析复杂问题
    适合需要多步推理、网络搜索和综合分析的场景
    """

    name: str = "deep_research"
    description: str = (
        "深度研究工具。用于分析复杂问题、进行多步推理和综合研究。"
        "当用户的问题需要深入分析、多角度思考或需要搜索最新信息时使用此工具。"
        "例如：市场分析、技术调研、学术问题等。"
    )
    args_schema: Type[BaseModel] = DeepResearchInput

    # Pydantic 字段声明
    class Config:
        arbitrary_types_allowed = True

    async def _arun(
        self,
        query: str,
        max_tokens: Optional[int] = 4096,
    ) -> str:
        """异步执行深度研究

        Args:
            query: 研究问题
            max_tokens: 最大 token 数

        Returns:
            str: 研究结果
        """
        try:
            logger.info(f"LangChain: 调用 Deep Research - 问题: {query[:50]}...")

            # 每次调用时获取客户端
            client = get_deep_research_client()

            # 流式调用 Deep Research 并收集完整响应
            full_response = ""
            async for chunk in client.stream_chat(
                query=query,
                session_history=[],
            ):
                full_response += chunk

            logger.info(f"LangChain: Deep Research 完成 - 长度: {len(full_response)}")
            return full_response

        except Exception as e:
            error_msg = f"Deep Research 调用失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"错误: {error_msg}"

    def _run(
        self,
        query: str,
        max_tokens: Optional[int] = 4096,
    ) -> str:
        """同步执行（内部调用异步方法）"""
        return asyncio.run(self._arun(query=query, max_tokens=max_tokens))


def get_deep_research_tool() -> DeepResearchTool:
    """获取 Deep Research 工具实例

    Returns:
        DeepResearchTool: Deep Research 工具
    """
    return DeepResearchTool()
