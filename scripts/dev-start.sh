#!/bin/bash

# 本地开发环境启动脚本
# 用于启动Python MiniBlog微服务开发环境

set -e

echo "启动Python MiniBlog微服务开发环境..."

# 检查必要的工具
command -v docker >/dev/null 2>&1 || { echo "错误: docker 未安装" >&2; exit 1; }
if ! docker compose version >/dev/null 2>&1; then
    echo "错误: docker compose 未安装" >&2
    exit 1
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p tyk-config/apps
mkdir -p tyk-config/policies
mkdir -p logs

# 检查配置文件
if [ ! -f "configs/tyk-config/apps/api-definition.json" ]; then
    echo "警告: Tyk API定义文件不存在，请确保已创建 configs/tyk-config/apps/api-definition.json"
fi

if [ ! -f "configs/tyk-config/policies/policies.json" ]; then
    echo "警告: Tyk策略文件不存在，请确保已创建 configs/tyk-config/policies/policies.json"
fi

# 停止现有容器（如果存在）
echo "停止现有容器..."
docker compose -f docker/docker-compose.microservices.yml down

# 清理旧的镜像（可选）
read -p "是否清理旧的Docker镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理旧镜像..."
    docker compose -f docker/docker-compose.microservices.yml down --rmi local
fi

# 构建并启动服务
echo "构建并启动服务..."
docker compose -f docker/docker-compose.microservices.yml up --build -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 检查服务状态
echo "检查服务状态..."
docker compose -f docker/docker-compose.microservices.yml ps

# 健康检查
echo "\n执行健康检查..."

services=("mysql:3306" "redis:6379" "nacos:8848" "user-service:5001" "blog-service:5002" "api-gateway:8000" "tyk-gateway:8080")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "检查 $name ($port)... "
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✓ 运行中"
    else
        echo "✗ 未响应"
    fi
done

# 显示访问信息
echo "\n=== 服务访问信息 ==="
echo "用户服务: http://localhost:5001"
echo "博客服务: http://localhost:5002"
echo "API网关: http://localhost:8000"
echo "Tyk网关: http://localhost:8080"
echo "MySQL: localhost:3306 (用户名: miniblog, 密码: miniblog123)"
echo "Redis: localhost:6379"
echo "Nacos: http://localhost:8848/nacos (用户名: nacos, 密码: nacos)"

echo "\n=== API测试示例 ==="
echo "1. 用户注册:"
echo "curl -X POST http://localhost:8080/api/users/register \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"test\",\"email\":\"test@example.com\",\"password\":\"password123\"}'"

echo "\n2. 用户登录:"
echo "curl -X POST http://localhost:8080/api/users/login \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"test\",\"password\":\"password123\"}'"

echo "\n3. 获取用户资料（需要JWT令牌）:"
echo "curl -X GET http://localhost:8080/api/users/profile \\"
echo "  -H 'Authorization: Bearer <your-jwt-token>'"

echo "\n=== 日志查看 ==="
echo "查看所有服务日志: docker compose -f docker/docker-compose.microservices.yml logs -f"
echo "查看特定服务日志: docker compose -f docker/docker-compose.microservices.yml logs -f <service-name>"

echo "\n=== 停止服务 ==="
echo "停止所有服务: docker compose -f docker/docker-compose.microservices.yml down"
echo "或使用: make dev-stop"

echo "\n开发环境启动完成！"