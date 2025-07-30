.PHONY: help setup init-db dev dev-microservices dev-stop test lint format clean build docker-build docker-run deploy helm-install helm-uninstall dev-setup microservices-setup status

# 默认目标
help:
	@echo "Available commands:"
	@echo "  setup              - 初始化项目环境"
	@echo "  init-db            - 初始化MySQL数据库"
	@echo "  dev                - 启动单体应用开发服务器"
	@echo "  dev-microservices  - 启动微服务开发环境"
	@echo "  dev-stop           - 停止微服务开发环境"
	@echo "  test               - 运行测试"
	@echo "  lint               - 代码检查"
	@echo "  format             - 代码格式化"
	@echo "  clean              - 清理临时文件"
	@echo "  build              - 构建应用"
	@echo "  docker-build       - 构建Docker镜像"
	@echo "  docker-run         - 运行Docker容器"
	@echo "  deploy             - 部署到Kubernetes"
	@echo "  helm-install       - 使用Helm安装到Kubernetes"
	@echo "  helm-uninstall     - 卸载Helm部署"
	@echo "  dev-setup          - 开发环境完整设置"
	@echo "  microservices-setup - 微服务架构设置"
	@echo "  status             - 显示项目状态"

# 项目初始化
setup:
	@echo "初始化项目环境..."
	@if [ ! -f .env ]; then \
		cp configs/.env.example .env; \
		echo "已创建.env文件，请务必修改以下配置:"; \
		echo "  - SECRET_KEY: 设置生产环境密钥"; \
		echo "  - DATABASE_URL: 设置MySQL数据库连接"; \
		echo "  - REDIS_HOST: 设置Redis服务器地址"; \
		echo "  - NACOS_HOST: 设置Nacos服务器地址"; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		echo "使用uv安装依赖..."; \
		uv sync; \
	else \
		echo "使用pip安装依赖..."; \
		pip install -r requirements.txt; \
	fi
	@echo "注意: 请确保MySQL数据库已创建并可访问，然后运行数据库初始化"
	@echo "数据库初始化命令: make init-db"

# 初始化MySQL数据库
init-db:
	@echo "初始化MySQL数据库..."
	@if [ ! -f .env ]; then \
		echo "错误: .env文件不存在，请先运行 'make setup'"; \
		exit 1; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		uv run flask init-db; \
	else \
		flask init-db; \
	fi
	@echo "数据库初始化完成"

# 开发服务器（单体应用）
dev:
	@echo "启动Flask开发服务器（单体应用）..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python run.py; \
	else \
		python run.py; \
	fi

# 微服务开发环境
dev-microservices:
	@echo "启动微服务开发环境..."
	@chmod +x scripts/start-dev.sh
	@./scripts/start-dev.sh

# 停止微服务开发环境
dev-stop:
	@echo "停止微服务开发环境..."
	@chmod +x scripts/stop-dev.sh
	@./scripts/stop-dev.sh

# 运行测试
test:
	@echo "运行测试..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest; \
	else \
		pytest; \
	fi

# 代码检查
lint:
	@echo "运行代码检查..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run flake8 app/ *.py; \
	else \
		flake8 app/ *.py; \
	fi

# 代码格式化
format:
	@echo "格式化代码..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run black app/ *.py; \
	else \
		black app/ *.py; \
	fi

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# 构建应用
build: clean lint test
	@echo "构建应用..."
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python -m build; \
	fi

# 构建Docker镜像
docker-build:
	@echo "构建微服务Docker镜像..."
	docker build -t python-miniblog-user-service:latest ./services/user-service
	docker build -t python-miniblog-blog-service:latest ./services/blog-service
	@echo "所有微服务镜像构建完成"

# 运行Docker容器（微服务）
docker-run:
	@echo "启动微服务Docker环境..."
	docker-compose -f docker/docker-compose.microservices.yml up -d

# 部署到Kubernetes
deploy:
	@echo "部署微服务到Kubernetes..."
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh

# 使用Helm安装到Kubernetes
helm-install:
	@echo "使用Helm安装微服务到Kubernetes..."
	helm upgrade --install python-miniblog ./helm/python-miniblog --namespace miniblog --create-namespace

# 卸载Helm部署
helm-uninstall:
	@echo "卸载Helm部署..."
	helm uninstall python-miniblog --namespace miniblog

# 开发环境完整设置
dev-setup: setup
	@echo "开发环境设置完成"
	@echo "单体应用: 使用 'make dev' 启动"
	@echo "微服务架构: 使用 'make dev-microservices' 启动"

# 微服务架构设置
microservices-setup: setup
	@echo "微服务架构环境设置..."
	@echo "确保Docker和docker-compose已安装"
	@echo "使用 'make dev-microservices' 启动微服务开发环境"
	@echo "使用 'make dev-stop' 停止微服务开发环境"

# 显示项目状态
status:
	@echo "=== 项目状态 ==="
	@echo "项目目录: $(PWD)"
	@echo "Python版本: $(shell python --version 2>/dev/null || echo '未安装')"
	@echo "Docker版本: $(shell docker --version 2>/dev/null || echo '未安装')"
	@echo "Helm版本: $(shell helm version --short 2>/dev/null || echo '未安装')"
	@echo "kubectl版本: $(shell kubectl version --client --short 2>/dev/null || echo '未安装')"
	@if [ -f .env ]; then echo "配置文件: ✓ .env存在"; else echo "配置文件: ✗ .env不存在"; fi