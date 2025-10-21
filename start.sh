#!/bin/bash

echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🏆 Alpha Arena - DeepSeek-V3 Trading Bot         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip3 install -r requirements.txt -q

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "❌ 配置文件 .env 不存在"
    exit 1
fi

# 启动机器人
echo "🚀 启动 Alpha Arena Bot..."
echo ""

python3 alpha_arena_bot.py
