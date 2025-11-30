"""LangChain MCP 工具集成

将 MCP server 的工具和 Deep Research 包装为 LangChain 工具
"""
import asyncio
import json
from typing import Any, Dict, List, Optional, Type, Union

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.services.mcp_client import MCPClient
from src.services.langchain_deep_research import get_deep_research_tool
from src.config.logging import get_logger

logger = get_logger(__name__)


class ChartGenerationInput(BaseModel):
    """图表生成工具的输入模型"""

    data: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(
        description=(
            "图表数据，支持两种格式:\n"
            "1. 列表格式（大多数图表）: [{'category': 'A', 'value': 100}, ...]\n"
            "2. 树形对象（思维导图、组织架构图等）: {'name': '主题', 'children': [{'name': '子主题1'}, ...]}"
        )
    )
    chart_type: Optional[str] = Field(
        default="column",
        description=(
            "图表类型，支持: column(柱形图), bar(条形图), line(折线图), "
            "area(���积图), pie(饼图), scatter(散点图), radar(雷达图), "
            "mindmap(思维导图), fishbone(鱼骨图), flow(流程图), organization(组织架构图) 等"
        ),
    )
    title: Optional[str] = Field(default=None, description="图表标题")
    description: Optional[str] = Field(default=None, description="图表描述")


class MCPChartTool(BaseTool):
    """MCP 图表生成工具

    通过 MCP server 生成各种类型的图表
    """

    name: str = "generate_chart"
    description: str = (
        "生成数据可视化图表。"
        "当需要将数据以图表形式展示时使用此工具。"
        "支持多种图表类型：柱状图、折线图、饼图、散点图、思维导图、组织架构图等。"
        "数据格式：列表（普通图表）或树形对象（思维导图等）。"
    )
    args_schema: Type[BaseModel] = ChartGenerationInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _arun(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        chart_type: Optional[str] = "column",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """异步执行图表生成

        Args:
            data: 图表数据（列表或树形对象）
            chart_type: 图表类型
            title: 图表标题
            description: 图表描述

        Returns:
            str: 图表配置的 JSON 字符串
        """
        try:
            # 为每次调用创建新的 MCP 客户端
            mcp_client = MCPClient()

            # 连接
            await mcp_client.connect()

            # 记录数据类型和大小
            if isinstance(data, list):
                logger.info(f"LangChain: 生成图表 - 类型: {chart_type}, 数据点: {len(data)}")
            else:
                logger.info(f"LangChain: 生成图表 - 类型: {chart_type}, 数据: 树形结构")

            # 调用 MCP 客户端生成图表
            chart_config = await mcp_client.generate_chart(
                data=data,
                chart_type=chart_type,
                title=title,
                description=description,
            )

            # 断开连接
            await mcp_client.disconnect()

            # 返回 JSON 字符串
            result = json.dumps(chart_config, ensure_ascii=False)
            logger.info(f"LangChain: 图表生成成功")

            return result

        except Exception as e:
            error_msg = f"图表生成失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

    def _run(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        chart_type: Optional[str] = "column",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """同步执行图表生成（内部调用异步方法）"""
        return asyncio.run(
            self._arun(data=data, chart_type=chart_type, title=title, description=description)
        )


def get_mcp_tools(include_deep_research: bool = True) -> List[BaseTool]:
    """获取所有 MCP 工具

    Args:
        include_deep_research: 是否包含 Deep Research 工具

    Returns:
        List[BaseTool]: LangChain 工具列表
    """
    tools = [MCPChartTool()]

    if include_deep_research:
        tools.append(get_deep_research_tool())

    return tools
