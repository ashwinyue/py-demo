# 博客服务 (Blog Service)

基于FastAPI的现代博客服务，提供高性能的文章管理API。

## 特性

- 🚀 **FastAPI框架**: 现代、快速的Web框架，自动生成API文档
- 🔒 **类型安全**: 使用Pydantic模型进行数据验证和序列化
- 📊 **数据库支持**: SQLAlchemy 2.0 + MySQL
- ⚡ **Redis缓存**: 高性能缓存系统
- 🔐 **JWT认证**: 安全的用户认证机制
- 📝 **自动文档**: Swagger UI 和 ReDoc
- 🐳 **Docker支持**: 容器化部署
- 🧪 **测试覆盖**: 完整的单元测试和集成测试

## 快速开始

### 环境要求

- Python 3.8.1+
- MySQL 5.7+
- Redis 6.0+
- uv (推荐) 或 pip

### 安装依赖

```bash
# 使用uv (推荐)
make setup

# 或使用pip
pip install -e .
```

### 开发环境设置

```bash
# 完整的开发环境设置
make dev-setup

# 或手动设置
make setup-dev
make init-db
make create-sample-data
```

### 启动服务

```bash
# 开发模式 (热重载)
make dev

# 生产模式
make run
```

服务将在 http://localhost:5002 启动

### API文档

- Swagger UI: http://localhost:5002/docs
- ReDoc: http://localhost:5002/redoc

## API端点

### 文章管理

- `GET /api/posts/` - 获取文章列表
- `GET /api/posts/{id}` - 获取文章详情
- `POST /api/posts/` - 创建文章
- `PUT /api/posts/{id}` - 更新文章
- `DELETE /api/posts/{id}` - 删除文章
- `POST /api/posts/{id}/like` - 点赞文章

### 健康检查

- `GET /health` - 服务健康状态

## 配置

通过环境变量配置服务:

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/blog_db

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 用户服务配置
USER_SERVICE_URL=http://localhost:5001
```

## 开发

### 代码格式化

```bash
make format      # 格式化代码
make format-check # 检查代码格式
```

### 代码检查

```bash
make lint        # 运行代码检查
```

### 测试

```bash
make test        # 运行测试
make test-cov    # 运行测试并生成覆盖率报告
```

### 数据库管理

```bash
make init-db           # 初始化数据库
make create-sample-data # 创建示例数据
make clear-cache       # 清除Redis缓存
```

## Docker部署

### 构建镜像

```bash
make docker-build
```

### 运行容器

```bash
make docker-run
```

### Docker Compose

```bash
make docker-compose-up   # 启动所有服务
make docker-compose-down # 停止所有服务
```

## 项目结构

```
blog-service/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── models.py          # 数据模型
│   ├── extensions.py      # 扩展功能
│   ├── middleware.py      # 中间件
│   └── routers/
│       ├── __init__.py
│       └── posts.py       # 文章路由
├── scripts/
│   ├── __init__.py
│   └── create_sample_data.py # 示例数据脚本（已移至bin目录）
├── main.py                # 应用入口
├── pyproject.toml         # 项目配置
├── Dockerfile             # Docker配置
├── Makefile              # 构建脚本
└── README.md             # 项目文档
```

## 技术栈

- **Web框架**: FastAPI
- **ASGI服务器**: Uvicorn
- **数据库ORM**: SQLAlchemy 2.0
- **数据验证**: Pydantic
- **缓存**: Redis
- **认证**: JWT
- **容器化**: Docker
- **依赖管理**: uv
- **代码格式化**: Black, isort
- **代码检查**: flake8, mypy
- **测试**: pytest

## 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v2.0.0

- 🎉 重构为FastAPI框架
- ✨ 添加类型安全支持
- 🚀 提升API性能
- 📚 自动生成API文档
- 🔧 改进开发体验

### v1.0.0

- 🎉 初始版本 (Flask)
- 📝 基础文章管理功能
- 🔐 用户认证
- ⚡ Redis缓存