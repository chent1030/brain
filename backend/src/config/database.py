"""数据库连接管理

配置异步SQLAlchemy引擎和会话工厂
支持连接池管理和性能优化
"""
from typing import AsyncGenerator
import os

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from src.models.base import Base
from src.config.settings import settings


# 数据库URL - 从 settings 读取（settings 会自动加载 .env 文件）
DATABASE_URL = settings.database_url


# 创建异步引擎
def create_database_engine(
    url: str = DATABASE_URL,
    echo: bool = False,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_pre_ping: bool = True,
) -> AsyncEngine:
    """创建数据库引擎

    Args:
        url: 数据库连接URL
        echo: 是否打印SQL语句(用于调试)
        pool_size: 连接池基础大小
        max_overflow: 连接池最大溢出连接数
        pool_pre_ping: 连接前ping检查连接有效性

    Returns:
        AsyncEngine: 异步数据库引擎
    """
    # 生产环境推荐配置
    return create_async_engine(
        url,
        echo=echo,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=pool_pre_ping,
        # 连接超时配置
        pool_recycle=3600,  # 1小时后回收连接
        pool_timeout=30,  # 30秒获取连接超时
        # 性能优化
        connect_args={
            "server_settings": {
                "application_name": "brain_backend",
                "jit": "off",  # 禁用JIT编译(小查询优化)
            },
            "command_timeout": 60,  # 60秒命令超时
        },
    )


# 测试环境引擎(无连接池)
def create_test_engine(url: str) -> AsyncEngine:
    """创建测试数据库引擎(无连接池)

    Args:
        url: 测试数据库URL

    Returns:
        AsyncEngine: 测试用异步引擎
    """
    return create_async_engine(
        url,
        echo=True,
        poolclass=NullPool,  # 测试时不使用连接池
    )


# 全局引擎实例
engine: AsyncEngine = create_database_engine(
    echo=os.getenv("DEBUG", "False").lower() == "true"
)


# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
    autoflush=False,  # 手动控制flush时机
    autocommit=False,  # 显式事务控制
)


# 依赖注入函数: 获取数据库会话
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖函数: 获取数据库会话

    使用方式:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            ...

    Yields:
        AsyncSession: 数据库会话
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 数据库初始化工具
async def init_database() -> None:
    """初始化数据库表结构

    警告: 仅用于开发/测试环境
    生产环境使用Alembic迁移
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_database() -> None:
    """删除所有数据库表

    警告: 危险操作,仅用于测试环境
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_database() -> None:
    """关闭数据库连接池

    应用关闭时调用
    """
    await engine.dispose()


# 健康检查
async def check_database_health() -> bool:
    """检查数据库连接健康状态

    Returns:
        bool: 数据库是否健康
    """
    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
            return True
    except Exception:
        return False
