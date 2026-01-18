#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili批量下载神器 - 图形界面版
使用customtkinter构建现代化界面，使用yt-dlp进行下载

版本历史：
==========

v1.4 (2026-01-17)
--------------
- 新增激活验证功能
  * 集成激活码验证系统
  * 激活窗口（支持在线验证）
  * 授权有效期和剩余天数显示
  * 根据剩余天数显示不同颜色提示（绿色/橙色/红色）

v1.3 (当前版本)
--------------
- 新增网络代理配置功能
  * 在设置区域添加网络代理选项
  * 支持启用/禁用代理，可自定义代理地址
  * 代理配置自动应用到yt-dlp下载选项

- 新增音视频独立提取功能
  * 支持三种下载模式：最佳音画、仅音频(MP3)、仅视频(无声)
  * 仅音频模式自动转换为MP3格式
  * 仅视频模式下载无音频视频文件

- GUI界面优化
  * 重新设计设置区域布局，更美观整洁
  * 登录凭证来源和下载模式分两行显示
  * 视频链接和保存路径并排显示，节省空间
  * 优化窗口高度和日志区域大小

v.2
----
- 修复Edge浏览器Cookie识别失败问题
  * 简化Cookie配置逻辑，直接使用'edge'名称，让yt-dlp内部处理
  * 移除无效的浏览器名称测试循环代码
  * 增强Edge浏览器错误提示，提供清晰的解决步骤
  * 提示用户关闭Edge后台进程或使用本地cookies.txt文件

v1.1
----
- 支持多浏览器Cookie选择
  * 新增Chrome、Edge、Firefox、Brave、Opera浏览器Cookie支持
  * 添加本地cookies.txt文件检测和导入功能
  * 支持"不使用登录（低画质）"模式
  * 默认选中Chrome浏览器
  
- 优化错误处理和降级机制
  * 智能捕获Cookie相关错误（初始化阶段和下载阶段）
  * Cookie读取失败时自动降级为不登录模式并重试
  * 提供详细的错误信息和可能的解决方案
  * 针对不同浏览器提供特定的错误提示

- 改进用户体验
  * 优化全局进度条显示，支持批量下载的平滑进度更新
  * 支持全时段暂停功能（包括解析阶段）
  * 改进了日志显示和状态提示

v1.0
----
- 初始版本
  * 基本的视频批量下载功能
  * 支持收藏夹、UP主空间等链接解析
  * 基础进度显示和日志功能
"""

import customtkinter as ctk
import yt_dlp
import threading
import os
import sys
import shutil
import time
from tkinter import filedialog, messagebox
import queue
from datetime import datetime
import re
from license_client import LicenseClient, get_machine_code


class MyLogger:
    """自定义日志类，将yt-dlp输出重定向到GUI文本框"""
    
    def __init__(self, text_widget, log_queue, app=None):
        self.text_widget = text_widget
        self.log_queue = log_queue
        self.app = app  # 保存app引用，用于暂停检查
    
    def debug(self, msg):
        # 第二道拦截（针对准备/解析阶段 - 关键黑科技）
        # yt-dlp在解析网页时会不断调用debug日志，卡住这里可以卡住解析流程
        if self.app is not None:
            while self.app.is_paused:
                time.sleep(0.1)
        
        if msg.startswith('[debug]'):
            return
        self.log_queue.put(('debug', msg))
    
    def info(self, msg):
        self.log_queue.put(('info', msg))
    
    def warning(self, msg):
        self.log_queue.put(('warning', msg))
    
    def error(self, msg):
        self.log_queue.put(('error', msg))


class ActivationApp:
    """激活窗口类"""
    
    LICENSE_FILE = ".license"  # 激活码保存文件（隐藏文件）
    
    def __init__(self, callback=None):
        """
        初始化激活窗口
        
        Args:
            callback: 激活成功后的回调函数，用于启动主程序
        """
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("软件激活")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 回调函数
        self.callback = callback
        
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
            text="软件激活",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(30, 20))
        
        # 激活码输入区域
        license_frame = ctk.CTkFrame(self.root)
        license_frame.pack(pady=15, padx=30, fill="x")
        
        license_label = ctk.CTkLabel(
            license_frame,
            text="请输入激活码：",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        license_label.pack(anchor="w", padx=15, pady=(15, 8))
        
        self.license_entry = ctk.CTkEntry(
            license_frame,
            height=40,
            font=ctk.CTkFont(size=12),
            placeholder_text="粘贴激活码..."
        )
        self.license_entry.pack(padx=15, pady=(0, 15), fill="x")
        self.license_entry.bind("<Return>", lambda e: self.activate())  # 回车键激活
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=(10, 5))
        
        # 激活按钮
        self.activate_btn = ctk.CTkButton(
            self.root,
            text="立即激活",
            command=self.activate,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            corner_radius=10
        )
        self.activate_btn.pack(pady=15, padx=30, fill="x")
        
        # 设置焦点到输入框
        self.license_entry.focus()
    
    def activate(self):
        """执行激活操作"""
        license_key = self.license_entry.get().strip()
        
        if not license_key:
            self.status_label.configure(
                text="请输入激活码",
                text_color="#d32f2f"
            )
            return
        
        # 禁用按钮，显示验证中
        self.activate_btn.configure(state="disabled", text="验证中...")
        self.status_label.configure(text="正在验证激活码...", text_color="gray")
        self.root.update()
        
        # 在新线程中执行验证（避免阻塞UI）
        threading.Thread(target=self._verify_thread, args=(license_key,), daemon=True).start()
    
    def _verify_thread(self, license_key):
        """验证线程"""
        try:
            client = LicenseClient()
            result, message = client.verify_online(license_key)
            
            # 在主线程中更新UI
            self.root.after(0, self._handle_verify_result, result, message, license_key)
        except Exception as e:
            self.root.after(0, self._handle_verify_result, False, f"验证过程发生错误: {str(e)}", None)
    
    def _handle_verify_result(self, result, message, license_key):
        """处理验证结果"""
        # 恢复按钮状态
        self.activate_btn.configure(state="normal", text="立即激活")
        
        if result:
            # 验证成功
            try:
                # 保存激活码到本地文件
                license_file_path = os.path.join(os.getcwd(), self.LICENSE_FILE)
                with open(license_file_path, 'w', encoding='utf-8') as f:
                    f.write(license_key)
                
                self.status_label.configure(
                    text="✓ 激活成功！",
                    text_color="#4caf50"
                )
                self.root.update()
                
                # 延迟关闭窗口，让用户看到成功提示，传递 message 参数
                self.root.after(500, lambda: self._on_activation_success(message))
            except Exception as e:
                self.status_label.configure(
                    text=f"保存激活码失败: {str(e)}",
                    text_color="#d32f2f"
                )
        else:
            # 验证失败
            self.status_label.configure(
                text=f"✗ {message}",
                text_color="#d32f2f"
            )
    
    def _on_activation_success(self, message):
        """激活成功后的处理"""
        # 关闭激活窗口
        self.root.destroy()
        
        # 调用回调函数启动主程序，传递 message 参数
        if self.callback:
            self.callback(message)
    
    def run(self):
        """运行激活窗口"""
        self.root.mainloop()


class BiliDownloaderGUI:
    """Bilibili批量下载器GUI类"""
    
    def __init__(self, license_info=""):
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("Bilibili批量下载神器 v1.4")
        self.root.geometry("900x850")
        
        # 保存授权信息
        self.license_info = license_info
        
        # 下载状态
        self.is_downloading = False
        self.is_paused = False
        self.download_thread = None
        self.log_queue = queue.Queue()
        self.current_download_url = None  # 保存当前下载链接
        self.all_videos_completed = False  # 所有视频完成标志
        self.ydl_instance = None  # 保存yt-dlp实例，用于取消下载
        # 播放列表信息
        self.playlist_count = None
        self.current_playlist_index = None
        self.completed_count = 0  # 实际下载完成的视频数量
        
        # 创建界面
        self.create_widgets()
        
        # 启动日志处理
        self.process_log_queue()
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = ctk.CTkLabel(
            self.root,
            text="Bilibili批量下载神器",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(25, 2))
        
        # 版本号显示
        version_label = ctk.CTkLabel(
            self.root,
            text="v1.4",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(pady=(0, 5))
        
        # 授权信息显示
        if self.license_info:
            # 尝试从 message 中提取日期
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', self.license_info)
            if date_match:
                try:
                    expiry_date_str = date_match.group()
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
                    current_date = datetime.now()
                    days_remaining = (expiry_date - current_date).days
                    
                    if days_remaining < 0:
                        # 已过期
                        license_text = f"👑 授权已过期: {expiry_date_str}"
                        license_color = "#d32f2f"
                    elif days_remaining < 7:
                        # 剩余天数少于7天，显示红色或橙色
                        license_text = f"👑 授权有效期至: {expiry_date_str} (剩余 {days_remaining} 天)"
                        license_color = "#ff9800"  # 橙色
                    else:
                        # 剩余天数充足，显示绿色
                        license_text = f"👑 授权有效期至: {expiry_date_str} (剩余 {days_remaining} 天)"
                        license_color = "#4caf50"  # 绿色
                except Exception:
                    # 日期解析失败，显示原始信息
                    license_text = "👑 授权状态: 已激活"
                    license_color = "#4caf50"
            else:
                # 未找到日期，显示原始信息
                license_text = "👑 授权状态: 已激活"
                license_color = "#4caf50"
            
            self.license_label = ctk.CTkLabel(
                self.root,
                text=license_text,
                font=ctk.CTkFont(size=12),
                text_color=license_color
            )
            self.license_label.pack(pady=(0, 10))
        else:
            # 无授权信息，不显示
            pass
        
        # 输入区框架
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        # --- 设置区域（整合为一个美观的框架）---
        settings_container = ctk.CTkFrame(input_frame)
        settings_container.pack(pady=15, padx=15, fill="x")
        
        # 设置区域标题
        settings_title = ctk.CTkLabel(
            settings_container,
            text="⚙️ 下载设置",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        settings_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # --- 登录凭证设置 ---
        cookie_row = ctk.CTkFrame(settings_container, fg_color="transparent")
        cookie_row.pack(pady=8, padx=15, fill="x")
        
        cookie_label = ctk.CTkLabel(
            cookie_row,
            text="登录凭证来源：",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            anchor="w"
        )
        cookie_label.pack(side="left")
        
        self.cookie_source_var = ctk.StringVar(value="Chrome 浏览器")
        self.cookie_combo = ctk.CTkComboBox(
            cookie_row,
            values=["Chrome 浏览器", "Edge 浏览器", "Firefox 浏览器", "Opera 浏览器", "Brave 浏览器", "本地 cookies.txt", "不使用登录 (低画质)"],
            width=220,
            variable=self.cookie_source_var,
            state="readonly"
        )
        self.cookie_combo.pack(side="left", padx=(0, 10))
        
        cookie_tip = ctk.CTkLabel(
            cookie_row,
            text="(大会员请选对应浏览器或导入cookie以获取4K)",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        cookie_tip.pack(side="left")
        
        # --- 下载模式和网络代理设置（同一行） ---
        mode_proxy_row = ctk.CTkFrame(settings_container, fg_color="transparent")
        mode_proxy_row.pack(pady=(8, 15), padx=15, fill="x")
        
        download_mode_label = ctk.CTkLabel(
            mode_proxy_row,
            text="下载模式：",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            anchor="w"
        )
        download_mode_label.pack(side="left")
        
        self.download_mode_var = ctk.StringVar(value="最佳音画 (默认 MP4)")
        self.download_mode_combo = ctk.CTkComboBox(
            mode_proxy_row,
            values=["最佳音画 (默认 MP4)", "仅音频 (MP3)", "仅视频 (无声 MP4)"],
            width=200,
            variable=self.download_mode_var,
            state="readonly"
        )
        self.download_mode_combo.pack(side="left", padx=(0, 20))
        
        # 网络代理（右侧）
        network_label = ctk.CTkLabel(
            mode_proxy_row,
            text="网络代理：",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            anchor="w"
        )
        network_label.pack(side="left")
        
        self.proxy_enabled_var = ctk.BooleanVar(value=False)
        self.proxy_checkbox = ctk.CTkCheckBox(
            mode_proxy_row,
            text="启用",
            variable=self.proxy_enabled_var,
            command=self.toggle_proxy_input
        )
        self.proxy_checkbox.pack(side="left", padx=(0, 10))
        
        self.proxy_entry = ctk.CTkEntry(
            mode_proxy_row,
            placeholder_text="http://127.0.0.1:7890",
            width=200,
            state="disabled"
        )
        self.proxy_entry.pack(side="left")
        # ---------------------
        
        # 链接和路径输入区域（同一行）
        link_path_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        link_path_container.pack(pady=(15, 15), padx=15, fill="x")
        
        # 左侧：视频链接
        link_left_frame = ctk.CTkFrame(link_path_container, fg_color="transparent")
        link_left_frame.pack(side="left", padx=(0, 10), fill="both", expand=True)
        
        link_label = ctk.CTkLabel(
            link_left_frame,
            text="📎 视频链接",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        link_label.pack(anchor="w", pady=(0, 8))
        
        self.link_entry = ctk.CTkEntry(
            link_left_frame,
            placeholder_text="粘贴视频/收藏夹/UP主空间链接...",
            height=38,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        self.link_entry.pack(fill="x")
        
        # 右侧：保存路径
        path_right_frame = ctk.CTkFrame(link_path_container, fg_color="transparent")
        path_right_frame.pack(side="right", fill="both", expand=True)
        
        path_label = ctk.CTkLabel(
            path_right_frame,
            text="💾 保存路径",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        path_label.pack(anchor="w", pady=(0, 8))
        
        path_frame = ctk.CTkFrame(path_right_frame, fg_color="transparent")
        path_frame.pack(fill="x")
        
        default_path = os.path.join(os.getcwd(), "downloads")
        self.path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="选择保存路径...",
            height=38,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        self.path_entry.insert(0, default_path)
        self.path_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(
            path_frame,
            text="浏览",
            command=self.browse_folder,
            width=80,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8
        )
        browse_btn.pack(side="right")
        
        # 控制区框架
        control_frame = ctk.CTkFrame(self.root)
        control_frame.pack(pady=(8, 8), padx=20, fill="x")
        
        # 按钮区域（横向排列）
        button_row = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_row.pack(pady=12, padx=20, fill="x")
        
        # 开始下载按钮
        self.download_btn = ctk.CTkButton(
            button_row,
            text="▶ 开始批量下载",
            command=self.start_download,
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            corner_radius=10
        )
        self.download_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # 暂停/继续按钮
        self.btn_pause = ctk.CTkButton(
            button_row,
            text="⏸ 暂停任务",
            command=self.toggle_pause,
            height=48,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            state="disabled",
            corner_radius=10,
            width=150
        )
        self.btn_pause.pack(side="right")
        
        # 进度条区域
        progress_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        progress_container.pack(pady=(0, 12), padx=20, fill="x")
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(progress_container, height=22, corner_radius=12)
        self.progress_bar.pack(pady=(0, 6), fill="x")
        self.progress_bar.set(0)
        
        # 进度标签
        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="等待开始...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack()
        
        # 日志区框架
        log_frame = ctk.CTkFrame(self.root)
        log_frame.pack(pady=(8, 10), padx=20, fill="both", expand=True)
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 下载日志",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        log_title.pack(anchor="w", padx=15, pady=(12, 8))
        
        # 日志文本框（增加高度以确保有足够空间）
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=250,
            font=ctk.CTkFont(size=11, family="Consolas"),
            wrap="word",
            corner_radius=8
        )
        self.log_text.pack(pady=(0, 12), padx=15, fill="both", expand=True)
    
    def toggle_proxy_input(self):
        """切换代理输入框的启用/禁用状态"""
        if self.proxy_enabled_var.get():
            self.proxy_entry.configure(state="normal")
        else:
            self.proxy_entry.configure(state="disabled")
    
    def browse_folder(self):
        """选择保存文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
    
    def log(self, message, level="info"):
        """添加日志到文本框"""
        self.log_text.insert("end", f"[{level.upper()}] {message}\n")
        self.log_text.see("end")
    
    def process_log_queue(self):
        """处理日志队列"""
        try:
            while True:
                level, msg = self.log_queue.get_nowait()
                self.log(msg, level)
        except queue.Empty:
            pass
        
        # 每100ms检查一次
        self.root.after(100, self.process_log_queue)
    
    def progress_hook(self, d):
        """下载进度回调 - 优化后的平滑全局总进度显示"""
        # 第一道拦截（针对下载阶段）
        # 在函数第一行加入循环检查：while self.is_paused: time.sleep(0.1)
        while self.is_paused:
            time.sleep(0.1)
            # 暂停时进度条显示灰色
            self.progress_bar.configure(progress_color="#757575")
        
        # 暂停状态已解除，进度条恢复正常颜色
        self.progress_bar.configure(progress_color="#1f538d")
        
        try:
            # 获取关键数据：从d提取playlist_index和playlist_count
            playlist_index = d.get('playlist_index')
            playlist_count = d.get('playlist_count')
            
            # 更新播放列表信息（优先使用d中的信息，这是yt-dlp在实际下载时提供的准确数量）
            # 优先使用progress_hook中的playlist_count，因为它考虑了download_archive等过滤条件
            if playlist_count is not None and playlist_count > 0:
                # 如果数量发生变化，说明实际要下载的数量与初始数量不同（可能因为download_archive）
                if self.playlist_count is not None and self.playlist_count != playlist_count:
                    self.log(f"实际要下载的视频数量: {playlist_count}（初始: {self.playlist_count}，已跳过 {self.playlist_count - playlist_count} 个已下载的视频）", "info")
                # 使用yt-dlp在实际下载时提供的准确数量
                self.playlist_count = playlist_count
            elif self.playlist_count is None:
                # 如果d中没有，尝试从self中获取（fallback）
                playlist_count = self.playlist_count
            
            if playlist_index is not None:
                self.current_playlist_index = playlist_index
            elif self.current_playlist_index is None:
                # 如果d中没有，初始化为1
                self.current_playlist_index = 1
            
            # 使用self中保存的playlist_count（更可靠）
            if self.playlist_count is not None:
                playlist_count = self.playlist_count
            
            if d.get('status') == 'downloading':
                # 如果所有视频已完成，不再处理下载状态
                if self.all_videos_completed:
                    return
                
                # 提取当前视频的进度百分比，转化为0.0-1.0的浮点数
                current_video_percent = 0.0
                try:
                    if 'total_bytes' in d and d['total_bytes'] and d['total_bytes'] > 0:
                        current_video_percent = d.get('downloaded_bytes', 0) / d['total_bytes']
                    elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] and d['total_bytes_estimate'] > 0:
                        current_video_percent = d.get('downloaded_bytes', 0) / d['total_bytes_estimate']
                    else:
                        # 容错：没有进度信息，直接返回
                        return
                    
                    # 确保进度在0-1范围内
                    current_video_percent = max(0.0, min(1.0, current_video_percent))
                except (ZeroDivisionError, KeyError, TypeError, ValueError) as e:
                    # 容错：解析百分比时（如"Unknown%"）不会导致程序崩溃
                    return
                
                # 计算核心公式：全局总进度
                if playlist_count is not None and playlist_count > 1:
                    # 列表下载模式
                    # 使用已完成数量和当前视频进度来计算总进度
                    # 公式：global_progress = (completed_count + current_video_percent) / playlist_count
                    global_progress = (self.completed_count + current_video_percent) / playlist_count
                    # 确保进度在0-1范围内
                    global_progress = max(0.0, min(1.0, global_progress))
                    current_idx = self.completed_count + 1  # 当前正在下载的是第 completed_count + 1 个
                else:
                    # 单视频下载模式
                    global_progress = current_video_percent
                    current_idx = None
                    playlist_count = None
                
                # UI更新逻辑：下载状态
                # 制定进度条self.progress_bar.set(global_progress)
                self.progress_bar.set(global_progress)
                global_percent = int(global_progress * 100)
                
                # 更新按钮文字显示详情
                if playlist_count is not None and playlist_count > 1:
                    # 列表下载：显示 "正在下载 (3/50) - 15%"
                    self.download_btn.configure(text=f"正在下载 ({current_idx}/{playlist_count}) - {global_percent}%")
                    self.progress_label.configure(text=f"总进度: {global_percent}% | 已完成: {self.completed_count}/{playlist_count} | 当前视频: {int(current_video_percent * 100)}%")
                else:
                    # 单视频下载
                    self.download_btn.configure(text=f"正在下载 - {global_percent}%")
                    self.progress_label.configure(text=f"下载进度: {global_percent}%")
            
            elif d.get('status') == 'finished':
                # 完成状态处理
                # 如果所有视频已完成，不再处理
                if self.all_videos_completed:
                    return
                
                # 使用self中保存的信息（优先使用从progress_hook中获取的实际数量）
                playlist_count = self.playlist_count
                
                # 如果playlist_count还没有设置，说明还没有开始实际下载，暂时不处理
                if playlist_count is None:
                    return
                
                # 增加完成计数器（防止重复计数）
                if playlist_count is not None and playlist_count > 1:
                    # 列表下载模式：只有当完成数量小于总数时才增加
                    if self.completed_count < playlist_count:
                        self.completed_count += 1
                else:
                    # 单视频下载模式
                    if self.completed_count == 0:
                        self.completed_count = 1
                
                # 关键判断：只有当所有视频都下载完成时才显示100%
                if playlist_count is not None and playlist_count > 1:
                    # 列表下载模式
                    # 按照实际下载完成的视频数量显示对应的百分比
                    global_progress = self.completed_count / playlist_count
                    global_progress = max(0.0, min(1.0, global_progress))
                    global_percent = int(global_progress * 100)
                    
                    # 只有当完成数量真正等于总数时才认为全部完成
                    if self.completed_count >= playlist_count:
                        # 所有视频都下载完成，显示100%
                        self.all_videos_completed = True  # 设置完成标志
                        self.progress_bar.set(1.0)
                        self.download_btn.configure(text="全部完成！")
                        self.progress_label.configure(text="全部完成: 100%")
                        self.log(f"所有 {playlist_count} 个视频下载完成！（已完成: {self.completed_count}）", "info")
                        # 取消下载，防止重复下载
                        if self.ydl_instance is not None:
                            try:
                                self.ydl_instance.cancel_download()
                            except:
                                pass
                    else:
                        # 如果只是列表中途的一个视频完成，不要重置进度条，只打印日志
                        # 保持当前进度，不重置
                        self.progress_bar.set(global_progress)
                        self.download_btn.configure(text=f"正在下载 ({self.completed_count}/{playlist_count}) - {global_percent}%")
                        self.progress_label.configure(text=f"总进度: {global_percent}% | 已完成: {self.completed_count}/{playlist_count}")
                        # 只打印日志
                        self.log(f"视频 {self.completed_count}/{playlist_count} 下载完成", "info")
                else:
                    # 单视频下载模式，全部完成
                    # 将进度条强制设为1.0(100%)并显示"下载完成"
                    self.all_videos_completed = True  # 设置完成标志
                    self.progress_bar.set(1.0)
                    self.download_btn.configure(text="下载完成！")
                    self.progress_label.configure(text="下载完成: 100%")
                    # 取消下载，防止重复下载
                    if self.ydl_instance is not None:
                        try:
                            self.ydl_instance.cancel_download()
                        except:
                            pass
                
                # 记录文件信息
                if 'filename' in d:
                    try:
                        filename = os.path.basename(d['filename'])
                        self.log(f"文件保存为: {filename}", "info")
                    except:
                        pass  # 容错：文件名解析失败时忽略
        
        except Exception as e:
            # 容错：确保在解析错误时不会导致程序崩溃
            pass
    
    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        return shutil.which('ffmpeg') is not None
    
    def wait_if_paused(self):
        """等待暂停状态解除（用于准备阶段）"""
        while self.is_paused:
            time.sleep(0.1)
            # 在等待期间，可以更新UI提示用户当前处于暂停状态
            if self.is_downloading:
                self.progress_label.configure(text="已暂停，等待继续...")
                # 暂停时进度条显示灰色
                self.progress_bar.configure(progress_color="#757575")
        
        # 暂停状态已解除，进度条恢复正常颜色和显示
        if self.is_downloading:
            self.progress_bar.configure(progress_color="#1f538d")
            # 准备中时，由暂停状态恢复继续状态后，进度条显示改为准备中...显示
            self.progress_label.configure(text="准备中...")
    
    def extract_info_with_pause_check(self, ydl, url):
        """可中断的extract_info包装函数，在执行过程中检查暂停状态"""
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        
        def extract_worker():
            """在单独线程中执行extract_info"""
            try:
                info = ydl.extract_info(url, download=False)
                result_queue.put(info)
            except Exception as e:
                exception_queue.put(e)
        
        # 在单独线程中执行extract_info
        extract_thread = threading.Thread(target=extract_worker, daemon=True)
        extract_thread.start()
        
        # 等待结果，期间检查暂停状态
        while extract_thread.is_alive():
            # 检查是否有结果
            try:
                info = result_queue.get_nowait()
                # 获取列表后立即检查暂停状态
                self.wait_if_paused()
                return info
            except queue.Empty:
                pass
            
            # 检查是否有异常
            try:
                exception = exception_queue.get_nowait()
                raise exception
            except queue.Empty:
                pass
            
            # 检查暂停状态
            if self.is_paused:
                # 如果暂停了，等待继续（但extract_info会继续执行）
                time.sleep(0.1)
                if self.is_downloading:
                    self.progress_label.configure(text="已暂停，等待继续...（正在获取列表）")
                    # 暂停时进度条显示灰色
                    self.progress_bar.configure(progress_color="#757575")
            else:
                time.sleep(0.1)  # 短暂等待，避免CPU占用过高
                # 非暂停状态，进度条恢复正常颜色
                if self.is_downloading:
                    self.progress_bar.configure(progress_color="#1f538d")
                    # 准备中时，由暂停状态恢复继续状态后，进度条显示改为准备中...显示
                    if self.progress_label.cget("text") in ["已暂停，等待继续...（正在获取列表）", "已暂停，等待继续..."]:
                        self.progress_label.configure(text="正在获取视频列表...")
        
        # 线程已结束，获取结果
        try:
            info = result_queue.get(timeout=0.1)
            # 获取列表后立即检查暂停状态
            self.wait_if_paused()
            return info
        except queue.Empty:
            # 检查是否有异常
            try:
                exception = exception_queue.get(timeout=0.1)
                raise exception
            except queue.Empty:
                # 如果都没有，可能是超时，尝试再次获取
                if not result_queue.empty():
                    info = result_queue.get()
                    self.wait_if_paused()
                    return info
                raise Exception("获取视频列表超时")
    
    def download_worker(self):
        """下载工作线程"""
        ydl_opts = None  # 初始化ydl_opts变量
        format_str = None  # 初始化format_str变量
        save_path = None  # 初始化save_path变量
        url = None  # 初始化url变量
        cookie_selection = None  # 初始化cookie_selection变量
        cookie_type = None  # 初始化cookie_type变量
        
        try:
            # 优先使用保存的链接，如果没有则使用输入框的值
            url = self.current_download_url if self.current_download_url else self.link_entry.get().strip()
            if not url:
                self.log("错误: 请输入视频链接", "error")
                self.is_downloading = False
                self.download_btn.configure(text="开始批量下载", state="normal")
                return
            
            save_path = self.path_entry.get().strip()
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            
            # 确保保存路径存在
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            self.log(f"开始下载: {url}", "info")
            self.log(f"保存路径: {save_path}", "info")
            
            # 检查暂停状态（准备阶段）
            self.wait_if_paused()
            
            # === 下载模式配置 ===
            download_mode = self.download_mode_var.get()
            postprocessors = []
            
            if "仅音频" in download_mode:
                # 仅音频模式
                format_str = 'bestaudio/best'
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                self.log("🎵 已启用纯音频下载模式 (MP3)", "info")
            elif "仅视频" in download_mode:
                # 仅视频模式（无声）
                format_str = 'bestvideo/best'
                self.log("🎬 已启用纯视频下载模式 (无声)", "info")
            else:
                # 最佳音画模式（默认）
                has_ffmpeg = self.check_ffmpeg()
                if has_ffmpeg:
                    format_str = 'bv*[height>=2160]+ba/b[height>=2160]/bv*[height>=1080]+ba/b[height>=1080]/bv*[height>=720]+ba/b[height>=720]/bestvideo+bestaudio/best'
                    self.log("检测到ffmpeg，将优先下载4K/1080P高清视频", "info")
                else:
                    format_str = 'b[height>=2160]/b[height>=1080]/b[height>=720]/best'
                    self.log("未检测到ffmpeg，将下载单文件格式", "warning")
            
            # 检查暂停状态（配置前）
            self.wait_if_paused()
            
            # === 网络代理配置 ===
            proxy_url = None
            if self.proxy_enabled_var.get():
                proxy_input = self.proxy_entry.get().strip()
                if proxy_input:
                    proxy_url = proxy_input
                    self.log(f"🌐 已启用网络代理: {proxy_url}", "info")
            
            # === 动态配置 Cookie ===
            cookie_selection = self.cookie_source_var.get()
            cookie_config = {}
            cookie_type = None  # 记录Cookie类型，用于错误处理
            browser_name = None  # 初始化浏览器名称，用于错误处理
            self.log(f"登录凭证来源: {cookie_selection}", "info")
            
            if "本地 cookies.txt" in cookie_selection:
                # 本地文件模式：检测当前目录下是否存在 cookies.txt
                local_cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
                if os.path.exists(local_cookie_path):
                    # 验证文件是否可以读取
                    try:
                        with open(local_cookie_path, 'r', encoding='utf-8') as f:
                            # 简单验证：至少读取一行
                            first_line = f.readline()
                            if not first_line.strip():
                                raise ValueError("cookies.txt文件为空")
                        cookie_config = {'cookiefile': local_cookie_path}
                        cookie_type = 'cookiefile'
                        self.log("✅ 成功加载本地 cookies.txt", "info")
                    except Exception as e:
                        self.log(f"❌ cookies.txt 文件读取失败: {str(e)}，已降级为不登录模式", "warning")
                        cookie_config = {}
                else:
                    self.log("❌ 未找到 cookies.txt！已降级为不登录模式", "warning")
                    cookie_config = {}  # 降级为不使用Cookie
            elif "不使用登录" in cookie_selection:
                # 不使用登录模式：不配置任何Cookie参数
                cookie_config = {}
            else:
                # 浏览器模式：提取选中项的第一个词（如 "Edge"），转换为小写
                browser_display_name = cookie_selection.split(" ")[0]
                browser_name = browser_display_name.lower()
                
                # Edge浏览器的特殊处理：直接使用 'edge'，让 yt-dlp 内部处理
                if 'edge' in browser_name:
                    browser_name = 'edge'
                
                # 配置Cookie
                cookie_config = {'cookiesfrombrowser': (browser_name,)}
                cookie_type = 'cookiesfrombrowser'
                self.log(f"使用 {cookie_selection} 的 Cookie", "info")
            
            # 配置下载选项
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(save_path, '%(uploader)s/%(title)s.%(ext)s'),
                'download_archive': os.path.join(save_path, 'archive.txt'),
                'ignoreerrors': True,
                'writethumbnail': True,
                'progress_hooks': [self.progress_hook],
                'logger': MyLogger(self.log_text, self.log_queue, app=self),
            }
            # 添加后处理器（仅音频模式）
            if postprocessors:
                ydl_opts['postprocessors'] = postprocessors
            # 合并代理配置
            if proxy_url:
                ydl_opts['proxy'] = proxy_url
            # 合并Cookie配置
            if cookie_config:
                ydl_opts.update(cookie_config)
            
            # 开始下载 - 包装在try-except中捕获初始化错误
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # 保存ydl实例，用于取消下载
                    self.ydl_instance = ydl
                    
                    # 检查暂停状态（准备阶段）
                    self.wait_if_paused()
                    
                    # 提取信息查看有多少个视频（使用可中断的包装函数）
                    self.log("正在获取视频列表...", "info")
                    info = self.extract_info_with_pause_check(ydl, url)
                    
                    if 'entries' in info:
                        # 解析正确的视频数量（过滤掉None）
                        entries = [e for e in info['entries'] if e is not None]
                        total = len(entries)
                        # 初始视频数量（所有视频，包括已下载的）
                        initial_count = total
                        # 注意：实际要下载的数量可能少于这个数量（因为download_archive会跳过已下载的）
                        # 实际数量会在progress_hook中从yt-dlp获取
                        self.playlist_count = total  # 初始值，会在progress_hook中更新为实际值
                        self.current_playlist_index = 1  # 初始化当前索引为1
                        self.completed_count = 0  # 重置完成计数器
                        self.all_videos_completed = False  # 重置完成标志
                        self.log(f"找到 {initial_count} 个视频（实际下载数量将在下载过程中确定）...", "info")
                    else:
                        # 单视频
                        self.playlist_count = None
                        self.current_playlist_index = None
                        self.completed_count = 0
                        self.all_videos_completed = False  # 重置完成标志
                    
                    # 检查暂停状态（开始下载前）
                    self.wait_if_paused()
                    
                    # 检查是否已完成（防止重复下载）
                    if self.all_videos_completed:
                        self.log("所有视频已完成，停止下载", "info")
                        return
                    
                    # 开始下载（暂停逻辑在progress_hook中处理）
                    try:
                        ydl.download([url])
                    except Exception as download_error:
                        # 如果是因为取消下载导致的异常，这是正常的
                        if self.all_videos_completed:
                            # 所有视频已完成，取消下载是正常的
                            self.log("批量下载完成！", "info")
                            self.progress_label.configure(text="下载完成！")
                            return
                        else:
                            # 其他异常，重新抛出
                            raise
                    
                    # 下载完成后，检查是否真的全部完成
                    if self.all_videos_completed:
                        self.log("批量下载完成！", "info")
                        self.progress_label.configure(text="下载完成！")
                        return
            except Exception as init_error:
                # 捕获YoutubeDL初始化时的错误（包括Cookie相关错误）
                error_msg = str(init_error)
                error_type = type(init_error).__name__
                
                # 检查是否是Cookie相关错误
                is_cookie_error = (
                    cookie_type and (
                        'cookie' in error_msg.lower() or 
                        'browser' in error_msg.lower() or
                        'CookieLoadError' in error_type or
                        'database' in error_msg.lower() or
                        'locked' in error_msg.lower()
                    )
                )
                
                if is_cookie_error:
                    # Cookie初始化失败，重新抛出以便外层处理
                    raise init_error
                else:
                    # 其他初始化错误，直接抛出
                    raise init_error
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # 智能容错与降级机制：捕获因Cookie导致的下载错误
            # 检查是否是Cookie相关错误（包括初始化错误）
            is_cookie_error = (
                cookie_type and (
                    'cookie' in error_msg.lower() or 
                    'browser' in error_msg.lower() or
                    'CookieLoadError' in error_type or
                    'database' in error_msg.lower() or
                    'locked' in error_msg.lower() or
                    'sqlite' in error_msg.lower()
                )
            )
            
            if is_cookie_error and ydl_opts:
                # 提供详细的错误信息和解决方案
                if cookie_type == 'cookiesfrombrowser':
                    browser_display_name = cookie_selection.split(" ")[0]
                    self.log(f"⚠️ {browser_display_name} Cookie读取失败", "warning")
                    self.log(f"   错误详情: {error_msg}", "warning")
                    
                    # Edge浏览器特殊提示
                    if 'edge' in str(cookie_selection).lower():
                        self.log("🛑【Edge 特别注意】：Edge 的 Cookie 数据库通常被后台进程锁定。", "warning")
                        self.log("👉 请尝试：1. 关闭所有 Edge 窗口。", "warning")
                        self.log("👉 2. 打开任务管理器，强制结束所有 'Microsoft Edge' 进程。", "warning")
                        self.log("👉 3. 或者使用 '本地 cookies.txt' 模式。", "warning")
                    else:
                        self.log("   可能的原因：", "warning")
                        self.log("   1. 浏览器正在运行，请先关闭浏览器后重试", "warning")
                        self.log("   2. 浏览器Cookie数据库被锁定", "warning")
                        self.log("   3. 权限不足，请以管理员身份运行", "warning")
                        self.log("   4. 浏览器Cookie数据库不存在或已损坏", "warning")
                elif cookie_type == 'cookiefile':
                    self.log(f"⚠️ cookies.txt 文件读取失败", "warning")
                    self.log(f"   错误详情: {error_msg}", "warning")
                    self.log("   可能的原因：", "warning")
                    self.log("   1. cookies.txt 文件格式不正确", "warning")
                    self.log("   2. cookies.txt 文件已损坏或为空", "warning")
                    self.log("   3. 文件权限不足，无法读取", "warning")
                
                self.log("🔄 正在尝试以降级模式（不使用登录）重试...", "info")
                
                # 重新构建ydl_opts，移除Cookie配置（但保留代理配置和下载模式配置）
                ydl_opts_no_cookie = {
                    'format': format_str,
                    'outtmpl': os.path.join(save_path, '%(uploader)s/%(title)s.%(ext)s'),
                    'download_archive': os.path.join(save_path, 'archive.txt'),
                    'ignoreerrors': True,
                    'writethumbnail': True,
                    'progress_hooks': [self.progress_hook],
                    'logger': MyLogger(self.log_text, self.log_queue, app=self),
                }
                # 保留后处理器配置（仅音频模式）
                if postprocessors:
                    ydl_opts_no_cookie['postprocessors'] = postprocessors
                # 保留代理配置
                if proxy_url:
                    ydl_opts_no_cookie['proxy'] = proxy_url
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts_no_cookie) as ydl:
                        # 保存ydl实例，用于取消下载
                        self.ydl_instance = ydl
                        
                        # 检查暂停状态（准备阶段）
                        self.wait_if_paused()
                        
                        # 提取信息查看有多少个视频（使用可中断的包装函数）
                        self.log("正在获取视频列表...", "info")
                        info = self.extract_info_with_pause_check(ydl, url)
                        
                        if 'entries' in info:
                            # 解析正确的视频数量（过滤掉None）
                            entries = [e for e in info['entries'] if e is not None]
                            total = len(entries)
                            # 初始视频数量（所有视频，包括已下载的）
                            initial_count = total
                            # 注意：实际要下载的数量可能少于这个数量（因为download_archive会跳过已下载的）
                            # 实际数量会在progress_hook中从yt-dlp获取
                            self.playlist_count = total  # 初始值，会在progress_hook中更新为实际值
                            self.current_playlist_index = 1  # 初始化当前索引为1
                            self.completed_count = 0  # 重置完成计数器
                            self.all_videos_completed = False  # 重置完成标志
                            self.log(f"找到 {initial_count} 个视频（实际下载数量将在下载过程中确定，已降级为不登录模式）...", "info")
                        else:
                            self.playlist_count = None
                            self.current_playlist_index = None
                            self.completed_count = 0
                            self.all_videos_completed = False  # 重置完成标志
                        
                        # 检查暂停状态（开始下载前）
                        self.wait_if_paused()
                        
                        # 检查是否已完成（防止重复下载）
                        if self.all_videos_completed:
                            self.log("所有视频已完成，停止下载", "info")
                            return
                        
                        # 开始下载（暂停逻辑在progress_hook中处理）
                        try:
                            ydl.download([url])
                        except Exception as download_error:
                            # 如果是因为取消下载导致的异常，这是正常的
                            if self.all_videos_completed:
                                # 所有视频已完成，取消下载是正常的
                                self.log("批量下载完成！（已降级为不登录模式，可能画质较低）", "info")
                                return
                            else:
                                # 其他异常，重新抛出
                                raise
                        
                        # 下载完成后，检查是否真的全部完成
                        if self.all_videos_completed:
                            self.log("批量下载完成！（已降级为不登录模式，可能画质较低）", "info")
                            return
                    self.log("批量下载完成！（已降级为不登录模式，可能画质较低）", "info")
                except Exception as e2:
                    self.log(f"下载失败: {str(e2)}", "error")
            else:
                self.log(f"下载失败: {error_msg}", "error")
        
        finally:
            # 结束处理：重置所有状态
            # 联动逻辑：当下载线程彻底结束（或者成功失败），重置暂停按钮不可用
            self.is_downloading = False
            self.is_paused = False  # 确保self.is_paused恢复为False（防止下次开始直接卡死）
            self.all_videos_completed = False  # 重置完成标志
            self.ydl_instance = None  # 清除ydl实例
            self.download_btn.configure(text="开始批量下载", state="normal")
            self.btn_pause.configure(state="disabled", text="⏸ 暂停任务", fg_color="#d32f2f", hover_color="#b71c1c")
            self.progress_bar.set(0)
            self.progress_bar.configure(progress_color="#1f538d")  # 进度条恢复正常颜色
    
    def toggle_pause(self):
        """暂停/继续下载 - 全盘暂停功能"""
        if not self.is_downloading:
            return
        
        if self.is_paused:
            # 继续任务 - 显示绿色
            # 检查链接是否改变
            new_url = self.link_entry.get().strip()
            if new_url and new_url != self.current_download_url:
                # 暂停任务后，若有下载链接修改，需要切到新的下载链接进行视频下载
                self.log(f"检测到链接已更改，切换到新链接: {new_url}", "info")
                # 停止当前下载线程
                self.is_paused = False
                self.is_downloading = False
                # 重置状态
                self.playlist_count = None
                self.current_playlist_index = None
                self.completed_count = 0
                self.all_videos_completed = False  # 重置完成标志
                # 使用新链接重新开始下载
                self.current_download_url = new_url
                self.log_text.delete("1.0", "end")
                self.download_btn.configure(text="准备中...", state="disabled")
                self.btn_pause.configure(state="normal", text="⏸ 暂停任务", fg_color="#d32f2f", hover_color="#b71c1c")
                self.progress_bar.set(0)
                self.progress_bar.configure(progress_color="#1f538d")
                self.progress_label.configure(text="准备中...")
                # 在新线程中运行下载
                self.is_downloading = True
                self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
                self.download_thread.start()
                return
            
            # 链接未改变，继续当前下载
            self.is_paused = False
            self.btn_pause.configure(text="⏸ 暂停任务", fg_color="#d32f2f", hover_color="#b71c1c")
            self.log("▶️ 任务继续...", "info")
            # 进度条恢复正常显示
            self.progress_bar.configure(progress_color="#1f538d")
            # 准备中时，由暂停状态恢复继续状态后，进度条显示改为准备中...显示
            current_progress = self.progress_bar.get()
            if current_progress == 0.0 or self.progress_label.cget("text") in ["已暂停，等待继续...", "准备中..."]:
                self.progress_label.configure(text="准备中...")
        else:
            # 暂停任务 - 显示红色
            self.is_paused = True
            self.btn_pause.configure(text="▶ 继续任务", fg_color="#388e3c", hover_color="#2e7d32")
            self.log("⏸️ 任务已暂停...", "warning")
            # 进度条显示暂停状态（灰色）
            self.progress_bar.configure(progress_color="#757575")
    
    def start_download(self):
        """开始下载"""
        if self.is_downloading and not self.is_paused:
            return
        
        # 如果是暂停状态，继续下载
        if self.is_paused:
            self.toggle_pause()
            return
        
        # 获取当前链接
        url = self.link_entry.get().strip()
        if not url:
            self.log("错误: 请输入视频链接", "error")
            return
        
        # 清空日志
        self.log_text.delete("1.0", "end")
        
        # 保存当前下载链接
        self.current_download_url = url
        
        # 重置播放列表信息和暂停状态
        self.playlist_count = None
        self.current_playlist_index = None
        self.completed_count = 0  # 重置完成计数器
        self.all_videos_completed = False  # 重置完成标志
        self.is_paused = False
        
        # 更新状态
        self.is_downloading = True
        self.download_btn.configure(text="准备中...", state="disabled")
        # 联动逻辑：当"开始下载"被点击时，激活暂停按钮（红色，暂停状态）
        self.btn_pause.configure(state="normal", text="⏸ 暂停任务", fg_color="#d32f2f", hover_color="#b71c1c")
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="#1f538d")  # 进度条正常颜色（蓝色）
        self.progress_label.configure(text="准备中...")
        
        # 在新线程中运行下载
        self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.download_thread.start()
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def check_license():
    """
    检查激活状态
    
    Returns:
        Tuple[bool, str]: (True, message) 表示已激活，message 包含过期时间信息
                         (False, None) 表示需要激活
    """
    license_file = os.path.join(os.getcwd(), ActivationApp.LICENSE_FILE)
    
    # 检查激活码文件是否存在
    if not os.path.exists(license_file):
        return (False, None)
    
    # 读取激活码
    try:
        with open(license_file, 'r', encoding='utf-8') as f:
            license_key = f.read().strip()
        
        if not license_key:
            # 文件为空，删除文件
            os.remove(license_file)
            return (False, None)
        
        # 静默验证激活码
        client = LicenseClient()
        result, message = client.verify_online(license_key)
        
        if result:
            # 验证通过，返回 (True, message)
            return (True, message)
        else:
            # 验证失败（过期或被封禁），删除激活码文件
            try:
                os.remove(license_file)
            except:
                pass
            return (False, None)
    
    except Exception as e:
        # 读取或验证过程出错，删除文件
        try:
            if os.path.exists(license_file):
                os.remove(license_file)
        except:
            pass
        return (False, None)


def start_main_app(license_info=""):
    """启动主程序"""
    app = BiliDownloaderGUI(license_info=license_info)
    app.run()


def start_activation_app():
    """启动激活窗口"""
    activation_app = ActivationApp(callback=start_main_app)
    activation_app.run()


if __name__ == '__main__':
    # 启动检查：验证激活状态
    is_valid, license_msg = check_license()
    if is_valid:
        # 已激活，直接启动主程序，传递授权信息
        start_main_app(license_info=license_msg)
    else:
        # 未激活或验证失败，显示激活窗口
        start_activation_app()
