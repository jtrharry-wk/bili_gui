#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码管理工具 - GUI 版本
用于创建激活码

版本历史：
==========

v1.0 (2026-01-17)
--------------
- 初始版本
  * 基于 customtkinter 的图形界面
  * 支持服务器地址配置
  * 支持有效期天数输入
  * 显示生成的激活码和过期日期
  * 完整的错误处理和网络异常处理
"""
import customtkinter as ctk
import requests
import threading
import sys
import os

API_URL = "http://127.0.0.1:8000"


class AdminToolGUI:
    """激活码管理工具 GUI 类"""
    
    def __init__(self):
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("激活码管理工具")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 创建界面
        self.create_widgets()
        
        # 居中显示窗口
        self.center_window()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = ctk.CTkLabel(
            self.root,
            text="激活码管理工具",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(30, 20))
        
        # 服务器地址显示
        server_frame = ctk.CTkFrame(self.root)
        server_frame.pack(pady=10, padx=30, fill="x")
        
        server_label = ctk.CTkLabel(
            server_frame,
            text="服务器地址：",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        server_label.pack(anchor="w", padx=15, pady=(15, 8))
        
        self.server_entry = ctk.CTkEntry(
            server_frame,
            height=35,
            font=ctk.CTkFont(size=12),
            placeholder_text="http://127.0.0.1:8000"
        )
        self.server_entry.insert(0, API_URL)
        self.server_entry.pack(padx=15, pady=(0, 15), fill="x")
        
        # 有效期天数输入
        days_frame = ctk.CTkFrame(self.root)
        days_frame.pack(pady=10, padx=30, fill="x")
        
        days_label = ctk.CTkLabel(
            days_frame,
            text="有效期天数：",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        days_label.pack(anchor="w", padx=15, pady=(15, 8))
        
        self.days_entry = ctk.CTkEntry(
            days_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="请输入天数（例如：30）"
        )
        self.days_entry.pack(padx=15, pady=(0, 15), fill="x")
        self.days_entry.bind("<Return>", lambda e: self.create_license())  # 回车键创建
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=(10, 5))
        
        # 创建按钮
        self.create_btn = ctk.CTkButton(
            self.root,
            text="创建激活码",
            command=self.create_license,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            corner_radius=10
        )
        self.create_btn.pack(pady=15, padx=30, fill="x")
        
        # 结果显示区域
        result_frame = ctk.CTkFrame(self.root)
        result_frame.pack(pady=10, padx=30, fill="both", expand=True)
        
        result_title = ctk.CTkLabel(
            result_frame,
            text="生成结果：",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        result_title.pack(anchor="w", padx=15, pady=(15, 8))
        
        self.result_text = ctk.CTkTextbox(
            result_frame,
            height=120,
            font=ctk.CTkFont(size=11, family="Consolas"),
            wrap="word"
        )
        self.result_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.result_text.insert("1.0", "等待创建激活码...")
        self.result_text.configure(state="disabled")
        
        # 设置焦点到输入框
        self.days_entry.focus()
    
    def create_license(self):
        """创建激活码"""
        # 获取输入
        days_input = self.days_entry.get().strip()
        server_url = self.server_entry.get().strip() or API_URL
        
        # 验证输入
        if not days_input:
            self.status_label.configure(
                text="请输入有效期天数",
                text_color="#d32f2f"
            )
            return
        
        try:
            days = int(days_input)
            if days <= 0:
                self.status_label.configure(
                    text="天数必须大于 0",
                    text_color="#d32f2f"
                )
                return
        except ValueError:
            self.status_label.configure(
                text="请输入有效的数字",
                text_color="#d32f2f"
            )
            return
        
        # 禁用按钮，显示创建中
        self.create_btn.configure(state="disabled", text="创建中...")
        self.status_label.configure(text="正在创建激活码...", text_color="gray")
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "正在连接服务器...")
        self.result_text.configure(state="disabled")
        self.root.update()
        
        # 在新线程中执行创建（避免阻塞UI）
        threading.Thread(
            target=self._create_thread,
            args=(days, server_url),
            daemon=True
        ).start()
    
    def _create_thread(self, days, server_url):
        """创建激活码线程"""
        try:
            url = f"{server_url}/create_license"
            payload = {"days": days}
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # 在主线程中更新UI
            self.root.after(0, self._handle_create_result, True, result, None)
        except requests.exceptions.ConnectionError:
            self.root.after(
                0,
                self._handle_create_result,
                False,
                None,
                "无法连接到服务器，请确保服务器正在运行"
            )
        except requests.exceptions.Timeout:
            self.root.after(
                0,
                self._handle_create_result,
                False,
                None,
                "请求超时"
            )
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP 错误: {str(e)}"
            try:
                error_detail = response.json().get("detail", "未知错误")
                error_msg = f"{error_msg}\n详情: {error_detail}"
            except:
                pass
            self.root.after(0, self._handle_create_result, False, None, error_msg)
        except Exception as e:
            self.root.after(
                0,
                self._handle_create_result,
                False,
                None,
                f"创建失败: {str(e)}"
            )
    
    def _handle_create_result(self, success, result, error_msg):
        """处理创建结果"""
        # 恢复按钮状态
        self.create_btn.configure(state="normal", text="创建激活码")
        
        # 更新结果显示
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        
        if success:
            # 创建成功
            license_key = result.get('license_key', 'N/A')
            expiration_date = result.get('expiration_date', 'N/A')
            message = result.get('message', 'N/A')
            
            result_text = f"""[成功] 激活码创建成功！

激活码: {license_key}
过期日期: {expiration_date}
消息: {message}

[提示] 可以复制激活码给用户使用"""
            
            self.result_text.insert("1.0", result_text)
            self.status_label.configure(
                text="激活码创建成功！",
                text_color="#4caf50"
            )
        else:
            # 创建失败
            self.result_text.insert("1.0", f"[错误] {error_msg}")
            self.status_label.configure(
                text="创建失败",
                text_color="#d32f2f"
            )
        
        self.result_text.configure(state="disabled")
    
    def run(self):
        """运行 GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = AdminToolGUI()
    app.run()
