#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * License 数据模型
    - key: 主键，激活码
    - machine_id: 机器码（可为空）
    - expiration_date: 过期日期
    - is_active: 是否激活（默认 True）
"""
from sqlalchemy import Column, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

Base = declarative_base()


class License(Base):
    """激活码数据模型"""
    __tablename__ = "licenses"
    
    key = Column(String, primary_key=True, index=True)
    machine_id = Column(String, nullable=True)
    expiration_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
