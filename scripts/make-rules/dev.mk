# =============================================================================
# 开发环境相关规则
# =============================================================================

.PHONY: setup init-db dev dev-microservices dev-stop dev-setup microservices-setup status

# 项目初始化
setup:
	$(call log_info,"初始化项目环境...")
	@if [ ! -f .env ]; then \
		cp configs/.env.example .env; \
		$(call log_warn,"已创建.env文件，请务必修改以下配置:"); \
		echo "  - SECRET_KEY: 设置生产环境密钥"; \
		echo "  - DATABASE_URL: 设置MySQL数据库连接"; \
		echo "  - REDIS_HOST: 设置Redis服务器地址"; \
		echo "  - NACOS_HOST: 设置Nacos服务器地址"; \
	fi
	@if [ -n "$(HAS_UV)" ]; then \
		$(call log_info,"使用uv安装依赖..."); \
		uv sync; \
	else \
		$(call log_info,"使用pip安装依赖..."); \
		pip install -r requirements.txt; \
	fi
	$(call log_warn,"注意: 请确保MySQL数据库已创建并可访问，然后运行数据库初始化")
	$(call log_info,"数据库初始化命令: make init-db")

# 初始化MySQL数据库
init-db:
	$(call log_info,"初始化MySQL数据库...")
	$(call check_file,.env)
	@if [ -n "$(HAS_UV)" ]; then \
		uv run flask init-db; \
	else \
		flask init-db; \
	fi
	$(call log_success,"数据库初始化完成")

# 开发服务器（单体应用）
dev:
	$(call log_info,"启动Flask开发服务器（单体应用）...")
	@if [ -n "$(HAS_UV)" ]; then \
		uv run python run.py; \
	else \
		python run.py; \
	fi

# 微服务开发环境
dev-microservices:
	$(call log_info,"启动微服务开发环境...")
	@chmod +x $(SCRIPTS_DIR)/dev-start.sh
	@$(SCRIPTS_DIR)/dev-start.sh

# 停止微服务开发环境
dev-stop:
	$(call log_info,"停止微服务开发环境...")
	@chmod +x $(SCRIPTS_DIR)/dev-stop.sh
	@$(SCRIPTS_DIR)/dev-stop.sh

# 开发环境完整设置
dev-setup: setup
	$(call log_success,"开发环境设置完成")
	@echo "单体应用: 使用 'make dev' 启动"
	@echo "微服务架构: 使用 'make dev-microservices' 启动"

# 微服务架构设置
microservices-setup: setup
	$(call log_info,"微服务架构环境设置...")
	$(call check_tool,docker)
	$(call check_tool,docker)
	@echo "使用 'make dev-microservices' 启动微服务开发环境"
	@echo "使用 'make dev-stop' 停止微服务开发环境"

# 显示项目状态
status:
	@echo "$(CYAN)=== 项目状态 ===$(RESET)"
	@echo "项目目录: $(ROOT_DIR)"
	@echo "项目版本: $(VERSION)"
	@echo "构建日期: $(BUILD_DATE)"
	@echo "Git提交: $(GIT_COMMIT)"
	@echo "Python版本: $(shell python3 --version 2>/dev/null || echo '未安装')"
	@echo "Docker版本: $(shell docker --version 2>/dev/null || echo '未安装')"
	@echo "Helm版本: $(shell helm version --short 2>/dev/null || echo '未安装')"
	@echo "Kind版本: $(shell kind version 2>/dev/null || echo '未安装')"
	@echo "kubectl版本: $(shell kubectl version --client --short 2>/dev/null || echo '未安装')"
	@if [ -f .env ]; then echo "配置文件: $(GREEN)✓$(RESET) .env存在"; else echo "配置文件: $(RED)✗$(RESET) .env不存在"; fi