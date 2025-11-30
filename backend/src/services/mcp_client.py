"""MCP (Model Context Protocol) 客户端

与@antv/mcp-server-chart通信生成图表配置
通过 stdio 协议与 npx 启动的 MCP server 通信
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP服务器客户端

    与@antv/mcp-server-chart通信,根据数据生成AntV G2图表配置
    使用 stdio 协议通过 npx 启动 MCP server
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化MCP客户端

        Args:
            config_path: MCP配置文件路径
            timeout: 请求超时(秒)
        """
        self.timeout = timeout
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "../config/mcp_config.json"
        )
        self.session: Optional[ClientSession] = None
        self._exit_stack = None
        self._read = None
        self._write = None

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载MCP服务器配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.mcp_servers = config.get("mcpServers", {})
                logger.info(f"已加载MCP配置: {list(self.mcp_servers.keys())}")
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
            self.mcp_servers = {}

    async def connect(self, server_name: str = "mcp-server-chart"):
        """连接到MCP服务器

        Args:
            server_name: 服务器名称
        """
        if self.session is not None:
            logger.warning("MCP客户端已连接")
            return

        if server_name not in self.mcp_servers:
            raise ValueError(f"MCP服务器 '{server_name}' 未在配置中找到")

        server_config = self.mcp_servers[server_name]
        command = server_config.get("command")
        args = server_config.get("args", [])

        logger.info(f"正在连接到MCP服务器: {server_name} ({command} {' '.join(args)})")

        try:
            # 创建 stdio 服务器参数
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=None
            )

            # 使用 stdio_client 连接
            from contextlib import AsyncExitStack
            self._exit_stack = AsyncExitStack()
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self._read, self._write = stdio_transport

            # 创建客户端会话
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(self._read, self._write)
            )

            # 初始化会话
            await self.session.initialize()

            logger.info(f"MCP客户端已连接到 {server_name}")

        except Exception as e:
            logger.error(f"连接MCP服务器失败: {e}", exc_info=True)
            await self.disconnect()
            raise

    async def disconnect(self):
        """断开MCP服务器连接"""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.error(f"关闭MCP连接时出错: {e}")
            finally:
                self._exit_stack = None
                self.session = None
                self._read = None
                self._write = None
                logger.info("MCP客户端已断开连接")

    async def generate_chart(
        self,
        data: Any,  # 可以是 List[Dict] 或 Dict（思维导图等树形结构）
        chart_type: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """生成图表配置

        Args:
            data: 图表数据
                - 大多数图表：列表字典格式 [{"x": ..., "y": ...}, ...]
                - 思维导图/组织架构图：树形对象 {"name": "...", "children": [...]}
            chart_type: 图表类型,支持:
                - bar: 柱状图
                - column: 柱形图
                - line: 折线图
                - area: 面积图
                - pie: 饼图
                - scatter: 散点图
                - radar: 雷达图
                - funnel: 漏斗图
                - boxplot: 箱线图
                - violin: 小提琴图
                - mindmap: 思维导图
                - fishbone: 鱼骨图
                - flow: 流程图
                - organization: 组织架构图
                等等
            title: 图表标题
            description: 图表描述

        Returns:
            dict: AntV G2图表配置

        Raises:
            Exception: MCP服务器请求失败时抛出
        """
        if self.session is None:
            await self.connect()

        # 记录数据类型和长度
        if isinstance(data, list):
            logger.info(f"请求MCP服务器生成图表 - 类型: {chart_type or 'auto'}, 数据点: {len(data)}")
        elif isinstance(data, dict):
            logger.info(f"请求MCP服务器生成图表 - 类型: {chart_type or 'auto'}, 数据: 树形结构")
        else:
            logger.warning(f"请求MCP服务器生成图表 - 类型: {chart_type or 'auto'}, 数据类型未知: {type(data)}")

        try:
            # 列出可用的工具
            tools_response = await self.session.list_tools()
            available_tools = {tool.name: tool for tool in tools_response.tools}
            logger.debug(f"可用的MCP工具: {list(available_tools.keys())}")

            # 映射 chart_type 到 MCP 工具名称
            chart_type_mapping = {
                "bar": "generate_bar_chart",
                "column": "generate_column_chart",
                "line": "generate_line_chart",
                "area": "generate_area_chart",
                "pie": "generate_pie_chart",
                "scatter": "generate_scatter_chart",
                "radar": "generate_radar_chart",
                "funnel": "generate_funnel_chart",
                "boxplot": "generate_boxplot_chart",
                "violin": "generate_violin_chart",
                "histogram": "generate_histogram_chart",
                "treemap": "generate_treemap_chart",
                "sankey": "generate_sankey_chart",
                "network": "generate_network_graph",
                "wordcloud": "generate_word_cloud_chart",
                "venn": "generate_venn_chart",
                "liquid": "generate_liquid_chart",
                "dual_axes": "generate_dual_axes_chart",
                "mindmap": "generate_mind_map",  # 思维导图
                "mind_map": "generate_mind_map",  # 兼容写法
                "fishbone": "generate_fishbone_diagram",  # 鱼骨图
                "flow": "generate_flow_diagram",  # 流程图
                "organization": "generate_organization_chart",  # 组织架构图
            }

            # 确定使用哪个工具
            tool_name = None
            if chart_type:
                tool_name = chart_type_mapping.get(chart_type.lower())

            if not tool_name or tool_name not in available_tools:
                # 如果没有指定或找不到，使用默认的柱状图
                tool_name = "generate_column_chart"
                logger.warning(
                    f"未找到图表类型 '{chart_type}' 对应的工具，使用默认的 {tool_name}"
                )

            logger.info(f"使用MCP工具: {tool_name}")

            # 获取工具的schema以了解需要哪些参数
            tool_info = available_tools[tool_name]

            # 构造调用参数 - 只传递data，不传递chart_type
            tool_arguments = {
                "data": data,
            }

            # 只有在工具支持时才添加 title 和 description
            if title:
                tool_arguments["title"] = title
            if description:
                tool_arguments["description"] = description

            result = await self.session.call_tool(tool_name, tool_arguments)

            # 解析结果
            if result.content:
                # MCP 返回的内容可能是列表，取第一个
                content = result.content[0] if isinstance(result.content, list) else result.content

                # 根据内容类型解析
                chart_config = None
                if hasattr(content, 'text'):
                    text_content = content.text.strip()
                    # 尝试解析为 JSON
                    if text_content:
                        try:
                            chart_config = json.loads(text_content)
                        except json.JSONDecodeError:
                            # 如果不是JSON，可能是纯文本或URL
                            # 将文本内容包装成简单的配置对象
                            chart_config = {
                                "type": chart_type or "unknown",
                                "content": text_content,
                                "url": text_content if text_content.startswith("http") else None,
                            }
                elif isinstance(content, dict):
                    chart_config = content
                else:
                    # 尝试转换为字符串然后解析
                    try:
                        chart_config = json.loads(str(content))
                    except json.JSONDecodeError:
                        chart_config = {
                            "type": chart_type or "unknown",
                            "content": str(content),
                        }

                if chart_config:
                    logger.info(f"MCP图表生成成功 - 类型: {chart_config.get('type', 'unknown')}")
                    return chart_config
                else:
                    raise Exception("无法解析MCP服务器返回的结果")
            else:
                raise Exception("MCP服务器返回空结果")

        except Exception as e:
            logger.error(f"MCP请求异常: {e}", exc_info=True)
            raise

    async def generate_multiple_charts(
        self,
        datasets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """批量生成多个图表

        Args:
            datasets: 图表数据集列表,每个元素包含:
                - data: 图表数据
                - chart_type: 图表类型(可选)
                - title: 标题(可选)
                - description: 描述(可选)

        Returns:
            List[dict]: 图表配置列表

        Raises:
            Exception: MCP服务器请求失败时抛出
        """
        if self.session is None:
            await self.connect()

        logger.info(f"批量请求MCP生成 {len(datasets)} 个图表")

        try:
            tasks = []
            for dataset in datasets:
                task = self._generate_single_chart(dataset)
                tasks.append(task)

            chart_configs = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤失败的图表
            successful_charts = []
            for i, result in enumerate(chart_configs):
                if isinstance(result, Exception):
                    logger.warning(f"图表 {i} 生成失败: {result}")
                else:
                    successful_charts.append(result)

            logger.info(
                f"批量图表生成完成 - "
                f"成功: {len(successful_charts)}/{len(datasets)}"
            )
            return successful_charts

        except Exception as e:
            logger.error(f"批量MCP请求异常: {e}", exc_info=True)
            raise

    async def _generate_single_chart(
        self,
        dataset: Dict[str, Any],
    ) -> Dict[str, Any]:
        """内部方法: 生成单个图表

        Args:
            dataset: 图表数据集

        Returns:
            dict: 图表配置
        """
        return await self.generate_chart(
            data=dataset.get("data", []),
            chart_type=dataset.get("chart_type"),
            title=dataset.get("title"),
            description=dataset.get("description"),
        )

    async def health_check(self) -> bool:
        """检查MCP服务器健康状态

        Returns:
            bool: 服务器是否健康
        """
        try:
            if self.session is None:
                await self.connect()

            # 尝试列出工具来验证连接
            await self.session.list_tools()
            return True
        except Exception as e:
            logger.warning(f"MCP健康检查失败: {e}")
            return False


# 全局客户端实例
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取全局MCP客户端实例

    Returns:
        MCPClient: 客户端实例
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(
            timeout=settings.mcp_server_timeout,
        )
    return _mcp_client
