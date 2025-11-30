"""FastAPI主应用

初始化FastAPI应用,配置中间件、路由和生命周期事件
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from src.config.settings import settings
from src.config.logging import auto_setup_logging, get_logger
from src.config.session import SESSION_SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from src.config.database import close_database, DATABASE_URL, engine
from src.api.error_handlers import (
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
)

# 初始化日志
auto_setup_logging()
logger = get_logger(__name__)


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    启动时执行初始化,关闭时清理资源
    """
    # 启动时
    logger.info(f"启动 {settings.app_name}")
    logger.info(f"环境: {settings.env}")
    logger.info(f"调试模式: {settings.debug}")

    # 打印数据库配置
    logger.info(f"数据库URL: {DATABASE_URL}")

    # 验证生产环境配置
    if settings.is_production:
        try:
            settings.validate_production_config()
            logger.info("生产环境配置验证通过")
        except ValueError as e:
            logger.error(f"生产环境配置验证失败: {e}")
            raise

    # 测试数据库连接
    logger.info("正在测试数据库连接...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ 数据库连接成功!")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {type(e).__name__}: {e}")
        logger.error(f"数据库URL: {DATABASE_URL}")
        logger.error("请检查:")
        logger.error("  1. 数据库服务器是否运行")
        logger.error("  2. 数据库URL是否正确")
        logger.error("  3. 网络连接是否正常")
        logger.error("  4. 防火墙是否阻止连接")
        raise RuntimeError(f"数据库连接失败: {e}") from e

    yield

    # 关闭时
    logger.info("关闭应用...")
    await close_database()
    logger.info("数据库连接已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="基于通义Deep Research和MCP图表服务的AI对话系统",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)


# 配置CORS中间件
# 注意：当 allow_credentials=True 时，allow_origins 不能是 ["*"]
# 必须指定具体的源列表
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从配置读取允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
    https_only=settings.is_production,
    same_site="lax",
)


# 注册路由
from src.api.health import router as health_router
from src.api.sessions import router as sessions_router
from src.api.messages import router as messages_router
from src.api.stream import router as stream_router

app.include_router(health_router, prefix="/api", tags=["健康检查"])
app.include_router(sessions_router, prefix="/api", tags=["会话管理"])
app.include_router(messages_router, prefix="/api", tags=["消息管理"])
app.include_router(stream_router, prefix="/api", tags=["SSE流式传输"])


# 注册错误处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# 根路径
@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.env,
    }


# 应用启动入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
