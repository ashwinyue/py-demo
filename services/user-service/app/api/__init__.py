from flask import Blueprint

# 创建API蓝图
api = Blueprint('api', __name__, url_prefix='/api/v1')

# 导入所有API模块
from . import auth, users, roles, permissions, admin, errors