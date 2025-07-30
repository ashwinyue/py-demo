# =============================================================================
# 测试相关规则
# =============================================================================

.PHONY: test test-unit test-integration test-api test-api-dev lint format clean

# 运行所有测试
test: test-unit test-integration
	$(call log_success,"所有测试完成")

# 运行单元测试
test-unit:
	$(call log_info,"运行单元测试...")
	@if [ -n "$(HAS_UV)" ]; then \
		uv run pytest tests/unit/ -v; \
	else \
		pytest tests/unit/ -v; \
	fi

# 运行集成测试
test-integration:
	$(call log_info,"运行集成测试...")
	@if [ -n "$(HAS_UV)" ]; then \
		uv run pytest tests/integration/ -v; \
	else \
		pytest tests/integration/ -v; \
	fi

# 测试API接口（默认环境）
test-api:
	$(call log_info,"运行API接口测试...")
	@$(SCRIPTS_DIR)/test-api.sh

# 测试API接口（开发环境）
test-api-dev:
	$(call log_info,"运行API接口测试（开发环境）...")
	@USER_SERVICE_URL=http://localhost:5001 BLOG_SERVICE_URL=http://localhost:5002 $(SCRIPTS_DIR)/test-api.sh



# 代码检查
lint:
	$(call log_info,"运行代码检查...")
	@if [ -n "$(HAS_UV)" ]; then \
		uv run flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503; \
		uv run black --check src/ tests/; \
		uv run isort --check-only src/ tests/; \
	else \
		flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503; \
		black --check src/ tests/; \
		isort --check-only src/ tests/; \
	fi

# 代码格式化
format:
	$(call log_info,"格式化代码...")
	@if [ -n "$(HAS_UV)" ]; then \
		uv run black src/ tests/; \
		uv run isort src/ tests/; \
	else \
		black src/ tests/; \
		isort src/ tests/; \
	fi
	$(call log_success,"代码格式化完成")

# 清理临时文件
clean:
	$(call log_info,"清理临时文件...")
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true
	$(call log_success,"清理完成")