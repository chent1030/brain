"""健康检查API

提供应用和数据库健康状态检查端点
用于监控和负载均衡器探测
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.config.database import get_db_session, check_database_health
from src.config.settings import settings
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """基础健康检查

    Returns:
        dict: 应用状态信息
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "environment": settings.env,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """就绪检查(包含数据库连接检查)

    用于Kubernetes等容器编排的就绪探测

    Args:
        db: 数据库会话

    Returns:
        dict: 详细健康状态
    """
    checks = {
        "application": "healthy",
        "database": "unknown",
    }

    # 检查数据库连接
    try:
        db_healthy = await check_database_health()
        checks["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        checks["database"] = "unhealthy"

    # 整体状态
    overall_status = "healthy" if all(
        v == "healthy" for v in checks.values()
    ) else "degraded"

    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }

    # 如果有组件不健康,返回503状态码
    status_code = (
        status.HTTP_200_OK
        if overall_status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return response


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """存活检查(轻量级,不检查依赖)

    用于Kubernetes等容器编排的存活探测

    Returns:
        dict: 简单的存活状态
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
