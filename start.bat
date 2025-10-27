@echo off
REM Windows 启动脚本
chcp 65001 >nul

echo 🚀 启动 Telegram 支付 Bot...

REM 进入脚本所在目录
cd /d %~dp0

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
python -c "import telegram" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 安装依赖...
    pip install -r requirements.txt
)

REM 检查配置文件
if not exist ".env" (
    echo ⚠️  未找到 .env 配置文件
    echo 请复制 .env.example 为 .env 并填写配置
    pause
    exit /b 1
)

REM 启动 Bot
echo ✅ 启动中...
python bot.py

pause



