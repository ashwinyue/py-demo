#!/bin/bash

# 测试修复后的调用链路
# 外部请求 → Ingress → Tyk Gateway → Python API Server

echo "=== 测试博客项目调用链路 ==="
echo

# 设置变量
HOST="python-miniblog.local"
BASE_URL="http://${HOST}"

echo "1. 测试健康检查端点 (通过完整调用链路)"
echo "请求路径: ${BASE_URL}/healthz"
echo "预期调用链路: 外部请求 → Ingress → Tyk Gateway → Python API Server"
echo

# 测试健康检查
curl -H "Host: ${HOST}" -s "${BASE_URL}/healthz" | jq . 2>/dev/null || curl -H "Host: ${HOST}" -s "${BASE_URL}/healthz"
echo
echo

echo "2. 测试博客API端点"
echo "请求路径: ${BASE_URL}/api/posts"
echo

# 测试博客API
curl -H "Host: ${HOST}" -s "${BASE_URL}/api/posts" | jq . 2>/dev/null || curl -H "Host: ${HOST}" -s "${BASE_URL}/api/posts"
echo
echo

echo "3. 测试Tyk Gateway直接访问 (验证网关正常运行)"
echo "注意: 这是直接访问Tyk Gateway，不经过Ingress"
echo

# 如果在集群内，可以直接测试Tyk Gateway
echo "如果在Kubernetes集群内，可以运行:"
echo "kubectl exec -it <pod-name> -- curl http://python-miniblog-tyk-gateway:8080/healthz"
echo

echo "=== 调用链路测试完成 ==="
echo
echo "修复说明:"
echo "1. Ingress现在正确路由到Tyk Gateway (端口8080)"
echo "2. Tyk Gateway配置了API定义，将请求转发到Python API Server (端口5000)"
echo "3. 完整调用链路: 外部请求 → Ingress → Tyk Gateway → Python API Server"
echo
echo "如果测试失败，请检查:"
echo "- /etc/hosts 是否配置了 python-miniblog.local"
echo "- Kubernetes集群是否正常运行"
echo "- 所有Pod是否处于Ready状态"