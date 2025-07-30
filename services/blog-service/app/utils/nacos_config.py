import json
import logging
from typing import Dict, Any, Optional
from nacos import NacosClient
from flask import current_app


class NacosConfigManager:
    """Nacos配置管理器"""
    
    def __init__(self):
        self.client: Optional[NacosClient] = None
        self.config_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def init_app(self, app):
        """初始化Nacos配置客户端"""
        try:
            self.client = NacosClient(
                server_addresses=app.config['NACOS_SERVER_ADDRESSES'],
                namespace=app.config['NACOS_NAMESPACE'],
                username=app.config.get('NACOS_USERNAME'),
                password=app.config.get('NACOS_PASSWORD')
            )
            
            # 加载配置
            self._load_configs(app)
            
            app.logger.info("Nacos配置管理器初始化成功")
        except Exception as e:
            app.logger.error(f"Nacos配置管理器初始化失败: {e}")
            self.client = None
    
    def _load_configs(self, app):
        """加载配置"""
        if not self.client:
            return
        
        try:
            # 定义需要从Nacos获取的配置项
            config_items = [
                {
                    'data_id': f'{app.config["SERVICE_NAME"]}-config',
                    'group': app.config['NACOS_GROUP_NAME'],
                    'type': 'json'
                },
                {
                    'data_id': 'common-config',
                    'group': app.config['NACOS_GROUP_NAME'],
                    'type': 'json'
                },
                {
                    'data_id': 'database-config',
                    'group': app.config['NACOS_GROUP_NAME'],
                    'type': 'json'
                },
                {
                    'data_id': 'redis-config',
                    'group': app.config['NACOS_GROUP_NAME'],
                    'type': 'json'
                }
            ]
            
            for config_item in config_items:
                self._load_single_config(
                    app,
                    config_item['data_id'],
                    config_item['group'],
                    config_item['type']
                )
                
                # 添加配置监听器
                self._add_config_listener(
                    config_item['data_id'],
                    config_item['group'],
                    app
                )
                
        except Exception as e:
            self.logger.error(f"加载Nacos配置失败: {e}")
    
    def _load_single_config(self, app, data_id: str, group: str, config_type: str = 'json'):
        """加载单个配置"""
        try:
            config_content = self.client.get_config(data_id, group)
            
            if config_content:
                if config_type == 'json':
                    config_data = json.loads(config_content)
                    self.config_cache[data_id] = config_data
                    
                    # 更新Flask配置
                    self._update_app_config(app, config_data)
                    
                    self.logger.info(f"成功加载配置: {data_id}")
                else:
                    self.config_cache[data_id] = config_content
            else:
                self.logger.warning(f"配置不存在: {data_id}")
                
        except Exception as e:
            self.logger.error(f"加载配置失败 {data_id}: {e}")
    
    def _update_app_config(self, app, config_data: Dict[str, Any]):
        """更新Flask应用配置"""
        try:
            # 定义配置映射关系
            config_mapping = {
                # 数据库配置
                'database_url': 'SQLALCHEMY_DATABASE_URI',
                'database_pool_size': 'SQLALCHEMY_ENGINE_OPTIONS',
                
                # Redis配置
                'redis_host': 'REDIS_HOST',
                'redis_port': 'REDIS_PORT',
                'redis_db': 'REDIS_DB',
                'redis_password': 'REDIS_PASSWORD',
                
                # JWT配置
                'jwt_secret_key': 'JWT_SECRET_KEY',
                'jwt_expires_hours': 'JWT_ACCESS_TOKEN_EXPIRES',
                
                # 缓存配置
                'cache_default_timeout': 'CACHE_DEFAULT_TIMEOUT',
                'cache_posts_timeout': 'CACHE_POSTS_TIMEOUT',
                
                # 分页配置
                'posts_per_page': 'POSTS_PER_PAGE',
                'max_posts_per_page': 'MAX_POSTS_PER_PAGE',
                
                # 用户服务配置
                'user_service_timeout': 'USER_SERVICE_TIMEOUT',
                
                # 日志配置
                'log_level': 'LOG_LEVEL',
                'log_file': 'LOG_FILE',
                
                # CORS配置
                'cors_origins': 'CORS_ORIGINS'
            }
            
            # 更新配置
            for nacos_key, flask_key in config_mapping.items():
                if nacos_key in config_data:
                    value = config_data[nacos_key]
                    
                    # 特殊处理某些配置
                    if flask_key == 'SQLALCHEMY_ENGINE_OPTIONS' and isinstance(value, dict):
                        # 合并数据库引擎选项
                        current_options = app.config.get(flask_key, {})
                        current_options.update(value)
                        app.config[flask_key] = current_options
                    elif flask_key == 'JWT_ACCESS_TOKEN_EXPIRES':
                        # JWT过期时间转换
                        from datetime import timedelta
                        app.config[flask_key] = timedelta(hours=int(value))
                    elif flask_key == 'CORS_ORIGINS':
                        # CORS配置处理
                        if isinstance(value, str):
                            app.config[flask_key] = value.split(',')
                        else:
                            app.config[flask_key] = value
                    else:
                        app.config[flask_key] = value
                    
                    self.logger.debug(f"更新配置: {flask_key} = {value}")
            
        except Exception as e:
            self.logger.error(f"更新应用配置失败: {e}")
    
    def _add_config_listener(self, data_id: str, group: str, app):
        """添加配置监听器"""
        if not self.client:
            return
        
        def config_callback(args):
            """配置变更回调函数"""
            try:
                self.logger.info(f"配置变更通知: {data_id}")
                
                # 重新加载配置
                with app.app_context():
                    self._load_single_config(app, data_id, group)
                    
            except Exception as e:
                self.logger.error(f"处理配置变更失败: {e}")
        
        try:
            self.client.add_config_watcher(data_id, group, config_callback)
            self.logger.info(f"添加配置监听器: {data_id}")
        except Exception as e:
            self.logger.error(f"添加配置监听器失败 {data_id}: {e}")
    
    def get_config(self, data_id: str, group: str = None) -> Optional[Any]:
        """获取配置"""
        if not self.client:
            return None
        
        try:
            if group is None:
                group = current_app.config['NACOS_GROUP_NAME']
            
            # 先从缓存获取
            if data_id in self.config_cache:
                return self.config_cache[data_id]
            
            # 从Nacos获取
            config_content = self.client.get_config(data_id, group)
            if config_content:
                try:
                    config_data = json.loads(config_content)
                    self.config_cache[data_id] = config_data
                    return config_data
                except json.JSONDecodeError:
                    return config_content
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取配置失败 {data_id}: {e}")
            return None
    
    def publish_config(self, data_id: str, content: str, group: str = None) -> bool:
        """发布配置"""
        if not self.client:
            return False
        
        try:
            if group is None:
                group = current_app.config['NACOS_GROUP_NAME']
            
            result = self.client.publish_config(data_id, group, content)
            
            if result:
                self.logger.info(f"发布配置成功: {data_id}")
                # 清除缓存
                if data_id in self.config_cache:
                    del self.config_cache[data_id]
            else:
                self.logger.error(f"发布配置失败: {data_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"发布配置异常 {data_id}: {e}")
            return False
    
    def remove_config(self, data_id: str, group: str = None) -> bool:
        """删除配置"""
        if not self.client:
            return False
        
        try:
            if group is None:
                group = current_app.config['NACOS_GROUP_NAME']
            
            result = self.client.remove_config(data_id, group)
            
            if result:
                self.logger.info(f"删除配置成功: {data_id}")
                # 清除缓存
                if data_id in self.config_cache:
                    del self.config_cache[data_id]
            else:
                self.logger.error(f"删除配置失败: {data_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"删除配置异常 {data_id}: {e}")
            return False


# 全局实例
nacos_config_manager = NacosConfigManager()


def get_nacos_config_manager():
    """获取Nacos配置管理器实例"""
    return nacos_config_manager