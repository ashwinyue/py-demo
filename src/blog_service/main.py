from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import get_settings
from app.core.database import engine, Base
from app.services.redis_service import init_redis
from app.schemas.common import HealthResponse, ErrorResponse
from app.middleware import setup_middleware
from app.routers import posts

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("正在启动FastAPI博客服务...")
    
    # 初始化数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")
    
    # 初始化Redis
    init_redis()
    
    yield
    
    # 关闭时执行
    logger.info("FastAPI博客服务正在关闭...")

# 创建FastAPI应用
app = FastAPI(
    title="博客服务 API",
    description="基于FastAPI的博客服务，提供文章管理功能",
    version="2.0.0",
    lifespan=lifespan
)

# 设置中间件
setup_middleware(app)

# 注册路由
app.include_router(posts.router)

# 健康检查端点
@app.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        service="blog-service",
        version="2.0.0"
    )

@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "message": "欢迎使用博客服务 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5002,
        reload=True,
        log_level="info"
    )