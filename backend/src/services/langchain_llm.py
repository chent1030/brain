"""通义 LLM LangChain 集成

将通义 API 封装为 LangChain 的 ChatModel
"""
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import dashscope
from dashscope import Generation
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)


class ChatTongyi(BaseChatModel):
    """通义千问聊天模型

    LangChain 集成的通义 API wrapper
    """

    model_name: str = Field(default="qwen-plus", alias="model")
    """模型名称，支持: qwen-turbo, qwen-plus, qwen-max 等"""

    api_key: str = Field(default=settings.tongyi_api_key)
    """通义 API Key"""

    temperature: float = Field(default=0.7)
    """生成温度 (0-1)"""

    max_tokens: int = Field(default=2000)
    """最大生成 token 数"""

    top_p: float = Field(default=0.9)
    """Top-p 采样参数"""

    streaming: bool = Field(default=False)
    """是否使用流式输出"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置 DashScope API Key
        dashscope.api_key = self.api_key

    @property
    def _llm_type(self) -> str:
        """返回 LLM 类型标识"""
        return "tongyi"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回标识此模型的参数"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

    def _convert_messages_to_tongyi_format(
        self, messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """将 LangChain 消息转换为通义 API 格式

        Args:
            messages: LangChain 消息列表

        Returns:
            List[Dict]: 通义 API 消息格式
        """
        tongyi_messages = []

        for message in messages:
            if isinstance(message, SystemMessage):
                tongyi_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                tongyi_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                tongyi_messages.append({"role": "assistant", "content": message.content})
            else:
                # 其他类型当作 user 消息处理
                tongyi_messages.append({"role": "user", "content": message.content})

        return tongyi_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成响应

        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 回调管理器

        Returns:
            ChatResult: 生成结果
        """
        tongyi_messages = self._convert_messages_to_tongyi_format(messages)

        logger.info(f"通义 API 调用 - 模型: {self.model_name}, 消息数: {len(messages)}")

        try:
            response = Generation.call(
                model=self.model_name,
                messages=tongyi_messages,
                result_format="message",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stop=stop,
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                message = AIMessage(content=content)

                generation = ChatGeneration(message=message)
                return ChatResult(generations=[generation])
            else:
                error_msg = f"通义 API 错误: {response.code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"通义 API 调用失败: {e}", exc_info=True)
            raise

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应

        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 异步回调管理器

        Returns:
            ChatResult: 生成结果
        """
        # 通义 SDK 暂不支持原生异步，使用同步方法
        return self._generate(messages, stop, None, **kwargs)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """流式生成响应

        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 回调管理器

        Yields:
            ChatGenerationChunk: 生成的消息块
        """
        tongyi_messages = self._convert_messages_to_tongyi_format(messages)

        logger.info(f"通义 API 流式调用 - 模型: {self.model_name}")

        try:
            responses = Generation.call(
                model=self.model_name,
                messages=tongyi_messages,
                result_format="message",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stop=stop,
                stream=True,
                incremental_output=True,
            )

            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    chunk = ChatGenerationChunk(message=AIMessageChunk(content=content))

                    if run_manager:
                        run_manager.on_llm_new_token(content)

                    yield chunk
                else:
                    error_msg = f"通义 API 流式错误: {response.code} - {response.message}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"通义 API 流式调用失败: {e}", exc_info=True)
            raise

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """异步流式生成响应

        Args:
            messages: 消息列表
            stop: 停止词
            run_manager: 异步回调管理器

        Yields:
            ChatGenerationChunk: 生成的消息块
        """
        # 通义 SDK 暂不支持原生异步流式
        for chunk in self._stream(messages, stop, None, **kwargs):
            yield chunk


def get_tongyi_llm(
    model: str = "qwen-plus",
    temperature: float = 0.7,
    streaming: bool = False,
) -> ChatTongyi:
    """获取通义 LLM 实例

    Args:
        model: 模型名称
        temperature: 生成温度
        streaming: 是否使用流式输出

    Returns:
        ChatTongyi: 通义聊天模型实例
    """
    return ChatTongyi(
        model=model,
        temperature=temperature,
        streaming=streaming,
    )
