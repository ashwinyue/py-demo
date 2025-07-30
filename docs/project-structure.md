# 项目结构说明

本文档描述了Mini Blog项目的目录结构和组织方式。

## 目录结构

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
├── scripts/               # 脚本文件目录
│   ├── start.sh          # 传统启动脚本
│   └── start_uv.sh       # uv启动脚本
├── configs/               # 配置文件目录
│   └── .env.example      # 环境变量示例
├── docs/                  # 文档目录
│   └── project-structure.md # 项目结构说明
├── tests/                 # 测试文件目录
├── logs/                  # 日志文件目录
├── docker/                # Docker配置
│   └── Dockerfile
├── helm/                  # Helm图表
│   └── python-miniblog/
│       ├── Chart.yaml
│       ├── templates/
│       └── values.yaml
├── Makefile              # 项目管理脚本
├── main.py               # 应用入口点
├── miniblog.py          # 应用入口
├── run.py               # 开发启动脚本
├── pyproject.toml       # 项目配置和依赖
├── requirements.txt     # 依赖包列表
├── uv.lock             # uv锁定文件
├── .python-version     # Python版本
├── .gitignore          # Git忽略文件
└── README.md           # 项目说明
```

## 目录说明

### 核心目录

- **`app/`**: Flask应用的核心代码
  - 包含所有业务逻辑、模型、API路由等
  - 使用蓝图模式组织代码

- **`scripts/`**: 各种脚本文件
  - 启动脚本、部署脚本、工具脚本等
  - 统一管理，避免根目录混乱

- **`configs/`**: 配置文件
  - 环境变量模板、配置文件等
  - 便于不同环境的配置管理

### 开发相关

- **`tests/`**: 测试文件
  - 单元测试、集成测试等
  - 保持测试代码的组织性

- **`docs/`**: 项目文档
  - API文档、架构说明、使用指南等
  - 便于项目维护和新人上手

- **`logs/`**: 日志文件
  - 应用运行日志、错误日志等
  - 便于问题排查和监控

### 部署相关

- **`docker/`**: Docker相关文件
  - Dockerfile、docker-compose等

- **`helm/`**: Kubernetes Helm图表
  - 用于Kubernetes部署

## 使用Makefile管理

项目现在使用Makefile来统一管理各种操作：

```bash
# 查看所有可用命令
make help

# 初始化项目
make setup

# 启动开发服务器
make dev-uv

# 运行测试
make test

# 构建Docker镜像
make docker-build
```

## 优势

1. **清晰的职责分离**: 每个目录都有明确的用途
2. **易于维护**: 相关文件集中管理
3. **便于扩展**: 新功能可以按照既定结构添加
4. **标准化**: 符合现代Python项目的最佳实践
5. **工具集成**: 与现代开发工具（uv、Docker、Helm）良好集成

## 迁移说明

从原有结构迁移到新结构时，主要变化：

1. 脚本文件移动到 `scripts/` 目录
2. 配置文件移动到 `configs/` 目录
3. 添加了 `docs/`、`tests/`、`logs/` 目录
4. 使用Makefile替代直接运行脚本

这种结构更适合团队协作和项目的长期维护。