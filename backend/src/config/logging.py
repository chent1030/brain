"""日志配置

统一的日志格式和级别配置
支持控制台和文件输出
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config.settings import settings


# 日志格式
LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - "
    "[%(filename)s:%(lineno)d] - %(message)s"
)
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 简化格式(控制台)
CONSOLE_FORMAT = "%(levelname)-8s [%(name)s] %(message)s"


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> None:
    """配置应用日志系统

    Args:
        level: 日志级别(DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径(可选)
        console_output: 是否输出到控制台
    """
    # 使用配置的日志级别
    log_level = level or settings.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 清除现有handlers
    root_logger.handlers.clear()

    # 控制台handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # 开发环境使用简化格式,生产环境使用完整格式
        if settings.is_development:
            console_formatter = logging.Formatter(CONSOLE_FORMAT)
        else:
            console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # 文件handler(可选)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)

        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    # 首次启动日志
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已初始化 - 级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_file}")


# 获取模块日志器的便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取命名日志器

    使用方式:
        logger = get_logger(__name__)
        logger.info("日志消息")

    Args:
        name: 日志器名称(通常使用__name__)

    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


# 自动初始化日志(可通过环境变量配置)
def auto_setup_logging() -> None:
    """自动配置日志系统(应用启动时调用)"""
    log_file_path = None

    # 生产环境启用文件日志
    if settings.is_production:
        log_dir = Path("logs")
        log_file_path = log_dir / "brain.log"

    setup_logging(
        level=settings.log_level,
        log_file=log_file_path,
        console_output=True,
    )


# 日志装饰器
def log_execution(logger: logging.Logger):
    """装饰器: 记录函数执行日志

    使用方式:
        @log_execution(logger)
        async def my_function():
            ...

    Args:
        logger: 日志器实例
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger.debug(f"执行函数: {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
                raise

        def sync_wrapper(*args, **kwargs):
            logger.debug(f"执行函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
                raise

        # 根据函数类型选择wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
