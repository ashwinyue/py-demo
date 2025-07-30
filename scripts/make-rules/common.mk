# =============================================================================
# 通用变量和函数定义
# =============================================================================

# 项目信息
PROJECT_NAME := python-miniblog
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# 目录定义
ROOT_DIR := $(shell pwd)
BIN_DIR := $(ROOT_DIR)/bin
SCRIPTS_DIR := $(ROOT_DIR)/scripts
SRC_DIR := $(ROOT_DIR)/src
DOCKER_DIR := $(ROOT_DIR)/docker
HELM_DIR := $(ROOT_DIR)/helm
MANIFESTS_DIR := $(ROOT_DIR)/manifests

# 工具检测
HAS_UV := $(shell command -v uv 2>/dev/null)
HAS_DOCKER := $(shell command -v docker 2>/dev/null)
HAS_KUBECTL := $(shell command -v kubectl 2>/dev/null)
HAS_HELM := $(shell command -v helm 2>/dev/null)
HAS_KIND := $(shell command -v kind 2>/dev/null)

# Python命令选择
ifeq ($(HAS_UV),)
    PYTHON_CMD := python3
    PIP_CMD := pip3
else
    PYTHON_CMD := uv run python
    PIP_CMD := uv
endif

# 颜色定义
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# 通用函数
define log_info
	@echo "$(CYAN)[INFO]$(RESET) $(1)"
endef

define log_warn
	@echo "$(YELLOW)[WARN]$(RESET) $(1)"
endef

define log_error
	@echo "$(RED)[ERROR]$(RESET) $(1)"
endef

define log_success
	@echo "$(GREEN)[SUCCESS]$(RESET) $(1)"
endef

# 检查工具是否安装
define check_tool
	@if [ -z "$(shell command -v $(1))" ]; then \
		echo "$(RED)[ERROR]$(RESET) $(1) 未安装，请先安装 $(1)"; \
		exit 1; \
	fi
endef

# 创建目录
define ensure_dir
	@mkdir -p $(1)
endef

# 检查文件是否存在
define check_file
	@if [ ! -f "$(1)" ]; then \
		echo "$(RED)[ERROR]$(RESET) 文件不存在: $(1)"; \
		exit 1; \
	fi
endef