"""LangChain Agent 服务

使用通义 API 的 function calling 功能构建智能对话 agent
动态加载所有MCP工具，让LLM自己选择使用哪个
"""
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import dashscope
from dashscope import Generation

from src.services.mcp_client import get_mcp_client
from src.services.deep_research_client import get_deep_research_client
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

# 设置 API Key
dashscope.api_key = settings.tongyi_api_key


# 系统提示词
SYSTEM_PROMPT = """你是一个智能 AI 助手，能够回答问题、进行深度研究并生成数据可视化图表。

你的能力：
1. 回答各种问题，提供有用的信息和建议
2. 对于复杂问题，可以使用 deep_research 工具进行深度分析和多步推理
3. 可以生成各种数据可视化图表（折线图、柱状图、饼图、思维导图、组织架构图等25+种图表）

工具使用指南：

**deep_research 工具**：
- 适用场景：复杂问题分析、市场调研、技术调查、学术研究等需要深入思考的任务
- 何时使用：当问题需要多角度分析、搜索最新信息或多步推理时

**图表生成工具**：
- 你有25+种图表工具可用，根据用户需求选择合适的工具
- 思维导图：使用 generate_mind_map
- 组织架构图：使用 generate_organization_chart
- 流程图：使用 generate_flow_diagram
- 鱼骨图：使用 generate_fishbone_diagram
- 柱状图：使用 generate_column_chart 或 generate_bar_chart
- 折线图：使用 generate_line_chart
- 饼图：使用 generate_pie_chart
- 等等...

**特别注意**：
- 当用户说"生成思维导图"、"画思维导图"时，使用 generate_mind_map 工具
- 根据工具的描述和参数要求，构造正确的数据格式
- 思维导图等层次结构图表需要树形数据：{"name": "主题", "children": [...]}
- 普通图表需要数组数据：[{"x": ..., "y": ...}, ...]
- 当图表工具返回成功后，告诉用户图表已生成并简要说明内容

现在开始对话吧！
"""


async def load_mcp_tools() -> List[Dict[str, Any]]:
    """从MCP服务器动态加载所有工具定义

    Returns:
        List[Dict]: 通义API格式的工具列表
    """
    mcp_client = get_mcp_client()
    await mcp_client.connect()

    try:
        # 获取MCP工具列表
        tools_response = await mcp_client.session.list_tools()

        tongyi_tools = []
        for tool in tools_response.tools:
            # 将MCP工具定义转换为通义API格式
            tongyi_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema  # MCP的inputSchema已经是JSON Schema格式
                }
            }
            tongyi_tools.append(tongyi_tool)

        logger.info(f"已加载 {len(tongyi_tools)} 个MCP工具: {[t['function']['name'] for t in tongyi_tools]}")
        return tongyi_tools

    finally:
        await mcp_client.disconnect()


async def load_deep_research_tool() -> Dict[str, Any]:
    """加载Deep Research工具定义

    Returns:
        Dict: 通义API格式的工具定义
    """
    return {
        "type": "function",
        "function": {
            "name": "deep_research",
            "description": (
                "深度研究工具。用于分析复杂问题、进行多步推理和综合研究。"
                "当用户的问题需要深入分析、多角度思考或需要搜索最新信息时使用此工具。"
                "例如：市场分析、技术调研、学术问题等。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要深度研究的问题或主题"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大生成token数",
                        "default": 4096
                    }
                },
                "required": ["query"]
            }
        }
    }


class LangChainAgentService:
    """LangChain Agent 服务类

    动态加载MCP工具，使用通义 API 的 function calling
    """

    def __init__(
        self,
        model_name: str = "qwen-plus",
        temperature: float = 0.7,
        streaming: bool = True,
    ):
        """初始化 Agent 服务

        Args:
            model_name: 通义模型名称
            temperature: 生成温度
            streaming: 是否使用流式输出
        """
        self.model_name = model_name
        self.temperature = temperature
        self.streaming = streaming
        self.tongyi_tools = None  # 延迟加载

        # 用于记录本次对话生成的图表（在保存消息时使用）
        self.generated_charts: List[Dict[str, Any]] = []

        logger.info(f"LangChain Agent 初始化 - 模型: {model_name}")

    async def _ensure_tools_loaded(self):
        """确保工具已加载"""
        if self.tongyi_tools is None:
            logger.info("正在加载工具...")

            # 加载MCP工具
            mcp_tools = await load_mcp_tools()

            # 加载Deep Research工具
            deep_research_tool = await load_deep_research_tool()

            # 合并所有工具
            self.tongyi_tools = mcp_tools + [deep_research_tool]

            logger.info(f"工具加载完成 - 总数: {len(self.tongyi_tools)}")

    async def chat_stream(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式聊天接口（支持工具调用）

        Args:
            message: 用户消息
            chat_history: 对话历史（通义格式）
            session_id: 会话 ID

        Yields:
            str: AI 回复的文本块
        """
        logger.info(
            f"处理流式聊天 - Session: {session_id}, "
            f"消息: {message[:100]}..., "
            f"历史消息数: {len(chat_history) if chat_history else 0}"
        )

        try:
            # 确保工具已加载
            await self._ensure_tools_loaded()

            # 清空之前的图表记录
            self.generated_charts = []

            # 构建消息列表
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            if chat_history:
                messages.extend(chat_history)

            messages.append({"role": "user", "content": message})

            # 工具调用循环（最多5轮）
            max_iterations = 5
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Agent迭代 {iteration}/{max_iterations}")

                # 调用通义 API（带工具定义）
                response = Generation.call(
                    model=self.model_name,
                    messages=messages,
                    result_format="message",
                    temperature=self.temperature,
                    tools=self.tongyi_tools,
                )

                if response.status_code != 200:
                    error_msg = f"通义 API 错误: {response.code} - {response.message}"
                    logger.error(error_msg)
                    yield f"\n\n❌ API调用失败: {error_msg}"
                    break

                assistant_message = response.output.choices[0].message

                # 检查是否有工具调用（通义SDK的对象需要用 hasattr + try-except）
                tool_calls = []
                try:
                    if hasattr(assistant_message, 'tool_calls'):
                        tool_calls = assistant_message.tool_calls or []
                except (KeyError, AttributeError):
                    # 没有tool_calls属性
                    tool_calls = []

                if not tool_calls:
                    # 没有工具调用，返回最终回复
                    logger.info("LLM 生成最终回复（无工具调用）")
                    content = assistant_message.content

                    if content:
                        yield content

                    break

                # 有工具调用
                logger.info(f"检测到 {len(tool_calls)} 个工具调用")

                # 将assistant消息添加到历史
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": tool_calls
                })

                # 执行工具
                for tool_call in tool_calls:
                    # 通义API返回的tool_call可能是字典格式
                    if isinstance(tool_call, dict):
                        function_name = tool_call["function"]["name"]
                        function_args_str = tool_call["function"]["arguments"]
                    else:
                        # 对象格式
                        function_name = tool_call.function.name
                        function_args_str = tool_call.function.arguments

                    logger.info(f"执行工具: {function_name}")
                    logger.debug(f"参数字符串 (前500字符): {function_args_str[:500]}...")
                    logger.debug(f"参数字符串 (后200字符): ...{function_args_str[-200:]}")
                    logger.debug(f"参数字符串长度: {len(function_args_str)}")

                    try:
                        function_args = json.loads(function_args_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {e}")
                        logger.error(f"错误位置: {e.pos}, 错误行列: line {e.lineno} column {e.colno}")
                        logger.error(f"错误位置附近的内容: ...{function_args_str[max(0, e.pos-100):min(len(function_args_str), e.pos+100)]}...")

                        # 保存完整内容到文件用于调试
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            f.write(function_args_str)
                            logger.error(f"完整参数已保存到: {f.name}")

                        # 尝试修复：截取到第一个完整的JSON对象
                        try:
                            # 尝试只解析到错误位置之前的有效JSON
                            decoder = json.JSONDecoder()
                            function_args, idx = decoder.raw_decode(function_args_str)
                            logger.warning(f"JSON修复成功 - 截取到位置 {idx}，剩余内容被丢弃")
                        except Exception as fix_error:
                            logger.error(f"JSON修复失败: {fix_error}")
                            # 如果还是失败，返回错误
                            tool_result = f"工具调用失败: 参数格式错误 - {str(e)}\n\n请使用正确的JSON格式。"
                            messages.append({
                                "role": "tool",
                                "content": tool_result,
                                "name": function_name
                            })
                            continue

                    logger.info(f"解析后的参数: {json.dumps(function_args, ensure_ascii=False)[:200]}...")

                    # 向用户显示工具调用信息
                    if function_name == "deep_research":
                        yield f"\n\n🔧 **正在调用工具**: `{function_name}`\n"
                        yield f"📊 **分析问题**: {function_args.get('query', '')[:100]}...\n\n"
                    elif function_name.startswith("generate_"):
                        # 图表工具
                        chart_type = function_name.replace("generate_", "").replace("_", " ")
                        yield f"\n\n🔧 **正在调用工具**: `{function_name}`\n"
                        yield f"📈 **生成图表**: {chart_type}\n\n"
                    else:
                        yield f"\n\n🔧 **正在调用工具**: `{function_name}`\n\n"

                    try:
                        # 执行工具
                        if function_name == "deep_research":
                            # Deep Research工具
                            tool_result = await self._execute_deep_research(**function_args)
                        elif function_name.startswith("generate_"):
                            # MCP图表工具
                            tool_result, chart_info = await self._execute_mcp_tool(function_name, function_args)

                            # 记录图表信息，后续保存消息时使用
                            if chart_info:
                                self.generated_charts.append(chart_info)
                                logger.info(f"记录图表信息: {chart_info['chart_type']}")
                        else:
                            tool_result = f"错误: 未知工具 {function_name}"
                            logger.error(tool_result)

                        logger.info(f"工具 {function_name} 执行成功，结果长度: {len(str(tool_result))}")

                    except Exception as e:
                        tool_result = f"工具执行失败: {str(e)}"
                        logger.error(f"工具 {function_name} 执行失败: {e}", exc_info=True)

                    # 添加工具结果到消息历史
                    messages.append({
                        "role": "tool",
                        "content": str(tool_result),
                        "name": function_name
                    })

                # 继续循环，让LLM根据工具结果生成回复

            if iteration >= max_iterations:
                logger.warning(f"达到最大迭代次数 {max_iterations}")
                yield "\n\n⚠️ 已达到最大工具调用次数。"

        except Exception as e:
            logger.error(f"流式聊天处理失败: {e}", exc_info=True)
            yield f"\n\n❌ 抱歉，处理您的消息时出现了错误: {str(e)}"

    async def _execute_deep_research(self, query: str, max_tokens: int = 4096) -> str:
        """执行Deep Research工具

        Args:
            query: 研究问题
            max_tokens: 最大token数

        Returns:
            str: 研究结果
        """
        client = get_deep_research_client()
        full_response = ""
        async for chunk in client.stream_chat(query=query, session_history=[]):
            full_response += chunk
        return full_response

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """执行MCP工具

        Args:
            tool_name: MCP工具名称
            arguments: 工具参数

        Returns:
            tuple: (给LLM的简单文本, 图表信息dict或None)
        """
        mcp_client = get_mcp_client()
        await mcp_client.connect()

        try:
            # 直接调用MCP工具
            result = await mcp_client.session.call_tool(tool_name, arguments)

            # 提取结果
            chart_url = None
            if hasattr(result, 'content'):
                # 提取content
                content_items = result.content
                if content_items and len(content_items) > 0:
                    chart_url = content_items[0].text

            if not chart_url:
                return "图表生成失败：工具返回空结果", None

            # 构造图表信息（用于后续保存）
            chart_info = {
                "type": "image",
                "url": chart_url,
                "tool": tool_name,
                "chart_type": tool_name.replace("generate_", "").replace("_", "-")
            }

            # 返回给LLM的只是简单确认信息
            return f"图表已成功生成！图表类型：{chart_info['chart_type']}", chart_info

        finally:
            await mcp_client.disconnect()

    def get_generated_charts(self) -> List[Dict[str, Any]]:
        """获取本次对话生成的所有图表信息

        供外部调用，在保存消息后获取图表信息
        """
        return self.generated_charts


# 全局 agent 实例
_agent_service: Optional[LangChainAgentService] = None


def get_agent_service(
    model_name: str = "qwen-plus",
    temperature: float = 0.7,
    streaming: bool = True,
) -> LangChainAgentService:
    """获取全局 Agent 服务实例

    Args:
        model_name: 模型名称
        temperature: 生成温度
        streaming: 是否流式输出

    Returns:
        LangChainAgentService: Agent 服务实例
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = LangChainAgentService(
            model_name=model_name,
            temperature=temperature,
            streaming=streaming,
        )
    return _agent_service
