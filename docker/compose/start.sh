#!/bin/bash

# Docker Compose 启动脚本
# 支持不同环境配置

set -e

# 默认环境为开发环境
ENV=${1:-development}

# 检查环境配置文件是否存在
ENV_FILE=".env.${ENV}"
if [ ! -f "$ENV_FILE" ]; then
    echo "错误: 环境配置文件 $ENV_FILE 不存在"
    echo "可用环境: development, production"
    exit 1
fi

echo "使用环境配置: $ENV"
echo "配置文件: $ENV_FILE"

# 停止现有服务
echo "停止现有服务..."
docker compose --env-file "$ENV_FILE" down

# 构建并启动服务
echo "构建并启动服务..."
docker compose --env-file "$ENV_FILE" up --build -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态:"
docker compose --env-file "$ENV_FILE" ps

echo "服务启动完成!"
echo "用户服务: http://localhost:$(grep USER_SERVICE_PORT $ENV_FILE | cut -d'=' -f2)"
echo "博客服务: http://localhost:$(grep BLOG_SERVICE_PORT $ENV_FILE | cut -d'=' -f2)"
echo "MySQL: localhost:$(grep MYSQL_PORT $ENV_FILE | cut -d'=' -f2)"
echo "Redis: localhost:$(grep REDIS_PORT $ENV_FILE | cut -d'=' -f2)"