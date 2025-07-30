# Python Mini Blog

一个现代化的 Python 微服务博客系统。基于 Flask 框架构建，采用微服务架构，集成了用户管理、博客文章管理、缓存、数据库迁移等功能。

## 项目特性

- 🏗️ **微服务架构**：用户服务和博客服务独立部署
- 🔐 **用户系统**：完整的用户注册、登录、JWT认证
- 📝 **博客管理**：文章的增删改查、分类、标签
- 🚀 **高性能**：Redis 缓存、数据库连接池
- 📊 **可观测性**：结构化日志、健康检查
- 🐳 **容器化**：Docker 和 Kubernetes 支持
- 📖 **API文档**：集成 Swagger OpenAPI 文档
- 🔧 **现代工具**：支持 uv 包管理器，快速依赖安装
- 🌐 **API网关**：Tyk 网关统一管理服务路由
- ⚙️ **配置管理**：Nacos 动态配置管理，支持配置热更新

## 📁 项目结构

```
py-demo/
├── services/                     # 微服务代码
│   ├── user-service/             # 用户服务
│   ├── blog-service/             # 博客服务
│   └── common/                   # 共享代码
├── scripts/                      # 部署和管理脚本
│   ├── deploy.sh                 # Kubernetes部署
│   ├── start-dev.sh              # 微服务开发环境启动
│   ├── stop-dev.sh               # 微服务开发环境停止
│   └── manage_nacos_config.py    # Nacos配置管理脚本
├── docker/                       # Docker配置
│   └── docker-compose.microservices.yml
├── configs/                      # 配置文件
│   ├── tyk-config/               # Tyk API网关配置
│   ├── .env.example              # 环境变量示例
│   └── nacos-config-examples.json # Nacos配置示例
├── docs/                         # 项目文档
│   ├── README-MICROSERVICES.md   # 微服务架构文档
│   ├── PROJECT-STRUCTURE.md      # 项目结构文档
│   └── nacos-config-guide.md     # Nacos配置管理指南
├── helm/                         # Kubernetes部署
├── tests/                        # 测试文件
├── Makefile                      # 项目管理命令
├── main.py                       # 主入口文件
├── miniblog.py                   # 应用启动文件
└── requirements.txt              # Python依赖
```

详细的项目结构说明请参考 [PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md)。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Docker & Docker Compose
- MySQL 8.0+
- Redis 6.0+

### 微服务模式启动

#### 1. 配置环境变量
```bash
cp configs/.env.example .env
# 编辑 .env 文件，配置数据库和 Redis 连接信息
```

#### 2. 安装依赖（可选，Docker模式不需要）

使用 pip：
```bash
cd services/user-service && pip install -r requirements.txt
cd ../blog-service && pip install -r requirements.txt
```

使用 uv（推荐，更快）：
```bash
cd services/user-service && uv pip install -r requirements.txt
cd ../blog-service && uv pip install -r requirements.txt
```

#### 3. 启动微服务
```bash
# 启动所有微服务（包含数据库、Redis、API网关）
./scripts/start-dev.sh

# 停止所有服务
./scripts/stop-dev.sh
```

#### 4. 初始化数据库
```bash
# 用户服务数据库
cd services/user-service && flask db upgrade

# 博客服务数据库
cd ../blog-service && flask db upgrade
```

## 📖 API 文档

本项目集成了 Swagger OpenAPI 文档，提供交互式 API 文档界面：

### 微服务 API 文档
- **用户服务**：
  - API 文档：http://localhost:5001/api/docs
  - Swagger UI：http://localhost:5001/docs/
- **博客服务**：
  - API 文档：http://localhost:5002/api/docs
  - Swagger UI：http://localhost:5002/docs/
- **API 网关**：http://localhost:8080

### Swagger UI 功能
通过 Swagger UI 可以：
- 📋 查看所有 API 接口文档
- 🧪 在线测试 API 接口
- 📊 查看请求/响应数据模型
- 📥 下载 OpenAPI 规范文件

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
| NACOS_NAMESPACE | Nacos命名空间 | public |
| SERVICE_NAME | 服务名称 | user-service/blog-service |

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

## 🛠️ 开发指南

### 微服务开发

#### 添加新的API端点
1. 在对应服务的蓝图文件中添加路由函数
2. 添加 Flask-RESTX 装饰器和文档注解
3. 更新错误处理和数据验证
4. 更新缓存逻辑（如需要）

#### 数据库迁移
```bash
# 用户服务
cd services/user-service
flask db init     # 初始化迁移
flask db migrate  # 生成迁移文件
flask db upgrade  # 应用迁移

# 博客服务
cd services/blog-service
flask db init
flask db migrate
flask db upgrade
```

#### 服务间通信
- 使用 HTTP REST API 进行服务间通信
- 通过 Tyk API 网关进行路由和负载均衡
- 使用 Redis 进行缓存和会话共享

## ⚙️ 配置管理

本项目集成了 Nacos 配置管理功能，支持动态配置和配置热更新。

### 配置特性
- 🔄 **动态配置**：从 Nacos 动态加载配置，无需重启服务
- 🔥 **热更新**：配置变更时自动更新应用配置
- 📦 **分组管理**：按业务模块组织配置
- 🌍 **多环境**：通过命名空间区分不同环境
- 💾 **本地缓存**：配置本地缓存，提高访问性能

### 配置管理

```bash
# 发布示例配置到 Nacos
python scripts/manage_nacos_config.py publish-examples --group DEFAULT_GROUP

# 获取配置
python scripts/manage_nacos_config.py get --data-id common-config --group DEFAULT_GROUP

# 发布单个配置
python scripts/manage_nacos_config.py publish --data-id test-config --content '{"key": "value"}'
```

详细的配置管理指南请参考 [Nacos配置管理指南](docs/nacos-config-guide.md)。

## 🔧 技术栈

- **Web框架**: Flask 2.3.3
- **API文档**: Flask-RESTX (Swagger OpenAPI)
- **ORM**: SQLAlchemy 3.0.5
- **数据库**: MySQL 8.0+
- **缓存**: Redis 6.0+
- **API网关**: Tyk Gateway
- **配置中心**: Nacos
- **WSGI服务器**: Gunicorn
- **容器化**: Docker + Kubernetes
- **包管理**: uv (推荐) / pip
- **架构模式**: 微服务架构

## 许可证

MIT License