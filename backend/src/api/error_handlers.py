"""API错误处理中间件

统一处理API异常并返回规范的错误响应
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.config.logging import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误(422)

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSONResponse: 错误响应
    """
    logger.warning(f"请求验证失败 - {request.url}: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors(),
        },
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """处理数据库异常(500)

    Args:
        request: 请求对象
        exc: 数据库异常

    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"数据库错误 - {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "数据库操作失败,请稍后重试",
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """处理通用异常(500)

    Args:
        request: 请求对象
        exc: 异常

    Returns:
        JSONResponse: 错误响应
    """
    logger.error(f"未捕获异常 - {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误,请联系管理员",
        },
    )
