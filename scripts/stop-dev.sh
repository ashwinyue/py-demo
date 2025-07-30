#!/bin/bash

# 停止本地开发环境脚本
# 用于停止Python MiniBlog微服务开发环境

set -e

echo "停止Python MiniBlog微服务开发环境..."

# 检查docker-compose是否可用
command -v docker-compose >/dev/null 2>&1 || { echo "错误: docker-compose 未安装" >&2; exit 1; }

# 停止所有服务
echo "停止所有服务..."
docker-compose -f docker/docker-compose.microservices.yml down

# 询问是否清理数据卷
read -p "是否删除数据卷（将清除所有数据）？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "删除数据卷..."
    docker-compose -f docker/docker-compose.microservices.yml down -v
fi

# 询问是否清理镜像
read -p "是否删除构建的镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "删除镜像..."
    docker-compose -f docker/docker-compose.microservices.yml down --rmi local
fi

# 清理未使用的Docker资源（可选）
read -p "是否清理未使用的Docker资源？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理未使用的Docker资源..."
    docker system prune -f
fi

echo "开发环境已停止！"