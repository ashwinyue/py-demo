# 微服务架构设计方案

## 概述

将当前的单体博客应用重构为微服务架构，分离用户中心和博客服务，使用Nacos作为注册中心，实现服务发现和配置管理。

## 微服务拆分方案

### 1. 用户中心服务 (User Service)

**职责范围：**
- 用户注册、登录、认证
- 用户信息管理（CRUD）
- 用户权限管理
- 用户会话管理

**API端点：**
- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `GET /api/users/{id}` - 获取用户详情
- `PUT /api/users/{id}` - 更新用户信息
- `DELETE /api/users/{id}` - 删除用户
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/profile` - 获取当前用户信息

**数据库表：**
- `users` - 用户基本信息
- `user_sessions` - 用户会话（可选）

### 2. 博客服务 (Blog Service)

**职责范围：**
- 文章管理（CRUD）
- 文章分类和标签
- 文章搜索和分页
- 文章统计

**API端点：**
- `GET /api/posts` - 获取文章列表
- `POST /api/posts` - 创建文章
- `GET /api/posts/{id}` - 获取文章详情
- `PUT /api/posts/{id}` - 更新文章
- `DELETE /api/posts/{id}` - 删除文章
- `GET /api/users/{user_id}/posts` - 获取用户的文章列表

**数据库表：**
- `posts` - 文章信息
- `categories` - 分类（扩展）
- `tags` - 标签（扩展）

### 3. API网关服务 (API Gateway)

**职责范围：**
- 请求路由和负载均衡
- 统一认证和授权
- 限流和熔断
- 日志和监控

**使用Tyk Gateway实现**

## 技术架构

### 服务注册与发现
- **注册中心**: Nacos
- **配置中心**: Nacos Config
- **服务发现**: Nacos Discovery

### 数据存储
- **用户中心**: 独立MySQL数据库
- **博客服务**: 独立MySQL数据库
- **缓存**: 共享Redis集群

### 通信方式
- **同步通信**: HTTP/REST API
- **异步通信**: 消息队列（可选，后续扩展）

## 项目结构

```
py-demo-microservices/
├── services/
│   ├── user-service/           # 用户中心服务
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── api/
│   │   │   │   ├── users.py
│   │   │   │   └── auth.py
│   │   │   └── extensions.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── main.py
│   │
│   ├── blog-service/           # 博客服务
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── api/
│   │   │   │   └── posts.py
│   │   │   └── extensions.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── main.py
│   │
│   └── common/                 # 共享组件
│       ├── __init__.py
│       ├── nacos_client.py
│       ├── redis_client.py
│       └── utils.py
│
├── helm/
│   ├── user-service/           # 用户服务Helm Chart
│   ├── blog-service/           # 博客服务Helm Chart
│   └── microservices/          # 整体部署Chart
│
├── docker-compose.yml          # 本地开发环境
├── README.md
└── docs/
    ├── api-design.md
    └── deployment.md
```

## 服务间通信

### 1. 用户验证流程
1. 客户端请求 → API Gateway
2. API Gateway → 用户中心服务验证token
3. 验证成功后，API Gateway路由到目标服务

### 2. 博客服务获取用户信息
1. 博客服务通过Nacos发现用户中心服务
2. 调用用户中心服务API获取用户信息
3. 缓存用户信息到Redis（可选）

## 部署架构

### Kubernetes部署
```
┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   Tyk Gateway   │
│   Controller    │────│   (API Gateway) │
└─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼─────┐
        │ User Service │ │ Blog Service│ │   Nacos   │
        │   (Pod)      │ │   (Pod)     │ │  (Pod)    │
        └──────────────┘ └─────────────┘ └───────────┘
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼─────┐
        │ User MySQL   │ │ Blog MySQL  │ │   Redis   │
        │   (Pod)      │ │   (Pod)     │ │  (Pod)    │
        └──────────────┘ └─────────────┘ └───────────┘
```

## 迁移步骤

### 阶段1：准备工作
1. 创建微服务项目结构
2. 拆分数据模型和API
3. 配置Nacos服务注册

### 阶段2：服务开发
1. 开发用户中心服务
2. 开发博客服务
3. 实现服务间通信

### 阶段3：部署和测试
1. 创建Helm Charts
2. 配置API Gateway路由
3. 端到端测试

### 阶段4：数据迁移
1. 数据库拆分
2. 数据迁移脚本
3. 生产环境部署

## 优势

1. **独立部署**: 每个服务可以独立开发、测试和部署
2. **技术栈灵活**: 不同服务可以使用不同的技术栈
3. **扩展性**: 可以根据负载独立扩展不同服务
4. **故障隔离**: 单个服务故障不会影响整个系统
5. **团队协作**: 不同团队可以负责不同的服务

## 注意事项

1. **数据一致性**: 需要处理分布式事务问题
2. **服务发现**: 确保服务注册和发现的可靠性
3. **监控和日志**: 需要统一的监控和日志收集
4. **网络延迟**: 服务间调用会增加网络延迟
5. **复杂性**: 系统整体复杂性会增加