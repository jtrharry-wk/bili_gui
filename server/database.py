#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置和连接

版本历史：
==========

v1.1 (2026-01-17)
--------------
- 支持 PostgreSQL 数据库
  * 从环境变量读取 DATABASE_URL
  * 自动适配 PostgreSQL 和 SQLite
  * 支持 Render/Neon 等云数据库服务

v1.0 (2026-01-17)
--------------
- 初始版本
  * SQLite 数据库连接配置
  * 创建 SessionLocal 和 Base
  * 数据库初始化函数
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# 从环境变量读取数据库 URL，默认为本地 SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./licenses.db")

# 关键逻辑适配：如果检测到 postgres:// 开头，替换为 postgresql://
# （SQLAlchemy 要求使用 postgresql:// 而不是 postgres://）
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 判断是否为 PostgreSQL 数据库
is_postgresql = DATABASE_URL.startswith("postgresql://")

# 创建数据库引擎
if is_postgresql:
    # PostgreSQL 配置（生产环境）
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # 连接前检查连接是否有效
        echo=False  # 设置为 True 可以查看 SQL 语句（调试用）
    )
else:
    # SQLite 配置（开发环境）
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite 需要这个参数
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
