from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restx import Api
from app.config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # 初始化 Swagger API 文档
    api = Api(app, 
              title='Blog Service API',
              version='1.0',
              description='博客服务 API 文档',
              doc='/docs/')
    
    # 将 API 实例存储到应用上下文中
    app.api = api
    
    # 注册蓝图
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 初始化扩展服务
    from app.extensions import init_redis
    init_redis(app)
    
    return app

# 导入模型（避免循环导入）
from app import models