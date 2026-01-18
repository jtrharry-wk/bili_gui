#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 验证服务器

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * POST /verify - 验证激活码接口
    - 检查激活码是否存在、是否过期、是否被冻结
    - 设备绑定逻辑（首次使用自动绑定，已绑定则验证设备ID）
  * POST /create_license - 创建激活码接口（管理员）
    - 生成 UUID 作为激活码
    - 根据天数计算过期时间
  * GET / - API 信息
  * GET /health - 健康检查接口
"""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
import uuid
from typing import Optional

from database import SessionLocal, init_db
from models import License

# 初始化 FastAPI 应用
app = FastAPI(title="License Verification Server", version="1.0.0")

# 初始化数据库
init_db()


# 依赖注入：获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic 模型：验证请求
class VerifyRequest(BaseModel):
    """验证请求模型"""
    license_key: str
    machine_id: str


class VerifyResponse(BaseModel):
    """验证响应模型"""
    valid: bool
    expiry: Optional[str] = None
    message: str


class CreateLicenseRequest(BaseModel):
    """创建激活码请求模型"""
    days: int


class CreateLicenseResponse(BaseModel):
    """创建激活码响应模型"""
    license_key: str
    expiration_date: str
    message: str


@app.post("/verify", response_model=VerifyResponse)
async def verify_license(
    request: VerifyRequest,
    db: Session = Depends(get_db)
):
    """
    验证激活码接口
    
    验证逻辑：
    1. 查找激活码
    2. 检查是否存在
    3. 检查是否过期
    4. 检查是否被冻结
    5. 处理设备绑定逻辑
    """
    # 在数据库中查找激活码
    license_obj = db.query(License).filter(License.key == request.license_key).first()
    
    # 如果激活码不存在
    if not license_obj:
        raise HTTPException(status_code=404, detail="激活码无效")
    
    # 检查是否过期
    if license_obj.expiration_date < date.today():
        raise HTTPException(status_code=403, detail="激活码已过期")
    
    # 检查是否被冻结
    if not license_obj.is_active:
        raise HTTPException(status_code=403, detail="激活码已被冻结")
    
    # 设备绑定逻辑
    if license_obj.machine_id is None or license_obj.machine_id == "":
        # 第一次使用，自动绑定设备
        license_obj.machine_id = request.machine_id
        db.commit()
        db.refresh(license_obj)
    elif license_obj.machine_id != request.machine_id:
        # 设备不匹配
        raise HTTPException(
            status_code=403,
            detail="设备不匹配（该激活码已绑定其他设备）"
        )
    
    # 验证通过
    return VerifyResponse(
        valid=True,
        expiry=license_obj.expiration_date.isoformat(),
        message="激活成功"
    )


@app.post("/create_license", response_model=CreateLicenseResponse)
async def create_license(
    request: CreateLicenseRequest,
    db: Session = Depends(get_db)
):
    """
    创建激活码接口（管理员专用）
    
    生成一个随机的 UUID 作为激活码，并设置过期时间
    """
    # 验证天数参数
    if request.days <= 0:
        raise HTTPException(status_code=400, detail="有效期天数必须大于 0")
    
    # 生成随机 UUID 作为激活码
    license_key = str(uuid.uuid4())
    
    # 计算过期时间
    expiration_date = date.today() + timedelta(days=request.days)
    
    # 创建新的激活码记录
    new_license = License(
        key=license_key,
        machine_id=None,  # 初始为空，等待首次使用时绑定
        expiration_date=expiration_date,
        is_active=True
    )
    
    # 保存到数据库
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    
    return CreateLicenseResponse(
        license_key=license_key,
        expiration_date=expiration_date.isoformat(),
        message=f"激活码创建成功，有效期 {request.days} 天"
    )


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "License Verification Server",
        "version": "1.0.0",
        "endpoints": {
            "verify": "POST /verify - 验证激活码",
            "create_license": "POST /create_license - 创建激活码"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}
