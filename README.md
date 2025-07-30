# Mini Blog API

一个基于Flask的轻量级博客API，采用现代化的Flask应用架构。

## 特性

- 🏗️ **模块化架构**: 使用Flask蓝图和应用工厂模式
- 📊 **数据库支持**: SQLAlchemy ORM，支持SQLite和MySQL
- 🚀 **缓存系统**: Redis缓存提升性能
- 🔧 **配置中心**: Nacos配置管理
- 🐳 **容器化**: Docker和Helm支持
- 📝 **RESTful API**: 完整的用户和文章管理API

## 项目结构

```
py-demo/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用工厂
│   ├── config.py          # 配置文件
│   ├── models.py          # 数据模型
│   ├── extensions.py      # 扩展模块
│   ├── main/              # 主蓝图
│   │   ├── __init__.py
│   │   └── routes.py
│   └── api/               # API蓝图
│       ├── __init__.py
│       ├── errors.py      # 错误处理
│       ├── users.py       # 用户API
│       └── posts.py       # 文章API
├── docker/                # Docker配置
├── helm/                  # Helm图表
├── miniblog.py           # 应用入口
├── run.py                # 开发启动脚本
├── requirements.txt      # 依赖包
├── .env.example         # 环境变量示例
└── README.md            # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，设置你的配置
```

### 3. 初始化数据库

```bash
flask init-db
```

### 4. 启动应用

```bash
# 开发模式
python run.py

# 或者使用Flask命令
flask run

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 miniblog:app
```

## API文档

### 健康检查

- `GET /healthz` - 健康检查

### 用户管理

- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `GET /api/users/{id}` - 获取用户详情
- `PUT /api/users/{id}` - 更新用户
- `DELETE /api/users/{id}` - 删除用户
- `GET /api/users/{id}/posts` - 获取用户文章

### 文章管理

- `GET /api/posts` - 获取文章列表（支持分页）
- `POST /api/posts` - 创建文章
- `GET /api/posts/{id}` - 获取文章详情
- `PUT /api/posts/{id}` - 更新文章
- `DELETE /api/posts/{id}` - 删除文章

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| FLASK_ENV | Flask环境 | development |
| SECRET_KEY | 密钥 | dev-secret-key |
| DATABASE_URL | 数据库URL | sqlite:///miniblog.db |
| REDIS_HOST | Redis主机 | localhost |
| REDIS_PORT | Redis端口 | 6379 |
| NACOS_HOST | Nacos主机 | localhost |
| NACOS_PORT | Nacos端口 | 8848 |

### 数据库配置

支持SQLite和MySQL数据库：

```bash
# SQLite（默认）
DATABASE_URL=sqlite:///miniblog.db

# MySQL
DATABASE_URL=mysql+pymysql://username:password@localhost/miniblog
```

## Docker部署

```bash
# 构建镜像
docker build -f docker/Dockerfile -t miniblog .

# 运行容器
docker run -p 5000:5000 miniblog
```

## Helm部署

```bash
# 安装到Kubernetes
helm install miniblog ./helm/python-miniblog
```

## 开发指南

### 添加新的API端点

1. 在相应的蓝图文件中添加路由函数
2. 更新错误处理（如需要）
3. 添加数据验证
4. 更新缓存逻辑（如需要）

### 数据库迁移

```bash
# 重置数据库
flask reset-db

# 初始化数据库
flask init-db
```

## 技术栈

- **Web框架**: Flask 2.3.3
- **ORM**: SQLAlchemy 3.0.5
- **缓存**: Redis 5.0.1
- **配置中心**: Nacos
- **WSGI服务器**: Gunicorn
- **容器化**: Docker + Kubernetes

## 许可证

MIT License