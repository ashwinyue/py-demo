# Python MiniBlog 项目结构

本文档描述了重构后的 Python MiniBlog 项目的目录结构和组织方式。

## 项目根目录结构

```
py-demo/
├── app/                          # 单体应用代码
│   ├── __init__.py
│   ├── models/                   # 数据模型
│   ├── views/                    # 视图控制器
│   ├── utils/                    # 工具函数
│   └── templates/                # 模板文件
├── services/                     # 微服务代码
│   ├── user-service/             # 用户服务
│   │   ├── app/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── run.py
│   └── blog-service/             # 博客服务
│       ├── app/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── run.py
├── scripts/                      # 部署和管理脚本
│   ├── deploy.sh                 # Kubernetes 部署脚本
│   ├── start-dev.sh              # 微服务开发环境启动脚本
│   └── stop-dev.sh               # 微服务开发环境停止脚本
├── docker/                       # Docker 配置文件
│   └── docker-compose.microservices.yml  # 微服务 Docker Compose 配置
├── configs/                      # 配置文件
│   └── tyk-config/               # Tyk API 网关配置
│       ├── apps/                 # API 定义
│       │   └── api-definition.json
│       └── policies/             # 策略配置
│           └── policies.json
├── docs/                         # 项目文档
│   ├── README-MICROSERVICES.md   # 微服务架构文档
│   └── PROJECT-STRUCTURE.md      # 项目结构文档（本文件）
├── helm/                         # Helm 部署配置
│   └── python-miniblog/
├── tests/                        # 测试文件
├── migrations/                   # 数据库迁移文件
├── static/                       # 静态资源
├── templates/                    # 模板文件
├── Makefile                      # 项目管理命令
├── docker-compose.yml            # 单体应用 Docker Compose 配置
├── requirements.txt              # Python 依赖
├── pyproject.toml               # 项目配置
├── .env.example                 # 环境变量示例
└── run.py                       # 单体应用启动文件
```

## 目录说明

### 核心目录

- **`app/`**: 单体应用的核心代码，包含模型、视图、工具函数等
- **`services/`**: 微服务代码，每个服务都是独立的应用
- **`scripts/`**: 部署和管理脚本，统一管理项目的自动化操作
- **`docker/`**: Docker 相关配置文件
- **`configs/`**: 各种配置文件，包括 API 网关配置
- **`docs/`**: 项目文档

### 微服务目录

每个微服务都包含：
- `app/`: 服务的核心代码
- `Dockerfile`: Docker 镜像构建文件
- `requirements.txt`: Python 依赖
- `run.py`: 服务启动文件

### 配置目录

- **`configs/tyk-config/`**: Tyk API 网关配置
  - `apps/`: API 定义文件
  - `policies/`: 访问策略配置

## 架构模式

项目支持两种架构模式：

1. **单体应用模式**: 使用 `app/` 目录下的代码，通过 `run.py` 启动
2. **微服务模式**: 使用 `services/` 目录下的各个服务，通过 Docker Compose 或 Kubernetes 部署

## 管理命令

项目使用 `Makefile` 统一管理各种操作：

- `make dev`: 启动单体应用开发服务器
- `make dev-microservices`: 启动微服务开发环境
- `make dev-stop`: 停止微服务开发环境
- `make docker-build`: 构建微服务 Docker 镜像
- `make docker-run`: 使用 Docker Compose 启动微服务
- `make deploy`: 部署到 Kubernetes
- `make status`: 查看项目状态

## 开发工作流

### 单体应用开发

1. 配置环境变量：`cp .env.example .env`
2. 安装依赖：`make setup`
3. 初始化数据库：`make init-db`
4. 启动开发服务器：`make dev`

### 微服务开发

1. 配置环境变量：`cp .env.example .env`
2. 启动微服务环境：`make dev-microservices`
3. 停止微服务环境：`make dev-stop`

### 生产部署

1. 构建镜像：`make docker-build`
2. 部署到 Kubernetes：`make deploy`

## 注意事项

1. 微服务模式需要 Docker 和 Docker Compose
2. Kubernetes 部署需要 kubectl 和 Helm
3. 确保所有脚本都有执行权限
4. 配置文件路径已经适配新的目录结构