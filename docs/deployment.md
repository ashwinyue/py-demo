# 部署配置指南

本文档描述了Mini Blog项目在生产环境中的部署配置要求。

## 环境要求

### 必需服务

1. **MySQL 8.0+**
   - 生产数据库
   - 测试数据库（用于测试环境）

2. **Redis 6.0+**
   - 缓存服务
   - 会话存储

3. **Nacos 2.0+**
   - 配置中心
   - 服务发现

## 环境变量配置

### 必需环境变量

所有环境变量都是必需的，没有默认值：

```bash
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-here-change-this
FLASK_APP=miniblog.py
FLASK_DEBUG=false

# MySQL数据库配置
DATABASE_URL=mysql+pymysql://username:password@mysql-host:3306/miniblog

# 测试数据库配置（测试环境）
TEST_DATABASE_URL=mysql+pymysql://username:password@mysql-host:3306/miniblog_test

# Redis配置
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_DB=0

# Nacos配置
NACOS_HOST=nacos-host
NACOS_PORT=8848
NACOS_NAMESPACE=production

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/miniblog.log
```

### 配置说明

#### SECRET_KEY
- **必需**: 是
- **说明**: Flask应用的密钥，用于会话加密
- **要求**: 至少32个字符的随机字符串
- **生成方法**: `python -c "import secrets; print(secrets.token_hex(32))"`

#### DATABASE_URL
- **必需**: 是
- **格式**: `mysql+pymysql://username:password@host:port/database`
- **说明**: MySQL数据库连接字符串
- **注意**: 数据库必须预先创建

#### TEST_DATABASE_URL
- **必需**: 测试环境必需
- **格式**: 同DATABASE_URL
- **说明**: 测试专用数据库，与生产数据库分离

#### REDIS_HOST
- **必需**: 是
- **说明**: Redis服务器地址
- **端口**: 默认6379，可通过REDIS_PORT配置

#### NACOS_HOST
- **必需**: 是
- **说明**: Nacos服务器地址
- **端口**: 默认8848，可通过NACOS_PORT配置

## 数据库设置

### MySQL配置要求

```sql
-- 创建数据库
CREATE DATABASE miniblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE miniblog_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER 'miniblog'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON miniblog.* TO 'miniblog'@'%';
GRANT ALL PRIVILEGES ON miniblog_test.* TO 'miniblog'@'%';
FLUSH PRIVILEGES;
```

### 连接池配置

应用已配置了MySQL连接池优化：

- `pool_pre_ping`: 连接前检查连接有效性
- `pool_recycle`: 300秒后回收连接
- `pool_timeout`: 连接超时时间
- `max_overflow`: 禁用连接溢出

## 部署步骤

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd py-demo

# 初始化项目
make setup
```

### 2. 配置环境变量

```bash
# 编辑.env文件
vim .env

# 确保所有必需变量都已设置
```

### 3. 数据库初始化

```bash
# 初始化数据库结构
make init-db
```

### 4. 启动应用

```bash
# 开发环境
make dev-uv

# 生产环境
make deploy
```

## Docker部署

### 构建镜像

```bash
make docker-build
```

### 运行容器

```bash
# 确保环境变量文件存在
docker run -d \
  --name miniblog \
  --env-file .env \
  -p 5000:5000 \
  miniblog:latest
```

## Kubernetes部署

### 使用Helm

```bash
# 安装
make helm-install

# 卸载
make helm-uninstall
```

### 配置Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: miniblog-config
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "mysql+pymysql://user:pass@mysql:3306/miniblog"
  REDIS_HOST: "redis"
  NACOS_HOST: "nacos"
```

## 监控和日志

### 日志配置

- 日志文件: `logs/miniblog.log`
- 日志级别: INFO（生产环境）
- 日志轮转: 建议配置logrotate

### 健康检查

```bash
# 健康检查端点
curl http://localhost:5000/healthz
```

## 安全注意事项

1. **密钥管理**
   - 使用强随机密钥
   - 定期轮换密钥
   - 不要在代码中硬编码密钥

2. **数据库安全**
   - 使用专用数据库用户
   - 限制数据库访问权限
   - 启用SSL连接

3. **网络安全**
   - 使用防火墙限制访问
   - 启用HTTPS
   - 配置适当的CORS策略

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL格式
   - 确认数据库服务可访问
   - 验证用户权限

2. **Redis连接失败**
   - 检查REDIS_HOST配置
   - 确认Redis服务运行
   - 检查网络连接

3. **应用启动失败**
   - 检查所有必需环境变量
   - 查看应用日志
   - 验证依赖服务状态

### 日志查看

```bash
# 查看应用日志
tail -f logs/miniblog.log

# 查看Docker容器日志
docker logs miniblog

# 查看Kubernetes Pod日志
kubectl logs deployment/miniblog
```