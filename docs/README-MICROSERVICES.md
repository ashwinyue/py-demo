# Python MiniBlog 微服务架构

本项目已重构为微服务架构，使用 Tyk API Gateway 进行统一的 API 管理和认证。

## 架构概览

### 服务组件

1. **用户服务 (User Service)**
   - 端口: 5001
   - 功能: 用户注册、登录、认证、用户管理
   - 路径: `/api/users/*`

2. **博客服务 (Blog Service)**
   - 端口: 5002
   - 功能: 文章管理、评论管理、分类管理
   - 路径: `/api/blogs/*`

3. **API网关 (API Gateway)**
   - 端口: 8000
   - 功能: 请求路由、负载均衡（备用）
   - 状态: 已禁用（使用 Tyk 替代）

4. **Tyk API Gateway**
   - 端口: 8080
   - 功能: API 管理、认证、限流、监控
   - 配置: JWT 认证策略

### 基础设施组件

1. **MySQL 数据库**
   - 端口: 3306
   - 用途: 持久化数据存储

2. **Redis 缓存**
   - 端口: 6379
   - 用途: 缓存、会话存储

3. **Nacos 配置中心**
   - 端口: 8848
   - 用途: 服务发现、配置管理

## 认证架构

### Tyk JWT 认证流程

1. 用户通过用户服务登录获取 JWT 令牌
2. 客户端在请求头中携带 `Authorization: Bearer <token>`
3. Tyk Gateway 验证 JWT 令牌的有效性
4. 验证通过后，请求转发到相应的微服务
5. 微服务从令牌中提取用户信息（无需再次验证）

### API 路由配置

**通过Tyk API Gateway的路由映射：**

```
/user-service/*  -> 用户服务:5001/api/* (需要JWT认证)
/blog-service/*  -> 博客服务:5002/api/* (部分接口需要JWT认证)
```

**具体路径映射：**

| 网关路径 | 目标服务 | 实际路径 | 认证要求 |
|----------|----------|----------|----------|
| `/user-service/users` | 用户服务 | `/api/users` | JWT |
| `/user-service/auth/login` | 用户服务 | `/api/auth/login` | 无 |
| `/user-service/auth/register` | 用户服务 | `/api/auth/register` | 无 |
| `/blog-service/posts` | 博客服务 | `/api/posts` | 读取无需认证，写入需要JWT |
| `/blog-service/categories` | 博客服务 | `/api/categories` | 读取无需认证，写入需要JWT |
| `/blog-service/tags` | 博客服务 | `/api/tags` | 读取无需认证，写入需要JWT |
| `/blog-service/comments` | 博客服务 | `/api/comments` | JWT |

**健康检查和监控端点：**

```
/user-service/healthz   -> 用户服务健康检查
/blog-service/healthz   -> 博客服务健康检查
/user-service/metrics   -> 用户服务指标
/blog-service/metrics   -> 博客服务指标
/user-service/docs/     -> 用户服务API文档
/blog-service/docs/     -> 博客服务API文档
```

## 部署指南

### 前置要求

- Kubernetes 集群
- Helm 3.x
- Docker
- kubectl

### 快速部署

1. **构建和部署**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **手动部署**
   ```bash
   # 创建命名空间
   kubectl create namespace miniblog
   
   # 构建镜像
   docker build -t python-miniblog-user-service:latest ./services/user-service
   docker build -t python-miniblog-blog-service:latest ./services/blog-service
   docker build -t python-miniblog-gateway:latest ./services/api-gateway
   
   # 部署 Helm Chart
   helm install python-miniblog ./helm/python-miniblog -n miniblog
   ```

### 配置说明

#### Tyk 配置

- **Gateway**: 启用，处理所有 API 请求
- **Dashboard**: 禁用，使用配置文件管理
- **认证策略**: JWT 验证，支持用户和管理员角色
- **API 定义**: 分别为用户服务和博客服务配置路由

#### 环境变量

主要环境变量在 `values.yaml` 中配置：

```yaml
# 数据库配置
DATABASE_URL: mysql://user:password@mysql:3306/miniblog

# Redis 配置
REDIS_URL: redis://redis:6379/0

# JWT 配置
JWT_SECRET_KEY: your-secret-key

# Nacos 配置
NACOS_SERVER_ADDR: nacos:8848
```

## 开发指南

### 本地开发

1. **启动基础设施**
   ```bash
   docker-compose up -d mysql redis nacos
   ```

2. **启动微服务**
   ```bash
   # 用户服务
   cd services/user-service
   python app.py
   
   # 博客服务
   cd services/blog-service
   python app.py
   ```

3. **启动 Tyk（可选）**
   ```bash
   # 使用 Docker 运行 Tyk
   docker run -d -p 8080:8080 \
     -v $(pwd)/helm/python-miniblog/templates/tyk-api-definition.yaml:/opt/tyk-gateway/apps/api-definition.json \
     tykio/tyk-gateway:latest
   ```

### API 测试

1. **用户注册**
   ```bash
   curl -X POST http://localhost:8080/api/users/register \
     -H "Content-Type: application/json" \
     -d '{"username":"test","email":"test@example.com","password":"password123"}'
   ```

2. **用户登录**
   ```bash
   curl -X POST http://localhost:8080/api/users/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"password123"}'
   ```

3. **访问受保护的接口**
   ```bash
   curl -X GET http://localhost:8080/api/users/profile \
     -H "Authorization: Bearer <your-jwt-token>"
   ```

## 监控和日志

### 查看服务状态

```bash
# 查看所有 Pod
kubectl get pods -n miniblog

# 查看服务
kubectl get svc -n miniblog

# 查看 Ingress
kubectl get ingress -n miniblog
```

### 查看日志

```bash
# 用户服务日志
kubectl logs -f deployment/python-miniblog-user-service -n miniblog

# 博客服务日志
kubectl logs -f deployment/python-miniblog-blog-service -n miniblog

# Tyk 网关日志
kubectl logs -f deployment/python-miniblog-tyk-gateway -n miniblog
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查环境变量配置
   - 确认数据库连接
   - 查看 Pod 日志

2. **认证失败**
   - 检查 JWT 密钥配置
   - 确认 Tyk 策略配置
   - 验证令牌格式

3. **服务间通信失败**
   - 检查服务发现配置
   - 确认网络策略
   - 验证端口配置

### 调试命令

```bash
# 进入 Pod 调试
kubectl exec -it <pod-name> -n miniblog -- /bin/bash

# 查看配置
kubectl describe configmap -n miniblog

# 查看事件
kubectl get events -n miniblog --sort-by='.lastTimestamp'
```

## 扩展和优化

### 性能优化

1. **水平扩展**
   ```bash
   kubectl scale deployment python-miniblog-user-service --replicas=3 -n miniblog
   ```

2. **资源限制**
   - 在 `values.yaml` 中调整 CPU 和内存限制
   - 配置 HPA（水平 Pod 自动扩展）

3. **缓存策略**
   - 优化 Redis 缓存配置
   - 实现应用级缓存

### 安全加固

1. **网络策略**
   - 配置 Kubernetes NetworkPolicy
   - 限制服务间通信

2. **密钥管理**
   - 使用 Kubernetes Secrets
   - 集成外部密钥管理系统

3. **RBAC**
   - 配置细粒度的角色权限
   - 实现 API 级别的访问控制

## 版本历史

- **v2.0.0**: 微服务架构重构
  - 拆分为用户服务和博客服务
  - 集成 Tyk API Gateway
  - 简化认证流程
  - 优化部署配置

- **v1.0.0**: 单体应用架构
  - 基础功能实现
  - 单一服务部署