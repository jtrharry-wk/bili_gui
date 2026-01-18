#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码验证客户端
负责机器码生成和网络验证

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * 机器码生成功能（基于 MAC 地址和计算机名）
  * 在线验证激活码功能
  * 完整的网络异常处理（连接失败、超时等）
  * 支持自定义 API 地址和超时时间
"""
import uuid
import platform
import hashlib
import requests
from typing import Tuple


def get_machine_code() -> str:
    """
    生成唯一机器码
    
    使用 MAC 地址和计算机名进行 MD5 哈希，取前 12 位大写字符
    
    Returns:
        str: 12位大写机器码
    """
    # 获取 MAC 地址
    mac_address = str(uuid.getnode())
    
    # 获取计算机名
    computer_name = platform.node()
    
    # 拼接 MAC 地址和计算机名
    combined_string = f"{mac_address}_{computer_name}"
    
    # MD5 哈希
    md5_hash = hashlib.md5(combined_string.encode('utf-8')).hexdigest()
    
    # 取前 12 位并转换为大写
    machine_code = md5_hash[:12].upper()
    
    return machine_code


class LicenseClient:
    """激活码验证客户端类"""
    
    # API 服务器地址（云端生产环境）
    API_URL = "https://license-verification-server-2efe.onrender.com"
    
    # API 服务器地址（本地测试用 - 已注释）
    # API_URL = "http://127.0.0.1:8000"
    
    # 请求超时时间（秒）
    TIMEOUT = 10
    
    def __init__(self, api_url: str = None, timeout: int = None):
        """
        初始化客户端
        
        Args:
            api_url: 自定义 API 服务器地址，默认为 API_URL
            timeout: 请求超时时间，默认为 TIMEOUT
        """
        self.api_url = api_url or self.API_URL
        self.timeout = timeout or self.TIMEOUT
    
    def verify_online(self, license_key: str) -> Tuple[bool, str]:
        """
        在线验证激活码
        
        Args:
            license_key: 激活码
            
        Returns:
            Tuple[bool, str]: (验证结果, 消息)
                - (True, "激活成功，有效期至: YYYY-MM-DD") 验证成功
                - (False, "错误信息") 验证失败
        """
        # 验证输入
        if not license_key or not license_key.strip():
            return (False, "激活码不能为空")
        
        # 获取机器码
        try:
            machine_code = get_machine_code()
        except Exception as e:
            return (False, f"获取机器码失败: {str(e)}")
        
        # 准备请求数据
        payload = {
            "license_key": license_key.strip(),
            "machine_id": machine_code
        }
        
        # 发送验证请求
        try:
            response = requests.post(
                f"{self.api_url}/verify",
                json=payload,
                timeout=self.timeout
            )
            
            # 处理响应
            if response.status_code == 200:
                # 验证成功
                data = response.json()
                expiry = data.get("expiry", "未知")
                message = data.get("message", "激活成功")
                return (True, f"{message}，有效期至: {expiry}")
            
            elif response.status_code == 404:
                # 激活码不存在
                error_detail = response.json().get("detail", "激活码无效")
                return (False, error_detail)
            
            elif response.status_code == 403:
                # 激活码过期、被冻结或设备不匹配
                error_detail = response.json().get("detail", "验证失败")
                return (False, error_detail)
            
            else:
                # 其他状态码
                try:
                    error_detail = response.json().get("detail", f"服务器返回错误 (状态码: {response.status_code})")
                except:
                    error_detail = f"服务器返回错误 (状态码: {response.status_code})"
                return (False, error_detail)
        
        except requests.exceptions.ConnectionError:
            # 连接失败
            return (False, "无法连接验证服务器，请检查网络连接或服务器是否运行")
        
        except requests.exceptions.Timeout:
            # 请求超时
            return (False, f"连接验证服务器超时（超过 {self.timeout} 秒）")
        
        except requests.exceptions.RequestException as e:
            # 其他网络请求异常
            return (False, f"网络请求失败: {str(e)}")
        
        except Exception as e:
            # 其他未知异常
            return (False, f"验证过程发生错误: {str(e)}")
    
    def get_machine_code(self) -> str:
        """
        获取当前机器的机器码
        
        Returns:
            str: 机器码
        """
        return get_machine_code()


# 测试代码
if __name__ == "__main__":
    # 测试机器码生成
    print("=" * 50)
    print("机器码生成测试")
    print("=" * 50)
    machine_code = get_machine_code()
    print(f"机器码: {machine_code}")
    print(f"长度: {len(machine_code)}")
    print()
    
    # 测试验证客户端
    print("=" * 50)
    print("验证客户端测试")
    print("=" * 50)
    client = LicenseClient()
    print(f"API 地址: {client.api_url}")
    print(f"超时时间: {client.timeout} 秒")
    print()
    
    # 测试验证（需要服务器运行）
    test_key = input("请输入测试激活码（直接回车跳过）: ").strip()
    if test_key:
        print("\n正在验证...")
        result, message = client.verify_online(test_key)
        print(f"验证结果: {'成功' if result else '失败'}")
        print(f"消息: {message}")
    else:
        print("跳过验证测试")
