"""会话中间件配置

使用HTTP-only cookies实现会话管理
支持跨域认证和CSRF保护
"""
import os
import secrets
from typing import Optional

from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request


# 会话密钥配置
SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY",
    secrets.token_hex(32)  # 开发环境默认生成随机密钥
)

# 会话配置
SESSION_COOKIE_NAME = "brain_session"
SESSION_MAX_AGE = 30 * 24 * 60 * 60  # 30天(秒)
SESSION_COOKIE_HTTPONLY = True  # 禁止JavaScript访问(防XSS)
SESSION_COOKIE_SECURE = os.getenv("ENV", "development") == "production"  # 生产环境强制HTTPS
SESSION_COOKIE_SAMESITE = "lax"  # CSRF保护: 'strict' | 'lax' | 'none'


def create_session_middleware() -> SessionMiddleware:
    """创建会话中间件实例

    Returns:
        SessionMiddleware: 配置好的会话中间件
    """
    if SESSION_SECRET_KEY == secrets.token_hex(32) and os.getenv("ENV") == "production":
        raise ValueError(
            "生产环境必须设置SESSION_SECRET_KEY环境变量! "
            "生成方法: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    return SessionMiddleware(
        app=None,  # 将在main.py中设置
        secret_key=SESSION_SECRET_KEY,
        session_cookie=SESSION_COOKIE_NAME,
        max_age=SESSION_MAX_AGE,
        https_only=SESSION_COOKIE_SECURE,
        same_site=SESSION_COOKIE_SAMESITE,
    )


# 会话辅助函数
def get_session_user_id(request: Request) -> Optional[int]:
    """从会话中获取用户ID

    Args:
        request: FastAPI/Starlette请求对象

    Returns:
        Optional[int]: 用户ID,未登录返回None
    """
    return request.session.get("user_id")


def set_session_user_id(request: Request, user_id: int) -> None:
    """设置会话用户ID(登录)

    Args:
        request: FastAPI/Starlette请求对象
        user_id: 用户ID
    """
    request.session["user_id"] = user_id


def clear_session(request: Request) -> None:
    """清除会话(登出)

    Args:
        request: FastAPI/Starlette请求对象
    """
    request.session.clear()


# MVP阶段: 自动登录默认用户
DEFAULT_USER_ID = 1  # MVP阶段固定用户ID


async def ensure_default_user_session(request: Request) -> int:
    """确保会话中有默认用户ID(MVP阶段自动登录)

    Args:
        request: FastAPI/Starlette请求对象

    Returns:
        int: 用户ID(MVP阶段固定为1)
    """
    user_id = get_session_user_id(request)
    if user_id is None:
        set_session_user_id(request, DEFAULT_USER_ID)
        user_id = DEFAULT_USER_ID
    return user_id
