#!/bin/bash
# Linux/Mac 启动脚本

echo "🚀 启动 Telegram 支付 Bot..."

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import telegram" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 配置文件"
    echo "请复制 .env.example 为 .env 并填写配置"
    exit 1
fi

# 启动 Bot
echo "✅ 启动中..."
python bot.py







