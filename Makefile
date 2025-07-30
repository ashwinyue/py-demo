.PHONY: help setup init-db dev dev-uv test lint format clean build docker-build docker-run deploy helm-install helm-uninstall

# 默认目标
help:
	@echo "Available commands:"
	@echo "  setup       - 初始化项目环境"
	@echo "  init-db     - 初始化MySQL数据库"
	@echo "  dev         - 启动开发服务器（传统方式）"
	@echo "  dev-uv      - 使用uv启动开发服务器"
	@echo "  test        - 运行测试"
	@echo "  lint        - 代码检查"
	@echo "  format      - 代码格式化"
	@echo "  clean       - 清理临时文件"
	@echo "  build       - 构建应用"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run  - 运行Docker容器"
	@echo "  deploy      - 部署到生产环境"
	@echo "  helm-install - 使用Helm安装到Kubernetes"
	@echo "  helm-uninstall - 卸载Helm部署"

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

# 开发服务器（传统方式）
dev:
	@echo "启动Flask开发服务器（传统方式）..."
	@if [ -f .venv/bin/activate ]; then \
		source .venv/bin/activate && python run.py; \
	else \
		python run.py; \
	fi

# 开发服务器（uv方式）
dev-uv:
	@echo "使用uv启动Mini Blog应用..."
	uv run python run.py

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
	@echo "构建Docker镜像..."
	docker build -t miniblog:latest -f docker/Dockerfile .

# 运行Docker容器
docker-run: docker-build
	@echo "运行Docker容器..."
	docker run -p 5000:5000 --name miniblog-container miniblog:latest

# 部署到生产环境
deploy: build
	@echo "部署到生产环境..."
	gunicorn -w 4 -b 0.0.0.0:5000 miniblog:app

# 使用Helm安装到Kubernetes
helm-install:
	@echo "使用Helm安装到Kubernetes..."
	helm install miniblog ./helm/python-miniblog

# 卸载Helm部署
helm-uninstall:
	@echo "卸载Helm部署..."
	helm uninstall miniblog

# 开发环境完整设置
dev-setup: setup
	@echo "开发环境设置完成，使用 'make dev-uv' 启动应用"