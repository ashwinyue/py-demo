from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.services.redis_service import redis_service
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["健康检查"])

@router.get("/", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """健康检查接口"""
    # 检查数据库连接
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 检查Redis连接
    redis_status = "healthy" if redis_service.health_check() else "unhealthy"
    
    # 整体状态
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        service="user-service",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        database=db_status,
        redis=redis_status
    )

@router.get("/ping")
def ping():
    """简单的ping接口"""
    return {"message": "pong", "timestamp": datetime.utcnow()}