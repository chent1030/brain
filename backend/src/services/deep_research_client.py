"""通义Deep Research客户端

封装通义Deep Research API的异步流式调用
支持流式响应处理和错误重试
"""
import asyncio
from typing import AsyncGenerator, Optional
import dashscope
from dashscope import Generation
from http import HTTPStatus

from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)


class DeepResearchClient:
    """通义Deep Research客户端

    使用DashScope SDK进行AI研究任务的异步流式调用
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-max",
        timeout: int = 30,
        max_tokens: int = 4096,
    ):
        """初始化客户端

        Args:
            api_key: API密钥(未提供则从settings读取)
            model: 模型名称
            timeout: 请求超时(秒)
            max_tokens: 最大token数
        """
        self.api_key = api_key or settings.tongyi_api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens

        # 设置DashScope API密钥
        dashscope.api_key = self.api_key

        if not self.api_key:
            raise ValueError(
                "通义API密钥未配置! 请设置TONGYI_API_KEY环境变量"
            )

    async def stream_chat(
        self,
        query: str,
        session_history: Optional[list[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话接口

        Args:
            query: 用户查询
            session_history: 历史对话记录,格式为[{"role": "user", "content": "..."}, ...]

        Yields:
            str: AI响应文本片段

        Raises:
            Exception: API调用失败时抛出
        """
        # 构建消息列表
        messages = []
        if session_history:
            messages.extend(session_history)
        messages.append({"role": "user", "content": query})

        logger.info(f"开始Deep Research流式请求 - 查询: {query[:50]}...")

        try:
            # 调用DashScope流式API
            responses = Generation.call(
                model=self.model,
                messages=messages,
                result_format='message',  # 获取完整消息格式
                stream=True,  # 启用流式输出
                incremental_output=True,  # 增量输出
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )

            total_content = ""
            for response in responses:
                if response.status_code == HTTPStatus.OK:
                    # 提取增量内容
                    content = response.output.choices[0].message.content
                    if content:
                        total_content += content
                        yield content
                else:
                    error_msg = (
                        f"API请求失败 - "
                        f"状态码: {response.status_code}, "
                        f"错误码: {response.code}, "
                        f"错误信息: {response.message}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)

            logger.info(
                f"Deep Research流式请求完成 - "
                f"总长度: {len(total_content)} 字符"
            )

        except Exception as e:
            logger.error(f"Deep Research请求异常: {e}", exc_info=True)
            raise

    async def generate_response(
        self,
        query: str,
        session_history: Optional[list[dict]] = None,
    ) -> str:
        """非流式对话接口(一次性返回完整响应)

        Args:
            query: 用户查询
            session_history: 历史对话记录

        Returns:
            str: 完整AI响应

        Raises:
            Exception: API调用失败时抛出
        """
        # 构建消息列表
        messages = []
        if session_history:
            messages.extend(session_history)
        messages.append({"role": "user", "content": query})

        logger.info(f"开始Deep Research非流式请求 - 查询: {query[:50]}...")

        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                result_format='message',
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )

            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0].message.content
                logger.info(f"Deep Research请求成功 - 长度: {len(content)} 字符")
                return content
            else:
                error_msg = (
                    f"API请求失败 - "
                    f"状态码: {response.status_code}, "
                    f"错误码: {response.code}, "
                    f"错误信息: {response.message}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Deep Research请求异常: {e}", exc_info=True)
            raise


# 全局客户端实例
_client: Optional[DeepResearchClient] = None


def get_deep_research_client() -> DeepResearchClient:
    """获取全局Deep Research客户端实例

    Returns:
        DeepResearchClient: 客户端实例
    """
    global _client
    if _client is None:
        _client = DeepResearchClient(
            timeout=settings.deep_research_timeout,
            max_tokens=settings.deep_research_max_tokens,
        )
    return _client
