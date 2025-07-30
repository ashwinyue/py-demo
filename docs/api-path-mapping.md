# API 路径映射分析

本文档分析项目中的API接口路径与Helm配置中的路径映射关系，确保配置的一致性。

## 当前路径映射问题

### 1. Tyk Gateway 配置问题

**Helm配置中的路径映射：**
- 用户服务：`/user-service/` -> `http://python-miniblog-user:5001/api/v1/`
- 博客服务：`/blog-service/` -> `http://python-miniblog-blog:5002/api/v1/`

**实际服务中的API路径：**
- 用户服务：`/api/v1/users/*`
- 博客服务：`/api/posts/*`, `/api/categories/*`, `/api/tags/*`, `/api/comments/*`

### 2. 路径不匹配分析

#### 用户服务路径问题
- **Tyk配置**：将 `/user-service/*` 转发到 `http://python-miniblog-user:5001/api/v1/*`
- **实际API**：用户服务的API蓝图注册在 `/api/v1` 路径下
- **问题**：路径映射正确，但需要确认服务注册的蓝图路径

#### 博客服务路径问题
- **Tyk配置**：将 `/blog-service/*` 转发到 `http://python-miniblog-blog:5002/api/v1/*`
- **实际API**：博客服务的API蓝图注册在 `/api` 路径下（没有v1版本）
- **问题**：目标URL中的 `/api/v1/` 路径与实际的 `/api/` 不匹配

## 具体API端点分析

### 用户服务 API 端点

| 功能 | HTTP方法 | 实际路径 | Tyk路径 | 状态 |
|------|----------|----------|---------|------|
| 获取用户列表 | GET | `/api/users` | `/user-service/users` | ✅ 已修复 |
| 创建用户 | POST | `/api/users` | `/user-service/users` | ✅ 已修复 |
| 获取用户详情 | GET | `/api/users/{id}` | `/user-service/users/{id}` | ✅ 已修复 |
| 更新用户 | PUT | `/api/users/{id}` | `/user-service/users/{id}` | ✅ 已修复 |
| 删除用户 | DELETE | `/api/users/{id}` | `/user-service/users/{id}` | ✅ 已修复 |
| 搜索用户 | GET | `/api/users/search` | `/user-service/users/search` | ✅ 已修复 |
| 用户登录 | POST | `/api/auth/login` | `/user-service/auth/login` | ✅ 已修复 |
| 用户注册 | POST | `/api/auth/register` | `/user-service/auth/register` | ✅ 已修复 |

### 博客服务 API 端点

| 功能 | HTTP方法 | 实际路径 | Tyk路径 | 状态 |
|------|----------|----------|---------|------|
| 获取文章列表 | GET | `/api/posts` | `/blog-service/posts` | ✅ 已修复 |
| 创建文章 | POST | `/api/posts` | `/blog-service/posts` | ✅ 已修复 |
| 获取文章详情 | GET | `/api/posts/{id}` | `/blog-service/posts/{id}` | ✅ 已修复 |
| 更新文章 | PUT | `/api/posts/{id}` | `/blog-service/posts/{id}` | ✅ 已修复 |
| 删除文章 | DELETE | `/api/posts/{id}` | `/blog-service/posts/{id}` | ✅ 已修复 |
| 点赞文章 | POST | `/api/posts/{id}/like` | `/blog-service/posts/{id}/like` | ✅ 已修复 |
| 获取分类列表 | GET | `/api/categories` | `/blog-service/categories` | ✅ 已修复 |
| 获取标签列表 | GET | `/api/tags` | `/blog-service/tags` | ✅ 已修复 |
| 获取评论列表 | GET | `/api/comments` | `/blog-service/comments` | ✅ 已修复 |

## 已完成的修复

### ✅ 统一API路径前缀

**修改内容：** 统一了两个服务的API路径前缀，移除了版本号差异

**用户服务修改：**
- 文件：`services/user-service/app/api/__init__.py`
- 修改：移除API蓝图的 `/v1` 前缀，统一为 `/api`
- 文件：`helm/python-miniblog/templates/tyk-api-definition.yaml`
- 修改：用户服务的 `target_url` 从 `http://python-miniblog-user:5001/api/v1/` 改为 `http://python-miniblog-user:5001/api/`

**博客服务修改：**
- 文件：`helm/python-miniblog/templates/tyk-api-definition.yaml`
- 修改：博客服务的 `target_url` 从 `http://python-miniblog-blog:5002/api/v1/` 改为 `http://python-miniblog-blog:5002/api/`

**修复结果：** 现在两个服务都使用统一的 `/api/` 路径前缀，Tyk网关能够正确转发所有请求

### ✅ 更新文档

1. **主README文档** (`README.md`)：
   - 更新了API端点说明，区分网关路径和直接访问路径
   - 添加了完整的API端点列表
   - 明确标注了认证要求

2. **微服务架构文档** (`docs/README-MICROSERVICES.md`)：
   - 更新了API路由配置说明
   - 添加了详细的路径映射表
   - 包含了健康检查和监控端点信息

3. **API路径映射文档** (`docs/api-path-mapping.md`)：
   - 新建了专门的路径映射分析文档
   - 详细记录了问题分析和修复过程
   - 提供了完整的API端点对比表

## 健康检查和服务发现端点

### 通用端点

| 端点 | 用户服务 | 博客服务 | 说明 |
|------|----------|----------|------|
| 健康检查 | `/healthz` | `/healthz` | 服务健康状态 |
| 服务信息 | `/` | `/` | 服务基本信息 |
| 指标监控 | `/metrics` | `/metrics` | 服务运行指标 |
| API文档 | `/docs/` | `/docs/` | Swagger文档 |

## 认证和授权

### JWT认证配置

- **认证头**：`Authorization: Bearer <token>`
- **JWT签名方法**：HMAC
- **用户身份字段**：`user_id`
- **策略字段**：`pol`
- **默认策略**：`jwt_policy`

### 权限要求

| API类型 | 认证要求 | 权限要求 |
|---------|----------|----------|
| 用户注册/登录 | 无 | 无 |
| 用户管理 | JWT | 用户本人或管理员 |
| 文章查看 | 无（公开文章） | 无 |
| 文章管理 | JWT | 作者本人或管理员 |
| 评论管理 | JWT | 评论者本人或管理员 |

## 更新记录

- **2024-07-30**: 初始版本，分析当前路径映射问题
- **2024-07-30**: 修复博客服务路径映射问题，更新相关文档
  - 修复了Tyk配置中的博客服务target_url路径
  - 更新了主README和微服务架构文档
  - 所有API路径映射现已正确配置

## 相关文档

- [微服务架构说明](README-MICROSERVICES.md)
- [项目结构文档](project-structure.md)
- [主要README](../README.md)