# Nacos配置管理指南

本项目已集成Nacos配置管理功能，支持从Nacos动态获取和更新业务配置。

## 功能特性

- ✅ 动态配置加载：应用启动时自动从Nacos加载配置
- ✅ 配置热更新：配置变更时自动更新应用配置，无需重启
- ✅ 配置缓存：本地缓存配置，提高访问性能
- ✅ 多环境支持：通过命名空间区分不同环境
- ✅ 配置分组：按业务模块组织配置
- ✅ 错误处理：配置加载失败时使用默认配置

## 配置结构

### 配置分类

项目中的配置按以下方式组织：

1. **common-config**: 通用配置，所有服务共享
2. **database-config**: 数据库相关配置
3. **redis-config**: Redis缓存配置
4. **user-service-config**: 用户服务专用配置
5. **blog-service-config**: 博客服务专用配置

### 配置映射

Nacos配置项与Flask应用配置的映射关系：

| Nacos配置项 | Flask配置项 | 说明 |
|------------|------------|------|
| database_url | SQLALCHEMY_DATABASE_URI | 数据库连接URL |
| redis_host | REDIS_HOST | Redis主机地址 |
| redis_port | REDIS_PORT | Redis端口 |
| jwt_secret_key | JWT_SECRET_KEY | JWT密钥 |
| jwt_expires_hours | JWT_ACCESS_TOKEN_EXPIRES | JWT过期时间 |
| log_level | LOG_LEVEL | 日志级别 |
| cors_origins | CORS_ORIGINS | CORS允许的源 |

## 使用方法

### 1. 环境变量配置

确保设置以下环境变量：

```bash
# Nacos服务器配置
NACOS_HOST=localhost
NACOS_PORT=8848
NACOS_NAMESPACE=public
NACOS_USERNAME=nacos
NACOS_PASSWORD=nacos

# 服务名称
SERVICE_NAME=user-service  # 或 blog-service
```

### 2. 发布配置到Nacos

使用配置管理脚本发布示例配置：

```bash
# 发布所有示例配置
python scripts/manage_nacos_config.py publish-examples --group DEFAULT_GROUP

# 发布单个配置
python scripts/manage_nacos_config.py publish --data-id common-config --group DEFAULT_GROUP --file configs/common.json

# 发布配置内容
python scripts/manage_nacos_config.py publish --data-id test-config --group DEFAULT_GROUP --content '{"key": "value"}'
```

### 3. 查看和管理配置

```bash
# 获取配置
python scripts/manage_nacos_config.py get --data-id common-config --group DEFAULT_GROUP

# 删除配置
python scripts/manage_nacos_config.py remove --data-id test-config --group DEFAULT_GROUP

# 列出配置（需要使用Nacos控制台）
python scripts/manage_nacos_config.py list --group DEFAULT_GROUP
```

### 4. 在代码中使用配置管理器

```python
from app.utils.nacos_config import get_nacos_config_manager

# 获取配置管理器实例
config_manager = get_nacos_config_manager()

# 获取配置
config_data = config_manager.get_config('common-config')

# 发布配置
config_manager.publish_config('new-config', '{"key": "value"}')

# 删除配置
config_manager.remove_config('old-config')
```

## 配置示例

### 通用配置 (common-config)

```json
{
  "log_level": "INFO",
  "cors_origins": "http://localhost:3000,http://localhost:8080",
  "jwt_secret_key": "your-jwt-secret-key-here",
  "jwt_expires_hours": 24
}
```

### 数据库配置 (database-config)

```json
{
  "database_url": "mysql+pymysql://root:password@mysql:3306/miniblog",
  "database_pool_size": {
    "pool_size": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": true,
    "max_overflow": 30
  }
}
```

### 用户服务配置 (user-service-config)

```json
{
  "password_min_length": 8,
  "password_require_special_chars": true,
  "max_login_attempts": 5,
  "account_lockout_duration": 1800,
  "email_verification_required": true,
  "session_timeout_minutes": 30,
  "admin_emails": ["admin@example.com"],
  "user_registration_enabled": true
}
```

### 博客服务配置 (blog-service-config)

```json
{
  "posts_per_page": 10,
  "max_posts_per_page": 50,
  "cache_posts_timeout": 600,
  "max_post_title_length": 200,
  "max_post_content_length": 50000,
  "allow_html_in_posts": false,
  "user_service_timeout": 10
}
```

## 配置热更新

当Nacos中的配置发生变更时，应用会自动接收到通知并更新本地配置，无需重启服务。

### 监听机制

- 应用启动时自动为所有配置项添加监听器
- 配置变更时触发回调函数
- 自动重新加载配置并更新Flask应用配置
- 记录配置变更日志

## 最佳实践

### 1. 配置组织

- 按功能模块组织配置（数据库、缓存、业务等）
- 使用有意义的配置ID命名
- 为配置添加描述信息

### 2. 环境管理

- 使用不同的命名空间区分环境（dev、test、prod）
- 敏感配置使用加密存储
- 定期备份重要配置

### 3. 版本控制

- 重要配置变更前先备份
- 记录配置变更历史
- 测试配置变更的影响

### 4. 监控告警

- 监控配置加载状态
- 配置变更时发送通知
- 记录配置访问日志

## 故障排查

### 常见问题

1. **配置加载失败**
   - 检查Nacos服务器连接
   - 验证命名空间和组名配置
   - 确认配置是否存在

2. **配置热更新不生效**
   - 检查监听器是否正常添加
   - 查看应用日志中的配置变更记录
   - 验证配置映射关系

3. **配置格式错误**
   - 确保JSON格式正确
   - 检查配置项数据类型
   - 验证必需配置项是否存在

### 日志查看

配置管理相关的日志会记录在应用日志中，包括：

- 配置加载成功/失败
- 配置变更通知
- 配置更新结果
- 错误信息和异常

## 迁移指南

如果要将现有的环境变量配置迁移到Nacos：

1. 分析现有配置项
2. 按模块组织配置
3. 创建对应的Nacos配置
4. 测试配置加载
5. 逐步迁移配置项
6. 移除环境变量配置

## 安全注意事项

- 敏感配置（密码、密钥）应使用Nacos的加密功能
- 限制Nacos访问权限
- 定期更新访问凭证
- 监控配置访问日志