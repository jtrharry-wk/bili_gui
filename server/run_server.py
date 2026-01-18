#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动服务器脚本

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * 使用 uvicorn 启动 FastAPI 服务器
  * 支持自动重载（开发模式）
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式，代码修改后自动重载
    )
