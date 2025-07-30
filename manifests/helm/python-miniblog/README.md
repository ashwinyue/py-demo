# Python MiniBlog Helm Chart

这个Helm Chart用于部署Python MiniBlog微服务应用到Kubernetes集群。

## 架构概述

该应用包含以下组件：

- **User Service**: 用户管理服务 (端口: 5001)
- **Blog Service**: 博客管理服务 (端口: 5002)
- **Tyk Gateway**: API网关 (端口: 8080)
- **MySQL**: 数据库服务 (端口: 3306)
- **Redis**: 缓存服务 (端口: 6379)

## 最新更新

### 从Docker Compose配置同步的更改

1. **移除Nacos依赖**: 不再使用Nacos作为服务注册中心
2. **环境变量更新**: 直接在Deployment中配置环境变量，不再使用ConfigMap
3. **数据库配置**: 更新MySQL初始化脚本，创建miniblog数据库和必要的表
4. **Tyk网关配置**: 更新API路径为 `/user-service/` 和 `/blog-service/`
5. **服务发现**: 使用Kubernetes原生服务发现替代Nacos

### 主要配置更改

#### User Service环境变量
```yaml
env:
  SERVICE_NAME: "user-service"
  SERVICE_IP: "0.0.0.0"
  SERVICE_PORT: "5001"
  MYSQL_HOST: "python-miniblog-mysql"
  MYSQL_PORT: "3306"
  MYSQL_USER: "miniblog"
  MYSQL_PASSWORD: "miniblog123"
  MYSQL_DATABASE: "miniblog"
  REDIS_URL: "redis://python-miniblog-redis:6379/0"
  JWT_SECRET_KEY: "your-secret-key-here"
  FLASK_ENV: "production"
  FLASK_CONFIG: "production"
```

#### Blog Service环境变量
```yaml
env:
  SERVICE_NAME: "blog-service"
  SERVICE_IP: "0.0.0.0"
  SERVICE_PORT: "5002"
  DATABASE_URL: "mysql+pymysql://miniblog:miniblog123@python-miniblog-mysql:3306/miniblog"
  MYSQL_HOST: "python-miniblog-mysql"
  MYSQL_PORT: "3306"
  MYSQL_USER: "miniblog"
  MYSQL_PASSWORD: "miniblog123"
  MYSQL_DATABASE: "miniblog"
  REDIS_URL: "redis://python-miniblog-redis:6379/0"
  JWT_SECRET_KEY: "your-secret-key-here"
  USER_SERVICE_URL: "http://python-miniblog-user:5001"
```

#### Tyk Gateway配置
- 镜像版本: `tykio/tyk-gateway:v5.2`
- 监听端口: 8080
- API路径:
  - User Service: `/user-service/` -> `http://python-miniblog-user:5001/`
  - Blog Service: `/blog-service/` -> `http://python-miniblog-blog:5002/`

## 部署说明

### 前置条件

1. Kubernetes集群 (版本 >= 1.19)
2. Helm 3.x
3. kubectl配置正确

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd py-demo
   ```

2. **创建命名空间**
   ```bash
   kubectl create namespace python-miniblog
   ```

3. **安装应用**
   ```bash
   helm install python-miniblog ./helm/python-miniblog --namespace python-miniblog
   ```

4. **检查部署状态**
   ```bash
   kubectl get pods -n python-miniblog
   kubectl get svc -n python-miniblog
   ```

### 使用测试脚本

我们提供了一个自动化测试脚本来验证部署：

```bash
./scripts/test-helm-deployment.sh
```

该脚本会：
- 验证Helm Chart语法
- 执行干运行部署
- 部署应用到Kubernetes
- 测试各个服务的连通性
- 提供访问说明

## 访问应用

### 本地访问

1. **端口转发**
   ```bash
   kubectl port-forward -n python-miniblog svc/python-miniblog-tyk-gateway 8080:8080
   ```

2. **访问服务**
   - Tyk Gateway健康检查: http://localhost:8080/hello
   - User Service: http://localhost:8080/user-service/
   - Blog Service: http://localhost:8080/blog-service/

### 通过Ingress访问

如果启用了Ingress，可以通过配置的域名访问：

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: miniblog.local
      paths:
        - path: /
          pathType: Prefix
```

## 配置说明

### 主要配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `global.namespace` | `python-miniblog` | 部署命名空间 |
| `userService.replicas` | `1` | User Service副本数 |
| `blogService.replicas` | `1` | Blog Service副本数 |
| `mysql.enabled` | `true` | 是否启用MySQL |
| `redis.enabled` | `true` | 是否启用Redis |
| `tyk.enabled` | `true` | 是否启用Tyk Gateway |
| `nacos.enabled` | `false` | 是否启用Nacos (已禁用) |

### 资源配置

每个服务都有默认的资源限制和请求配置，可以根据实际需求调整：

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

### 持久化存储

MySQL和Redis都支持持久化存储：

```yaml
mysql:
  persistence:
    enabled: true
    size: 8Gi
    storageClass: ""

redis:
  persistence:
    enabled: true
    size: 1Gi
    storageClass: ""
```

## 故障排除

### 常见问题

1. **Pod启动失败**
   ```bash
   kubectl describe pod <pod-name> -n python-miniblog
   kubectl logs <pod-name> -n python-miniblog
   ```

2. **服务连接问题**
   ```bash
   kubectl get svc -n python-miniblog
   kubectl get endpoints -n python-miniblog
   ```

3. **数据库连接问题**
   ```bash
   kubectl exec -it <mysql-pod> -n python-miniblog -- mysql -u miniblog -p
   ```

### 日志查看

```bash
# 查看所有Pod日志
kubectl logs -l app.kubernetes.io/instance=python-miniblog -n python-miniblog

# 查看特定服务日志
kubectl logs -l app.kubernetes.io/component=user-service -n python-miniblog
kubectl logs -l app.kubernetes.io/component=blog-service -n python-miniblog
kubectl logs -l app.kubernetes.io/component=tyk-gateway -n python-miniblog
```

## 卸载

```bash
# 卸载应用
helm uninstall python-miniblog -n python-miniblog

# 删除命名空间
kubectl delete namespace python-miniblog
```

## 开发说明

### Chart结构

```
helm/python-miniblog/
├── Chart.yaml              # Chart元数据
├── values.yaml             # 默认配置值
├── templates/              # Kubernetes模板文件
│   ├── deployment.yaml     # 应用部署配置
│   ├── service.yaml        # 服务配置
│   ├── mysql.yaml          # MySQL配置
│   ├── redis.yaml          # Redis配置
│   ├── tyk.yaml            # Tyk Gateway配置
│   ├── tyk-api-definition.yaml  # Tyk API定义
│   ├── tyk-policies.yaml   # Tyk策略配置
│   ├── ingress.yaml        # Ingress配置
│   └── _helpers.tpl        # 模板助手函数
└── README.md               # 本文档
```

### 自定义配置

可以通过创建自定义的values文件来覆盖默认配置：

```bash
helm install python-miniblog ./helm/python-miniblog \
  --namespace python-miniblog \
  --values custom-values.yaml
```

## 版本历史

- **v1.0.0**: 初始版本，基于Docker Compose配置
- **v1.1.0**: 移除Nacos依赖，优化配置结构