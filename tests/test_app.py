# -*- coding: utf-8 -*-
"""
应用基础测试
"""

import pytest
from app import create_app


@pytest.fixture
def app():
    """创建测试应用实例"""
    # 确保测试环境变量已设置
    import os
    if not os.environ.get('TEST_DATABASE_URL'):
        pytest.skip("TEST_DATABASE_URL environment variable not set")
    
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


def test_app_exists(app):
    """测试应用实例是否存在"""
    assert app is not None


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get('/healthz')
    assert response.status_code == 200


def test_app_is_testing(app):
    """测试应用是否在测试模式"""
    assert app.config['TESTING'] is True


class TestAPI:
    """API测试类"""
    
    def test_api_base_url(self, client):
        """测试API基础URL"""
        response = client.get('/api/')
        # 根据实际API实现调整断言
        assert response.status_code in [200, 404]
    
    def test_users_endpoint(self, client):
        """测试用户端点"""
        response = client.get('/api/users')
        # 根据实际API实现调整断言
        assert response.status_code in [200, 401, 404]
    
    def test_posts_endpoint(self, client):
        """测试文章端点"""
        response = client.get('/api/posts')
        # 根据实际API实现调整断言
        assert response.status_code in [200, 401, 404]