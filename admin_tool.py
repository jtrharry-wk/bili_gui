#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码管理工具
用于创建激活码

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * 命令行工具，支持创建激活码
  * 支持命令行参数和交互式模式
  * 完整的错误处理和网络异常处理
"""
import requests
import json
import sys
import argparse

API_URL = "http://127.0.0.1:8000"


def create_license(days: int) -> dict:
    """
    创建激活码
    
    Args:
        days: 有效期天数
        
    Returns:
        dict: 服务器返回的响应数据
    """
    url = f"{API_URL}/create_license"
    payload = {"days": days}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()  # 如果状态码不是 200，会抛出异常
        return response.json()
    except requests.exceptions.ConnectionError:
        print("[错误] 无法连接到服务器，请确保服务器正在运行")
        print(f"   服务器地址: {API_URL}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[错误] 请求超时")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"[错误] HTTP 错误 - {e}")
        try:
            error_detail = response.json().get("detail", "未知错误")
            print(f"   详情: {error_detail}")
        except:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"[错误] {str(e)}")
        sys.exit(1)


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='激活码生成工具')
    parser.add_argument('days', type=int, nargs='?', help='有效期天数')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("激活码生成工具")
    print("=" * 60)
    print(f"服务器地址: {API_URL}\n")
    
    # 确定天数
    days = None
    
    if args.days:
        # 命令行参数模式
        days = args.days
    elif args.interactive or not args.days:
        # 交互式模式
        while True:
            try:
                days_input = input("请输入有效期天数（直接回车退出）: ").strip()
                
                if not days_input:
                    print("已取消操作")
                    return
                
                days = int(days_input)
                
                if days <= 0:
                    print("[错误] 天数必须大于 0，请重新输入\n")
                    continue
                
                break
            except ValueError:
                print("[错误] 请输入有效的数字\n")
                continue
            except KeyboardInterrupt:
                print("\n已取消操作")
                return
    else:
        parser.print_help()
        return
    
    # 验证天数
    if days <= 0:
        print("[错误] 天数必须大于 0")
        sys.exit(1)
    
    # 创建激活码
    print(f"\n正在创建有效期 {days} 天的激活码...")
    
    try:
        result = create_license(days)
        
        # 显示结果
        print("\n" + "=" * 60)
        print("[成功] 激活码创建成功！")
        print("=" * 60)
        print(f"激活码: {result.get('license_key', 'N/A')}")
        print(f"过期日期: {result.get('expiration_date', 'N/A')}")
        print(f"消息: {result.get('message', 'N/A')}")
        print("=" * 60)
        
        # 复制提示
        license_key = result.get('license_key', '')
        if license_key:
            print(f"\n[提示] 激活码已生成，可以复制给用户使用")
            print(f"   激活码: {license_key}")
        
    except Exception as e:
        print(f"\n[错误] 创建失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已退出")
        sys.exit(0)
