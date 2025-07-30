# Make Rules 模块化说明

本目录包含了项目的模块化 Make 规则，将原本的单一 Makefile 拆分为多个功能模块，便于维护和扩展。

## 目录结构

```
scripts/make-rules/
├── README.md          # 本说明文件
├── common.mk          # 通用变量和函数定义
├── dev.mk             # 开发环境相关规则
├── test.mk            # 测试相关规则
├── docker.mk          # Docker相关规则


└── help.mk            # 帮助信息
```

## 模块说明

### common.mk
- 项目基本信息和版本管理
- 目录路径定义
- 工具检测和命令选择
- 通用函数（日志输出、工具检查等）
- 颜色定义

### dev.mk
- 项目初始化 (`setup`)
- 数据库初始化 (`init-db`)
- 开发服务器启动 (`dev`, `dev-microservices`)
- 开发环境管理 (`dev-stop`, `dev-setup`)
- 项目状态查看 (`status`)

### test.mk
- 单元测试和集成测试
- API接口测试（多环境支持）
- 代码检查和格式化 (`lint`, `format`)
- 临时文件清理 (`clean`)

### docker.mk
- Docker镜像构建（用户服务、博客服务）
- Docker环境管理 (`docker-run`, `docker-stop`)
- Docker资源清理 (`docker-clean`)
- 镜像推送到仓库 (`docker-push`)



### help.mk
- 完整的帮助信息
- 命令分类展示
- 快速开始指南

## 使用方法

所有模块通过主 Makefile 自动包含，使用方式与之前完全相同：

```bash
# 查看帮助
make help

# 项目初始化
make setup

# 启动开发环境
make dev

# 构建和部署
make kind-deploy
```

## 扩展说明

如需添加新功能模块：

1. 在 `scripts/make-rules/` 目录下创建新的 `.mk` 文件
2. 在主 Makefile 中添加 `include scripts/make-rules/新模块.mk`
3. 在 `help.mk` 中添加相应的帮助信息

## 兼容性

为保持向后兼容，主 Makefile 中保留了一些别名：
- `microservices-docker` -> `docker-run`

所有原有命令都可以正常使用。