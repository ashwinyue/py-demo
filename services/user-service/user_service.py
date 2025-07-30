#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户中心服务主入口文件
"""

import os
from flask.cli import with_appcontext
from app import create_app, db
from app.models import User, UserSession
from app.extensions import get_redis_client, get_nacos_client

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Flask shell 上下文"""
    return {
        'db': db,
        'User': User,
        'UserSession': UserSession,
        'redis_client': get_redis_client(),
        'nacos_client': get_nacos_client()
    }

@app.cli.command()
@with_appcontext
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成')

@app.cli.command()
@with_appcontext
def create_admin():
    """创建管理员用户"""
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # 检查管理员是否已存在
    admin = User.query.filter_by(username=admin_username).first()
    if admin:
        print(f'管理员用户 {admin_username} 已存在')
        return
    
    # 创建管理员用户
    admin = User(
        username=admin_username,
        email=admin_email,
        is_admin=True,
        is_active=True
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'管理员用户创建成功: {admin_username}')
    print(f'邮箱: {admin_email}')
    print(f'密码: {admin_password}')

@app.cli.command()
@with_appcontext
def test_connections():
    """测试外部服务连接"""
    print('测试数据库连接...')
    try:
        db.session.execute('SELECT 1')
        print('✓ 数据库连接正常')
    except Exception as e:
        print(f'✗ 数据库连接失败: {e}')
    
    print('\n测试Redis连接...')
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            print('✓ Redis连接正常')
        else:
            print('✗ Redis客户端未初始化')
    except Exception as e:
        print(f'✗ Redis连接失败: {e}')
    
    print('\n测试Nacos连接...')
    try:
        nacos_client = get_nacos_client()
        if nacos_client:
            # 尝试获取服务列表
            services = nacos_client.list_naming_instance('user-service')
            print('✓ Nacos连接正常')
        else:
            print('✗ Nacos客户端未初始化')
    except Exception as e:
        print(f'✗ Nacos连接失败: {e}')

if __name__ == '__main__':
    # 开发环境启动
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5001)),
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )