#!/usr/bin/env python3
"""Mini Blog应用入口文件"""

import os
from app import create_app, db
from app.config import config
from app.models import User, Post

# 根据环境变量选择配置
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

@app.shell_context_processor
def make_shell_context():
    """Flask shell上下文"""
    return {
        'db': db,
        'User': User,
        'Post': Post
    }

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成')

@app.cli.command()
def reset_db():
    """重置数据库"""
    db.drop_all()
    db.create_all()
    print('数据库重置完成')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)