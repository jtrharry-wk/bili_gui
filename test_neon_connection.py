#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Neon PostgreSQL 数据库连接
"""
import os
from sqlalchemy import create_engine, text

# 设置数据库 URL
DATABASE_URL = "postgres://neondb_owner:npg_DCG2u1leQiAv@ep-purple-star-a1sk78o1-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# 自动转换 postgres:// 为 postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print("=" * 60)
print("Neon PostgreSQL 连接测试")
print("=" * 60)
print(f"数据库 URL: {DATABASE_URL.split('@')[0]}@***")
print()

try:
    # 创建数据库引擎
    print("正在创建数据库引擎...")
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False
    )
    print("[成功] 数据库引擎创建成功")
    print()
    
    # 测试连接
    print("正在测试数据库连接...")
    with engine.connect() as conn:
        # 执行一个简单的查询
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("[成功] 数据库连接成功！")
        print(f"  PostgreSQL 版本: {version[:50]}...")
        print()
        
        # 检查 licenses 表是否存在
        print("正在检查 licenses 表...")
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'licenses'
            );
        """))
        table_exists = result.fetchone()[0]
        
        if table_exists:
            print("[成功] licenses 表已存在")
            
            # 获取表记录数
            result = conn.execute(text("SELECT COUNT(*) FROM licenses;"))
            count = result.fetchone()[0]
            print(f"  当前记录数: {count}")
        else:
            print("[提示] licenses 表不存在（首次运行时会自动创建）")
        print()
        
        # 测试写入权限
        print("正在测试写入权限...")
        test_result = conn.execute(text("SELECT 1;"))
        test_result.fetchone()
        print("[成功] 读写权限正常")
        print()
    
    print("=" * 60)
    print("[成功] 所有测试通过！数据库连接正常。")
    print("=" * 60)
    
except Exception as e:
    print("=" * 60)
    print("[失败] 连接失败！")
    print("=" * 60)
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print()
    print("可能的原因：")
    print("1. 数据库 URL 不正确")
    print("2. 网络连接问题")
    print("3. 数据库凭证错误")
    print("4. SSL 配置问题")
    import sys
    sys.exit(1)
