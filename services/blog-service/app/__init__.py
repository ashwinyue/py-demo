from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
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
    
    # 注册蓝图
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 初始化扩展服务
    from app.extensions import init_redis, init_nacos, register_service
    init_redis(app)
    init_nacos(app)
    
    # 注册服务到Nacos
    with app.app_context():
        register_service()
    
    return app

# 导入模型（避免循环导入）
from app import models