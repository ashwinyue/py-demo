# =============================================================================
# Docker相关规则
# =============================================================================

.PHONY: docker-build-images docker-build-user docker-build-blog docker-run docker-stop docker-clean

# Docker镜像标签
USER_IMAGE := $(PROJECT_NAME)-user:$(VERSION)
BLOG_IMAGE := $(PROJECT_NAME)-blog:$(VERSION)
USER_IMAGE_LATEST := $(PROJECT_NAME)-user:latest
BLOG_IMAGE_LATEST := $(PROJECT_NAME)-blog:latest

# 构建所有Docker镜像
docker-build-images: docker-build-user docker-build-blog
	$(call log_success,"所有Docker镜像构建完成")

# 构建用户服务Docker镜像
docker-build-user:
	$(call log_info,"构建用户服务Docker镜像...")
	$(call check_tool,docker)
	$(call check_file,$(DOCKER_DIR)/Dockerfile.user)
	docker build -f $(DOCKER_DIR)/Dockerfile.user -t $(USER_IMAGE) -t $(USER_IMAGE_LATEST) .
	$(call log_success,"用户服务镜像构建完成: $(USER_IMAGE)")

# 构建博客服务Docker镜像
docker-build-blog:
	$(call log_info,"构建博客服务Docker镜像...")
	$(call check_tool,docker)
	$(call check_file,$(DOCKER_DIR)/Dockerfile.blog)
	docker build -f $(DOCKER_DIR)/Dockerfile.blog -t $(BLOG_IMAGE) -t $(BLOG_IMAGE_LATEST) .
	$(call log_success,"博客服务镜像构建完成: $(BLOG_IMAGE)")

# 启动微服务Docker环境
docker-run:
	$(call log_info,"启动微服务Docker环境...")
	$(call check_tool,docker)
	$(call check_file,docker-compose.yml)
	docker-compose up -d
	$(call log_success,"微服务Docker环境启动完成")
	@echo "使用以下命令查看服务状态:"
	@echo "  docker-compose ps"
	@echo "  docker-compose logs -f"

# 停止微服务Docker环境
docker-stop:
	$(call log_info,"停止微服务Docker环境...")
	$(call check_tool,docker)
	docker-compose down
	$(call log_success,"微服务Docker环境已停止")

# 清理Docker资源
docker-clean:
	$(call log_info,"清理Docker资源...")
	$(call check_tool,docker)
	@echo "清理停止的容器..."
	@docker container prune -f
	@echo "清理未使用的镜像..."
	@docker image prune -f
	@echo "清理未使用的网络..."
	@docker network prune -f
	@echo "清理未使用的卷..."
	@docker volume prune -f
	$(call log_success,"Docker资源清理完成")

# 显示Docker镜像信息
docker-images:
	$(call log_info,"显示项目相关Docker镜像...")
	@docker images | grep -E "$(PROJECT_NAME)|REPOSITORY" || echo "未找到项目相关镜像"

# 推送Docker镜像到仓库
docker-push: docker-build-images
	$(call log_info,"推送Docker镜像到仓库...")
	$(call check_tool,docker)
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		$(call log_error,"请设置DOCKER_REGISTRY环境变量"); \
		exit 1; \
	fi
	@echo "标记镜像..."
	docker tag $(USER_IMAGE_LATEST) $(DOCKER_REGISTRY)/$(USER_IMAGE_LATEST)
	docker tag $(BLOG_IMAGE_LATEST) $(DOCKER_REGISTRY)/$(BLOG_IMAGE_LATEST)
	@echo "推送镜像..."
	docker push $(DOCKER_REGISTRY)/$(USER_IMAGE_LATEST)
	docker push $(DOCKER_REGISTRY)/$(BLOG_IMAGE_LATEST)
	$(call log_success,"Docker镜像推送完成")