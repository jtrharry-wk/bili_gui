@echo off
chcp 65001 >nul
echo ========================================
echo 软件打包脚本
echo ========================================
echo.

echo 正在检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [错误] 未安装 PyInstaller
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 选择要打包的程序：
echo ========================================
echo 1. bili_gui.py (Bilibili批量下载神器)
echo 2. admin_tool_gui.py (激活码管理工具)
echo 3. 全部打包
echo.
set /p choice="请输入选项 (1/2/3): "

if "%choice%"=="1" goto build_bili
if "%choice%"=="2" goto build_admin
if "%choice%"=="3" goto build_all
echo [错误] 无效的选项
pause
exit /b 1

:build_bili
echo.
echo ========================================
echo 正在打包 bili_gui.py...
echo ========================================
if exist build rmdir /s /q build
if exist dist\bili_gui.exe del /q dist\bili_gui.exe
pyinstaller bili_gui.spec
if errorlevel 1 (
    echo [错误] bili_gui 打包失败
    pause
    exit /b 1
)
echo.
echo [成功] bili_gui.exe 打包完成！
echo 位置: dist\bili_gui.exe
goto end

:build_admin
echo.
echo ========================================
echo 正在打包 admin_tool_gui.py...
echo ========================================
if exist build rmdir /s /q build
if exist dist\admin_tool_gui.exe del /q dist\admin_tool_gui.exe
pyinstaller admin_tool_gui.spec
if errorlevel 1 (
    echo [错误] admin_tool_gui 打包失败
    pause
    exit /b 1
)
echo.
echo [成功] admin_tool_gui.exe 打包完成！
echo 位置: dist\admin_tool_gui.exe
goto end

:build_all
echo.
echo ========================================
echo 正在打包所有程序...
echo ========================================
echo.
echo [1/2] 打包 bili_gui.py...
if exist build rmdir /s /q build
if exist dist\bili_gui.exe del /q dist\bili_gui.exe
pyinstaller bili_gui.spec
if errorlevel 1 (
    echo [错误] bili_gui 打包失败
    pause
    exit /b 1
)
echo [成功] bili_gui.exe 打包完成！
echo.
echo [2/2] 打包 admin_tool_gui.py...
if exist build rmdir /s /q build
if exist dist\admin_tool_gui.exe del /q dist\admin_tool_gui.exe
pyinstaller admin_tool_gui.spec
if errorlevel 1 (
    echo [错误] admin_tool_gui 打包失败
    pause
    exit /b 1
)
echo [成功] admin_tool_gui.exe 打包完成！
echo.
echo ========================================
echo [成功] 所有程序打包完成！
echo ========================================
echo bili_gui.exe: dist\bili_gui.exe
echo admin_tool_gui.exe: dist\admin_tool_gui.exe
goto end

:end
echo.
pause
