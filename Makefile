# =============================================================================
# Python MiniBlog 项目 Makefile
# =============================================================================

# 默认目标
.DEFAULT_GOAL := help

# 包含通用规则和变量
include scripts/make-rules/common.mk

# 包含各功能模块
include scripts/make-rules/dev.mk
include scripts/make-rules/test.mk
include scripts/make-rules/docker.mk
include scripts/make-rules/help.mk

# 环境配置目录
MANIFESTS_DIR := $(ROOT_DIR)/manifests

# 兼容性别名（保持向后兼容）
.PHONY: microservices-docker

# 启动微服务Docker环境（兼容性别名）
microservices-docker: docker-run

# 显示项目信息
.PHONY: info
info:
	@echo "$(CYAN)=== 项目信息 ===$(RESET)"
	@echo "项目名称: $(PROJECT_NAME)"
	@echo "项目版本: $(VERSION)"
	@echo "构建日期: $(BUILD_DATE)"
	@echo "Git提交: $(GIT_COMMIT)"
	@echo "根目录: $(ROOT_DIR)"
	@echo "配置清单目录: $(MANIFESTS_DIR)"
	@echo "脚本目录: $(SCRIPTS_DIR)"

