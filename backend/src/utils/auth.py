"""认证工具函数

提供会话验证、用户获取等认证相关功能
支持FastAPI依赖注入
"""
from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db_session
from src.config.session import get_session_user_id, ensure_default_user_session, DEFAULT_USER_ID
from src.models.user import User


# 异常定义
class AuthenticationError(HTTPException):
    """认证失败异常"""
    def __init__(self, detail: str = "未认证或会话已过期"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Session"},
        )


class AuthorizationError(HTTPException):
    """授权失败异常"""
    def __init__(self, detail: str = "无权访问此资源"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# FastAPI依赖: 获取当前用户ID(可选)
async def get_current_user_id_optional(request: Request) -> Optional[int]:
    """获取当前登录用户ID(可选,未登录返回None)

    使用方式:
        @app.get("/endpoint")
        async def endpoint(user_id: Optional[int] = Depends(get_current_user_id_optional)):
            if user_id is None:
                # 未登录逻辑
            else:
                # 已登录逻辑

    Args:
        request: FastAPI请求对象

    Returns:
        Optional[int]: 用户ID或None
    """
    return get_session_user_id(request)


# FastAPI依赖: 获取当前用户ID(必需,未登录抛出异常)
async def get_current_user_id(request: Request) -> int:
    """获取当前登录用户ID(必需,未登录抛出401)

    使用方式:
        @app.get("/endpoint")
        async def endpoint(user_id: int = Depends(get_current_user_id)):
            # user_id保证非空

    Args:
        request: FastAPI请求对象

    Returns:
        int: 用户ID

    Raises:
        AuthenticationError: 未登录时抛出401
    """
    user_id = get_session_user_id(request)
    if user_id is None:
        raise AuthenticationError()
    return user_id


# FastAPI依赖: 获取当前用户对象
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """获取当前登录用户对象(必需,未登录或用户不存在抛出异常)

    使用方式:
        @app.get("/endpoint")
        async def endpoint(user: User = Depends(get_current_user)):
            print(user.username)

    Args:
        request: FastAPI请求对象
        db: 数据库会话

    Returns:
        User: 用户对象

    Raises:
        AuthenticationError: 未登录或用户不存在时抛出401
    """
    user_id = await get_current_user_id(request)

    # 从数据库查询用户
    user = await db.get(User, user_id)
    if user is None:
        raise AuthenticationError(detail="用户不存在或已被删除")

    return user


# MVP阶段: 自动获取默认用户ID
async def get_default_user_id(request: Request) -> int:
    """MVP阶段: 自动获取默认用户ID(自动登录)

    使用方式:
        @app.get("/endpoint")
        async def endpoint(user_id: int = Depends(get_default_user_id)):
            # MVP阶段user_id固定为1

    Args:
        request: FastAPI请求对象

    Returns:
        int: 默认用户ID(固定为1)
    """
    return await ensure_default_user_session(request)


# MVP阶段: 自动获取默认用户对象
async def get_default_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """MVP阶段: 自动获取默认用户对象

    使用方式:
        @app.get("/endpoint")
        async def endpoint(user: User = Depends(get_default_user)):
            # MVP阶段user固定为default_user

    Args:
        request: FastAPI请求对象
        db: 数据库会话

    Returns:
        User: 默认用户对象

    Raises:
        AuthenticationError: 默认用户不存在时抛出500(数据库问题)
    """
    user_id = await get_default_user_id(request)

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"默认用户(id={DEFAULT_USER_ID})不存在,请检查数据库初始化"
        )

    return user


# 权限验证函数
def verify_user_owns_resource(user_id: int, resource_user_id: int) -> None:
    """验证用户是否拥有资源(用户ID匹配)

    Args:
        user_id: 当前用户ID
        resource_user_id: 资源所属用户ID

    Raises:
        AuthorizationError: 用户ID不匹配时抛出403
    """
    if user_id != resource_user_id:
        raise AuthorizationError(detail="您无权访问他人的资源")
