from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.health import router as health_router
from app.services.redis_service import redis_service

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    logger.info("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 测试Redis连接
    if redis_service.health_check():
        logger.info("Redis连接成功")
    else:
        logger.warning("Redis连接失败")
    
    logger.info("用户服务启动完成")
    yield
    
    # 关闭时清理资源
    logger.info("用户服务关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="用户管理服务API",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )

# 注册路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "用户服务API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )