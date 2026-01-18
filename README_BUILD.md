# 软件打包说明

## 打包工具

使用 PyInstaller 将 Python 程序打包成可执行文件。

## 打包文件

- `bili_gui.spec` - Bilibili批量下载神器的打包配置
- `admin_tool_gui.spec` - 激活码管理工具的打包配置
- `build_all.bat` - Windows 打包脚本

## 使用方法

### 方法 1：使用打包脚本（推荐）

```bash
build_all.bat
```

运行后会显示菜单：
1. 打包 bili_gui.py
2. 打包 admin_tool_gui.py
3. 全部打包

### 方法 2：手动打包

#### 打包 bili_gui.py

```bash
pyinstaller bili_gui.spec
```

#### 打包 admin_tool_gui.py

```bash
pyinstaller admin_tool_gui.spec
```

## 打包前准备

1. **安装 PyInstaller**：
   ```bash
   pip install pyinstaller
   ```

2. **安装所有依赖**：
   ```bash
   pip install customtkinter yt-dlp requests sqlalchemy fastapi uvicorn
   ```

3. **准备图标文件**（可选）：
   - `bili.ico` - bili_gui 的图标文件
   - 如需为 admin_tool_gui 添加图标，修改 `admin_tool_gui.spec` 中的 `icon` 参数

## 打包输出

打包完成后，可执行文件位于 `dist` 目录：
- `dist\bili_gui.exe` - Bilibili批量下载神器
- `dist\admin_tool_gui.exe` - 激活码管理工具

## 注意事项

1. **文件大小**：打包后的 exe 文件可能较大（包含所有依赖库）
2. **首次运行**：首次运行可能需要几秒钟启动时间
3. **杀毒软件**：某些杀毒软件可能会误报，需要添加信任
4. **依赖文件**：
   - `bili_gui.exe` 需要 `ffmpeg.exe`（如果使用音视频合并功能）
   - 激活验证功能需要验证服务器运行

## 打包配置说明

### bili_gui.spec
- 隐藏导入：`customtkinter`, `license_client`, `yt_dlp`, `PIL`, `requests`
- 无控制台窗口（GUI 模式）
- 使用图标：`bili.ico`

### admin_tool_gui.spec
- 隐藏导入：`customtkinter`, `requests`, `PIL`
- 无控制台窗口（GUI 模式）
- 无图标（可自行添加）

## 常见问题

1. **打包失败**：检查是否安装了所有依赖
2. **运行错误**：确保所有必要的文件都在同一目录
3. **文件过大**：可以使用 `--onefile` 模式，但启动会较慢
