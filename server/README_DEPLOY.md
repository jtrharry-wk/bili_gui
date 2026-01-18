# Render 部署指南

## 部署前检查清单

### ✅ 1. 依赖检查
- [x] `fastapi` - Web 框架
- [x] `uvicorn[standard]` - ASGI 服务器
- [x] `sqlalchemy` - ORM 数据库工具
- [x] `pydantic` - 数据验证
- [x] `psycopg2-binary` - PostgreSQL 适配器

### ✅ 2. 数据库配置
- [x] `server/database.py` 已配置从环境变量读取 `DATABASE_URL`
- [x] 自动将 `postgres://` 转换为 `postgresql://`（兼容 Render）
- [x] 支持 PostgreSQL 和 SQLite 自动切换

### ✅ 3. 部署文件
- [x] `Procfile` - Render 启动命令
- [x] `requirements.txt` - Python 依赖

## Render 部署步骤

### 1. 创建 Web Service

1. 登录 Render Dashboard
2. 点击 "New +" → "Web Service"
3. 连接你的 GitHub 仓库
4. 选择仓库和分支

### 2. 配置设置

**基本信息：**
- **Name**: `license-verification-server`（或自定义）
- **Region**: 选择离你最近的区域
- **Branch**: `main` 或 `master`
- **Root Directory**: `server`（重要！）
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`

**环境变量：**
- `DATABASE_URL`: 你的 Neon PostgreSQL 连接字符串
  - 格式：`postgres://user:password@host:port/dbname?sslmode=require`
  - 代码会自动转换为 `postgresql://`

### 3. 数据库配置（Neon）

1. 在 Neon Dashboard 创建数据库
2. 获取连接字符串
3. 在 Render 环境变量中设置 `DATABASE_URL`

**Neon 连接字符串示例：**
```
postgres://neondb_owner:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require
```

### 4. 部署

点击 "Create Web Service"，Render 会自动：
1. 安装依赖
2. 启动服务器
3. 创建数据库表（首次运行）

## 验证部署

部署成功后，访问：
- API 文档：`https://your-app.onrender.com/docs`
- 健康检查：`https://your-app.onrender.com/health`

## 注意事项

1. **Root Directory**: 必须设置为 `server`，因为代码在 server 文件夹中
2. **DATABASE_URL**: Render 可能提供 `postgres://` 格式，代码会自动转换
3. **首次启动**: 会自动创建 `licenses` 表
4. **免费计划**: Render 免费计划在 15 分钟无活动后会休眠，首次访问需要几秒钟唤醒

## 故障排查

### 数据库连接失败
- 检查 `DATABASE_URL` 环境变量是否正确
- 确认 Neon 数据库允许外部连接
- 检查 SSL 模式设置

### 启动失败
- 检查 `Procfile` 中的命令是否正确
- 查看 Render 日志了解详细错误
- 确认 `requirements.txt` 中所有依赖都已列出
