"""Alembic环境配置"""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入所有模型以便Alembic检测
# 这些导入将在模型文件创建后工作
try:
    from src.models.user import User
    from src.models.session import Session
    from src.models.message import Message
    from src.models.chart import Chart
    from src.models.base import Base
except ImportError:
    # 模型尚未创建时的占位符
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()

# Alembic配置对象
config = context.config

# 从环境变量设置数据库URL
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option(
        "sqlalchemy.url",
        os.getenv("DATABASE_URL", "postgresql+psycopg://root:Ct0520.0402@124.221.59.15:5432/brain_dev")
    )

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置target_metadata为所有模型的metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（生成SQL脚本，不连接数据库）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的核心逻辑"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移（连接到数据库）"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
