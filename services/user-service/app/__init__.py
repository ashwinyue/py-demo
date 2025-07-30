from flask import Flask
from flask_cors import CORS
from flask_restx import Api
import logging
from .config import config
from .extensions import db, redis_client, nacos_client
from .main import main as main_blueprint
from .api import api as api_blueprint


def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    
    # 初始化Redis
    redis_client.init_app(app)
    
    # 初始化Nacos
    nacos_client.init_app(app)
    
    # 初始化Swagger API文档
    api_doc = Api(
        app,
        version='1.0',
        title='用户服务 API',
        description='Python MiniBlog 用户服务的 RESTful API 文档',
        doc='/docs/',
        prefix='/api'
    )
    
    # 注册蓝图
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # 配置日志
    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('User service startup')
    
    # 注册服务到Nacos
    def register_service():
        try:
            nacos_client.register_service(
                service_name=app.config['SERVICE_NAME'],
                ip=app.config['SERVICE_HOST'],
                port=app.config['SERVICE_PORT'],
                metadata={
                    'version': app.config.get('SERVICE_VERSION', '1.0.0'),
                    'environment': config_name,
                    'description': 'User service for miniblog'
                }
            )
            app.logger.info('Service registered to Nacos successfully')
        except Exception as e:
            app.logger.error(f'Failed to register service to Nacos: {e}')
    
    # 在应用启动时注册服务
    with app.app_context():
        register_service()
    
    return app