"""数据库基础模块"""

import logging
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from ..config.base import get_config

logger = logging.getLogger(__name__)

# 创建基础模型类
Base = declarative_base()
metadata = MetaData()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.config = get_config()
        self.database_url = database_url or self.config.get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """设置数据库引擎"""
        engine_kwargs = {
            'echo': self.config.DEBUG,
            'pool_pre_ping': True,
        }
        
        # SQLite特殊配置
        if 'sqlite' in self.database_url:
            engine_kwargs.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False
                }
            })
        
        # MySQL特殊配置
        elif 'mysql' in self.database_url:
            engine_kwargs.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600,
            })
        
        self.engine = create_engine(self.database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"数据库引擎已创建: {self.database_url}")
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除成功")
        except Exception as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """数据库会话上下文管理器"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """数据库健康检查"""
        try:
            with self.session_scope() as session:
                session.execute('SELECT 1')
            return {
                'status': 'healthy',
                'database_url': self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url,
                'engine_pool_size': self.engine.pool.size() if hasattr(self.engine.pool, 'size') else 'N/A'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
            }
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db_session() -> Session:
    """获取数据库会话（依赖注入用）"""
    return db_manager.get_session()


def init_database():
    """初始化数据库"""
    db_manager.create_tables()


def close_database():
    """关闭数据库连接"""
    db_manager.close()