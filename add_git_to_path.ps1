# 将 Git 添加到系统 PATH（需要管理员权限）
# 使用方法：以管理员身份运行 PowerShell，然后执行此脚本

Write-Host "正在查找 Git 安装路径..." -ForegroundColor Yellow

# 常见的 Git 安装路径
$possiblePaths = @(
    "C:\Program Files\Git\cmd",
    "C:\Program Files (x86)\Git\cmd",
    "$env:LOCALAPPDATA\Programs\Git\cmd"
)

$gitPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $gitPath = $path
        Write-Host "找到 Git: $gitPath" -ForegroundColor Green
        break
    }
}

if (-not $gitPath) {
    Write-Host "错误: 未找到 Git 安装路径" -ForegroundColor Red
    Write-Host "请先安装 Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 获取当前 PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# 检查是否已在 PATH 中
if ($currentPath -like "*$gitPath*") {
    Write-Host "Git 已存在于 PATH 中" -ForegroundColor Green
    exit 0
}

# 添加到 PATH
Write-Host "正在添加 Git 到 PATH..." -ForegroundColor Yellow
$newPath = $currentPath + ";" + $gitPath
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "成功！Git 已添加到 PATH" -ForegroundColor Green
Write-Host "请重新打开终端窗口以使更改生效" -ForegroundColor Yellow
