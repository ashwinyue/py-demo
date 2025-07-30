#!/bin/bash

# 微服务部署脚本
# 用于部署重构后的Python MiniBlog微服务架构

set -e

echo "开始部署Python MiniBlog微服务架构..."

# 检查必要的工具
command -v kubectl >/dev/null 2>&1 || { echo "错误: kubectl 未安装" >&2; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "错误: helm 未安装" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "错误: docker 未安装" >&2; exit 1; }

# 设置变量
NAMESPACE=${NAMESPACE:-"miniblog"}
RELEASE_NAME=${RELEASE_NAME:-"python-miniblog"}
CHART_PATH="./helm/python-miniblog"

echo "使用命名空间: $NAMESPACE"
echo "使用发布名称: $RELEASE_NAME"

# 创建命名空间（如果不存在）
echo "创建命名空间..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 构建Docker镜像
echo "构建Docker镜像..."

# 构建用户服务镜像
echo "构建用户服务镜像..."
docker build -t python-miniblog-user-service:latest ./services/user-service

# 构建博客服务镜像
echo "构建博客服务镜像..."
docker build -t python-miniblog-blog-service:latest ./services/blog-service

# 构建API网关镜像
echo "构建API网关镜像..."
docker build -t python-miniblog-gateway:latest ./services/api-gateway

# 部署Helm Chart
echo "部署Helm Chart..."
helm upgrade --install $RELEASE_NAME $CHART_PATH \
  --namespace $NAMESPACE \
  --set userService.image.tag=latest \
  --set blogService.image.tag=latest \
  --set apiGateway.image.tag=latest \
  --wait

echo "等待所有Pod就绪..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=$RELEASE_NAME -n $NAMESPACE --timeout=300s

# 显示部署状态
echo "部署状态:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

# 显示服务信息
echo "\n服务信息:"
kubectl get svc -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

# 显示Ingress信息
echo "\nIngress信息:"
kubectl get ingress -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

echo "\n部署完成！"
echo "\n访问应用:"
echo "- 如果使用Ingress，请访问配置的域名"
echo "- 如果使用NodePort，请使用以下命令获取访问地址:"
echo "  kubectl get svc -n $NAMESPACE"

echo "\n查看日志:"
echo "- 用户服务: kubectl logs -f deployment/python-miniblog-user-service -n $NAMESPACE"
echo "- 博客服务: kubectl logs -f deployment/python-miniblog-blog-service -n $NAMESPACE"
echo "- API网关: kubectl logs -f deployment/python-miniblog-gateway -n $NAMESPACE"
echo "- Tyk网关: kubectl logs -f deployment/python-miniblog-tyk-gateway -n $NAMESPACE"