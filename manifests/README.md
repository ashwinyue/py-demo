# 部署配置目录

本目录包含了项目的所有部署相关配置文件，按照不同的部署方式进行组织。

## 目录结构

```
deployments/
├── README.md          # 本说明文件
├── helm/              # Helm Chart 部署配置
│   ├── README.md      # Helm 部署说明
│   └── python-miniblog/  # Helm Chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-development.yaml
│       ├── values-production.yaml
│       ├── values-testing.yaml
│       └── templates/ # Kubernetes 模板文件
└── kubernetes/        # 原始 Kubernetes 配置文件
    ├── namespace.yaml      # 命名空间
    ├── mysql.yaml          # MySQL 数据库
    ├── redis.yaml          # Redis 缓存
    ├── user-service.yaml   # 用户服务
    ├── blog-service.yaml   # 博客服务
    └── kustomization.yaml  # Kustomize 配置
```

## 部署方式

### 1. Helm 部署（推荐）

Helm 是 Kubernetes 的包管理器，提供了更灵活的配置管理和版本控制。

```bash
# 使用 Helm 部署
make helm-install

# 或者使用脚本部署
make helm-deploy

# 查看部署状态
make helm-status

# 卸载部署
make helm-uninstall
```

**优势：**
- 支持多环境配置（开发、测试、生产）
- 版本管理和回滚
- 参数化配置
- 依赖管理

### 2. 原始 Kubernetes 配置

使用原始的 Kubernetes YAML 文件进行部署，适合简单场景或学习目的。

```bash
# 使用 kubectl 直接部署
kubectl apply -f deployments/kubernetes/

# 或者使用 kustomize
kubectl apply -k deployments/kubernetes/

# 使用 make 命令部署
make kubernetes-deploy
```

**优势：**
- 配置直观，易于理解
- 无额外依赖
- 适合学习和调试

## 环境配置

### 开发环境
- 使用 `values-development.yaml`
- 单副本部署
- 开启调试模式
- 使用 NodePort 服务类型

### 测试环境
- 使用 `values-testing.yaml`
- 多副本部署
- 启用健康检查
- 资源限制较宽松

### 生产环境
- 使用 `values-production.yaml`
- 高可用部署
- 严格的资源限制
- 使用 LoadBalancer 或 Ingress
- 启用监控和日志

## 服务访问

部署完成后，可以通过以下方式访问服务：

### NodePort 方式（默认）
- 用户服务：`http://localhost:30001`
- 博客服务：`http://localhost:30002`

### 端口转发方式
```bash
# 设置端口转发
make kubernetes-port-forward

# 然后访问
# 用户服务：http://localhost:5001
# 博客服务：http://localhost:5002
```

## 监控和调试

```bash
# 查看部署状态
make kubernetes-status

# 查看服务日志
make kubernetes-logs

# 测试 API 接口
make test-api-kubernetes
```

## 配置说明

### 环境变量
- `DATABASE_URL`: MySQL 数据库连接字符串
- `REDIS_HOST`: Redis 服务器地址
- `USER_SERVICE_URL`: 用户服务地址（博客服务使用）

### 资源配置
- **用户服务**: 128Mi-256Mi 内存，100m-200m CPU
- **博客服务**: 128Mi-256Mi 内存，100m-200m CPU
- **MySQL**: 256Mi-512Mi 内存，200m-500m CPU
- **Redis**: 64Mi-128Mi 内存，50m-100m CPU

### 健康检查
- **存活探针**: `/health` 端点，30秒后开始，每10秒检查
- **就绪探针**: `/health` 端点，5秒后开始，每5秒检查

## 故障排除

### 常见问题

1. **Pod 启动失败**
   ```bash
   kubectl describe pod <pod-name> -n miniblog
   kubectl logs <pod-name> -n miniblog
   ```

2. **服务无法访问**
   ```bash
   kubectl get svc -n miniblog
   kubectl get endpoints -n miniblog
   ```

3. **镜像拉取失败**
   - 确保镜像已构建：`make docker-build-images`
   - Kind 集群需要加载镜像：`make kind-load-images`

4. **数据库连接失败**
   - 检查 MySQL Pod 状态
   - 验证环境变量配置
   - 检查网络策略

### 调试命令

```bash
# 进入 Pod 调试
kubectl exec -it <pod-name> -n miniblog -- /bin/bash

# 查看事件
kubectl get events -n miniblog --sort-by='.lastTimestamp'

# 查看资源使用情况
kubectl top pods -n miniblog
kubectl top nodes
```