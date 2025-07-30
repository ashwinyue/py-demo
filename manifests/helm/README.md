# Helm 环境配置说明

本项目支持多环境部署，包括开发环境、测试环境和生产环境。每个环境都有独立的配置文件和部署参数。

## 环境配置文件

### 开发环境 (Development)
- **配置文件**: `values-development.yaml`
- **命名空间**: `miniblog-dev`
- **特点**:
  - 单副本部署
  - 较低的资源配置
  - 禁用持久化存储
  - 使用开发环境密钥
  - 简化的健康检查配置

### 测试环境 (Testing)
- **配置文件**: `values-testing.yaml`
- **命名空间**: `miniblog-test`
- **特点**:
  - 双副本部署
  - 中等资源配置
  - 启用持久化存储
  - 使用测试环境密钥
  - 启用Tyk API网关进行测试

### 生产环境 (Production)
- **配置文件**: `values-production.yaml`
- **命名空间**: `miniblog`
- **特点**:
  - 三副本部署
  - 高资源配置
  - 启用持久化存储
  - 使用生产环境密钥
  - 完整的安全配置
  - Pod反亲和性配置
  - 启用HTTPS和SSL证书

## 部署命令

### 使用部署脚本 (推荐)

```bash
# 部署到开发环境
./deploy.sh development install

# 部署到测试环境
./deploy.sh testing install

# 部署到生产环境
./deploy.sh production install

# 升级现有部署
./deploy.sh production upgrade

# 查看部署状态
./deploy.sh production status

# 卸载部署
./deploy.sh production uninstall

# 执行干运行
./deploy.sh production dry-run
```

### 直接使用 Helm 命令

```bash
# 开发环境
helm upgrade --install python-miniblog-dev ./python-miniblog \
  --namespace miniblog-dev \
  --values ./python-miniblog/values-development.yaml \
  --create-namespace

# 测试环境
helm upgrade --install python-miniblog-test ./python-miniblog \
  --namespace miniblog-test \
  --values ./python-miniblog/values-testing.yaml \
  --create-namespace

# 生产环境
helm upgrade --install python-miniblog ./python-miniblog \
  --namespace miniblog \
  --values ./python-miniblog/values-production.yaml \
  --create-namespace
```

## 环境差异对比

| 配置项 | 开发环境 | 测试环境 | 生产环境 |
|--------|----------|----------|----------|
| 副本数 | 1 | 2 | 3 |
| CPU限制 | 200m | 500m | 1000m |
| 内存限制 | 256Mi | 512Mi | 1Gi |
| 持久化存储 | 禁用 | 启用 | 启用 |
| 存储大小 | - | 10Gi | 20Gi |
| 安全上下文 | 基础 | 中等 | 完整 |
| Ingress TLS | 禁用 | 禁用 | 启用 |
| API网关 | 禁用 | 启用 | 启用 |
| Pod反亲和性 | 禁用 | 部分 | 完整 |

## ConfigMap 配置

所有环境都启用了 ConfigMap 配置，通过 `configMap.enabled: true` 控制。ConfigMap 包含以下配置:

- 数据库连接配置
- Redis 连接配置
- JWT 密钥配置
- 应用程序配置
- 服务发现配置

## 安全注意事项

### 生产环境部署前必须修改的配置:

1. **数据库密码**: 修改 `mysql.auth.password` 和相关环境变量
2. **JWT密钥**: 修改 `JWT_SECRET_KEY` 和 `SECRET_KEY`
3. **域名配置**: 修改 `ingress.hosts` 中的域名
4. **TLS证书**: 配置正确的证书颁发者和域名
5. **Tyk密钥**: 修改 `TYK_GW_SECRET`

### 推荐的安全实践:

1. 使用 Kubernetes Secrets 存储敏感信息
2. 启用 RBAC 权限控制
3. 配置网络策略限制Pod间通信
4. 定期更新镜像和依赖
5. 启用审计日志

## 监控和日志

### 健康检查
- 所有服务都配置了存活性和就绪性探针
- 探针路径: `/healthz`
- 不同环境有不同的超时和间隔配置

### 日志收集
建议集成以下工具:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Prometheus + Grafana
- Jaeger (分布式追踪)

## 故障排除

### 常见问题

1. **Pod 启动失败**
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   kubectl logs <pod-name> -n <namespace>
   ```

2. **服务无法访问**
   ```bash
   kubectl get svc -n <namespace>
   kubectl get ingress -n <namespace>
   ```

3. **存储问题**
   ```bash
   kubectl get pv
   kubectl get pvc -n <namespace>
   ```

### 调试命令

```bash
# 查看所有资源
kubectl get all -n <namespace>

# 查看事件
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# 进入Pod调试
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# 查看配置
kubectl get configmap -n <namespace> -o yaml
```

## 升级和回滚

### 升级部署
```bash
# 使用脚本升级
./deploy.sh production upgrade

# 或使用helm命令
helm upgrade python-miniblog ./python-miniblog \
  --namespace miniblog \
  --values ./python-miniblog/values-production.yaml
```

### 回滚部署
```bash
# 查看历史版本
helm history python-miniblog -n miniblog

# 回滚到上一个版本
helm rollback python-miniblog -n miniblog

# 回滚到指定版本
helm rollback python-miniblog 2 -n miniblog
```

## 性能优化建议

1. **资源配置**: 根据实际负载调整CPU和内存配置
2. **副本数量**: 根据流量模式调整副本数
3. **存储优化**: 选择合适的存储类和大小
4. **网络优化**: 配置适当的服务网格
5. **缓存策略**: 优化Redis配置和使用模式