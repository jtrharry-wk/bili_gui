# License Verification Server

基于 FastAPI 的激活码验证服务器。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务器

### 方法 1：使用启动脚本
```bash
python run_server.py
```

### 方法 2：使用 uvicorn 直接运行
```bash
cd server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 方法 3：从项目根目录运行
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

服务器启动后，访问：
- API 文档：http://localhost:8000/docs
- 交互式 API 文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## API 接口

### 1. 验证激活码
**POST** `/verify`

请求体：
```json
{
  "license_key": "your-license-key",
  "machine_id": "your-machine-id"
}
```

响应：
```json
{
  "valid": true,
  "expiry": "2024-12-31",
  "message": "激活成功"
}
```

### 2. 创建激活码
**POST** `/create_license`

请求体：
```json
{
  "days": 30
}
```

响应：
```json
{
  "license_key": "uuid-generated-key",
  "expiration_date": "2024-12-31",
  "message": "激活码创建成功，有效期 30 天"
}
```

## 数据库

服务器使用 SQLite 数据库，数据库文件 `licenses.db` 会在首次运行时自动创建在 `server` 目录下。

## 验证逻辑

1. 检查激活码是否存在
2. 检查激活码是否过期
3. 检查激活码是否被冻结
4. 设备绑定逻辑：
   - 如果激活码未绑定设备，自动绑定当前设备
   - 如果已绑定设备，验证设备 ID 是否匹配
