#!/usr/bin/env python3
"""
Nacos配置管理功能测试
"""

import unittest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'services', 'user-service'))
sys.path.insert(0, os.path.join(project_root, 'services', 'blog-service'))


class TestNacosConfigManager(unittest.TestCase):
    """Nacos配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟Flask应用
        self.mock_app = Mock()
        self.mock_app.config = {
            'NACOS_SERVER_ADDRESSES': 'localhost:8848',
            'NACOS_NAMESPACE': 'public',
            'NACOS_GROUP_NAME': 'DEFAULT_GROUP',
            'SERVICE_NAME': 'test-service',
            'NACOS_USERNAME': None,
            'NACOS_PASSWORD': None
        }
        self.mock_app.logger = Mock()
        
        # 模拟Nacos客户端
        self.mock_nacos_client = Mock()
    
    @patch('services.user_service.app.utils.nacos_config.NacosClient')
    def test_init_app_success(self, mock_nacos_client_class):
        """测试配置管理器初始化成功"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 设置模拟
        mock_nacos_client_class.return_value = self.mock_nacos_client
        self.mock_nacos_client.get_config.return_value = '{}'
        
        # 创建配置管理器并初始化
        config_manager = NacosConfigManager()
        config_manager.init_app(self.mock_app)
        
        # 验证
        self.assertIsNotNone(config_manager.client)
        mock_nacos_client_class.assert_called_once()
        self.mock_app.logger.info.assert_called()
    
    @patch('services.user_service.app.utils.nacos_config.NacosClient')
    def test_init_app_failure(self, mock_nacos_client_class):
        """测试配置管理器初始化失败"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 设置模拟异常
        mock_nacos_client_class.side_effect = Exception("连接失败")
        
        # 创建配置管理器并初始化
        config_manager = NacosConfigManager()
        config_manager.init_app(self.mock_app)
        
        # 验证
        self.assertIsNone(config_manager.client)
        self.mock_app.logger.error.assert_called()
    
    def test_get_config_success(self):
        """测试获取配置成功"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        test_config = {'key': 'value', 'number': 123}
        self.mock_nacos_client.get_config.return_value = json.dumps(test_config)
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.get_config('test-config')
        
        # 验证
        self.assertEqual(result, test_config)
        self.mock_nacos_client.get_config.assert_called_once_with('test-config', 'DEFAULT_GROUP')
    
    def test_get_config_not_found(self):
        """测试获取不存在的配置"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        self.mock_nacos_client.get_config.return_value = None
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.get_config('non-existent-config')
        
        # 验证
        self.assertIsNone(result)
    
    def test_publish_config_success(self):
        """测试发布配置成功"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        self.mock_nacos_client.publish_config.return_value = True
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.publish_config('test-config', '{"key": "value"}')
        
        # 验证
        self.assertTrue(result)
        self.mock_nacos_client.publish_config.assert_called_once_with(
            'test-config', 'DEFAULT_GROUP', '{"key": "value"}'
        )
    
    def test_publish_config_failure(self):
        """测试发布配置失败"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        self.mock_nacos_client.publish_config.return_value = False
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.publish_config('test-config', '{"key": "value"}')
        
        # 验证
        self.assertFalse(result)
    
    def test_remove_config_success(self):
        """测试删除配置成功"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        self.mock_nacos_client.remove_config.return_value = True
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.remove_config('test-config')
        
        # 验证
        self.assertTrue(result)
        self.mock_nacos_client.remove_config.assert_called_once_with(
            'test-config', 'DEFAULT_GROUP'
        )
    
    def test_config_cache(self):
        """测试配置缓存功能"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        config_manager.client = self.mock_nacos_client
        
        # 设置模拟返回值
        test_config = {'cached': True}
        config_manager.config_cache['test-config'] = test_config
        
        # 模拟Flask应用上下文
        with patch('services.user_service.app.utils.nacos_config.current_app', self.mock_app):
            result = config_manager.get_config('test-config')
        
        # 验证缓存被使用，没有调用Nacos客户端
        self.assertEqual(result, test_config)
        self.mock_nacos_client.get_config.assert_not_called()
    
    def test_update_app_config(self):
        """测试更新应用配置"""
        from services.user_service.app.utils.nacos_config import NacosConfigManager
        
        # 创建配置管理器
        config_manager = NacosConfigManager()
        
        # 测试配置数据
        config_data = {
            'redis_host': 'new-redis-host',
            'redis_port': 6380,
            'jwt_expires_hours': 48,
            'cors_origins': 'http://localhost:3000,http://localhost:8080'
        }
        
        # 更新配置
        config_manager._update_app_config(self.mock_app, config_data)
        
        # 验证配置更新
        self.assertEqual(self.mock_app.config['REDIS_HOST'], 'new-redis-host')
        self.assertEqual(self.mock_app.config['REDIS_PORT'], 6380)
        self.assertEqual(self.mock_app.config['CORS_ORIGINS'], 
                        ['http://localhost:3000', 'http://localhost:8080'])


class TestNacosConfigScript(unittest.TestCase):
    """Nacos配置管理脚本测试"""
    
    @patch('scripts.manage_nacos_config.NacosClient')
    def test_get_nacos_client_success(self, mock_nacos_client_class):
        """测试获取Nacos客户端成功"""
        # 设置环境变量
        with patch.dict(os.environ, {
            'NACOS_HOST': 'test-host',
            'NACOS_PORT': '8848',
            'NACOS_NAMESPACE': 'test'
        }):
            from scripts.manage_nacos_config import get_nacos_client
            
            # 设置模拟
            mock_client = Mock()
            mock_nacos_client_class.return_value = mock_client
            
            # 调用函数
            result = get_nacos_client()
            
            # 验证
            self.assertEqual(result, mock_client)
            mock_nacos_client_class.assert_called_once_with(
                server_addresses='test-host:8848',
                namespace='test',
                username=None,
                password=None
            )
    
    @patch('scripts.manage_nacos_config.NacosClient')
    def test_get_nacos_client_failure(self, mock_nacos_client_class):
        """测试获取Nacos客户端失败"""
        # 设置模拟异常
        mock_nacos_client_class.side_effect = Exception("连接失败")
        
        from scripts.manage_nacos_config import get_nacos_client
        
        # 调用函数
        with patch('builtins.print') as mock_print:
            result = get_nacos_client()
        
        # 验证
        self.assertIsNone(result)
        mock_print.assert_called()
    
    def test_load_example_configs(self):
        """测试加载示例配置"""
        from scripts.manage_nacos_config import load_example_configs
        
        # 模拟配置文件存在
        test_config = {
            'common-config': {
                'description': '测试配置',
                'config': {'key': 'value'}
            }
        }
        
        with patch('builtins.open', unittest.mock.mock_open(
            read_data=json.dumps(test_config)
        )):
            result = load_example_configs()
        
        # 验证
        self.assertEqual(result, test_config)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)