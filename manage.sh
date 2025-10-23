#!/bin/bash

# Alpha Arena 管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$1" in
    start)
        echo "🚀 启动 Alpha Arena Bot..."
        python3 alpha_arena_bot.py
        ;;

    dashboard)
        echo "🌐 启动 Web 仪表板..."
        python3 web_dashboard.py
        ;;

    logs)
        echo "📝 查看实时日志（彩色终端输出）..."
        echo "提示: 此命令显示后台运行进程的日志"
        echo "如需查看文件日志，使用: tail -f logs/alpha_arena_*.log"
        echo ""

        # 检查是否有运行中的进程
        if pgrep -f "alpha_arena_bot.py" > /dev/null; then
            echo "✅ 检测到运行中的机器人进程"
            echo "正在显示实时输出..."
            echo ""
            # 使用ps找到进程并跟踪其输出
            # 如果进程在screen中运行，提示用户连接到screen
            if screen -ls | grep -q "alpha_arena"; then
                echo "⚠️  Bot 在 screen 会话中运行"
                echo "使用以下命令查看彩色日志:"
                echo "  screen -r alpha_arena"
                echo ""
                echo "或查看文件日志:"
                tail -f logs/alpha_arena_*.log 2>/dev/null || echo "❌ 日志文件不存在"
            else
                echo "显示文件日志 (无彩色格式):"
                tail -f logs/alpha_arena_*.log 2>/dev/null || echo "❌ 日志文件不存在"
            fi
        else
            echo "⚠️  未检测到运行中的进程"
            echo "显示最近的日志文件:"
            if ls logs/alpha_arena_*.log 1> /dev/null 2>&1; then
                tail -n 50 logs/alpha_arena_$(date +%Y%m%d).log 2>/dev/null || tail -n 50 $(ls -t logs/alpha_arena_*.log | head -1)
            else
                echo "❌ 日志文件不存在"
            fi
        fi
        ;;

    status)
        echo "📊 性能状态..."
        if [ -f "performance_data.json" ]; then
            python3 -c "
import json
with open('performance_data.json', 'r') as f:
    data = json.load(f)
    metrics = data.get('metrics', {})
    print('╔══════════════════════════════════════╗')
    print('║    DeepSeek-V3 AI 交易机器人状态     ║')
    print('╠══════════════════════════════════════╣')
    print(f'║ 账户价值: \${metrics.get(\"account_value\", 0):,.2f}')
    print(f'║ 总收益率: {metrics.get(\"total_return_pct\", 0):+.2f}%')
    print(f'║ 夏普比率: {metrics.get(\"sharpe_ratio\", 0):.2f}')
    print(f'║ 交易次数: {metrics.get(\"total_trades\", 0)}')
    print(f'║ 胜率: {metrics.get(\"win_rate_pct\", 0):.1f}%')
    print('╚══════════════════════════════════════╝')
"
        else
            echo "❌ 性能数据文件不存在"
        fi
        ;;

    install)
        echo "📦 安装依赖..."
        pip3 install -r requirements.txt
        ;;

    stop)
        echo "🛑 停止 Alpha Arena Bot..."
        pkill -f "python3 alpha_arena_bot.py"
        echo "✅ 已停止"
        ;;

    restart)
        echo "🔄 重启 Alpha Arena Bot..."
        $0 stop
        sleep 2
        $0 start
        ;;

    screen)
        echo "📺 在 screen 会话中启动..."
        screen -dmS alpha_arena bash -c "cd $SCRIPT_DIR && ./start.sh"
        echo "✅ Bot 已在后台启动"
        echo "   重新连接: screen -r alpha_arena"
        ;;

    help|*)
        echo "╔══════════════════════════════════════════════════╗"
        echo "║     DeepSeek AI 交易机器人 - 管理脚本          ║"
        echo "╚══════════════════════════════════════════════════╝"
        echo ""
        echo "📖 用法: ./manage.sh [命令]"
        echo ""
        echo "🎯 可用命令:"
        echo "  start      - 🚀 启动交易机器人"
        echo "  dashboard  - 🌐 启动 Web 仪表板 (http://localhost:5000)"
        echo "  logs       - 📝 查看实时日志"
        echo "  status     - 📊 查看当前性能状态"
        echo "  install    - 📦 安装 Python 依赖"
        echo "  stop       - 🛑 停止运行中的机器人"
        echo "  restart    - 🔄 重启机器人"
        echo "  screen     - 📺 在 screen 后台启动"
        echo "  help       - ❓ 显示此帮助信息"
        echo ""
        echo "💡 使用示例:"
        echo "  ./manage.sh start      # 前台启动机器人（可看彩色日志）"
        echo "  ./manage.sh screen     # 后台运行（推荐）"
        echo "  ./manage.sh status     # 查看账户状态和收益"
        echo "  ./manage.sh logs       # 查看日志输出"
        echo ""
        echo "🔗 相关命令:"
        echo "  screen -r alpha_arena  # 连接到后台 screen 会话"
        echo "  screen -d              # 从 screen 会话中分离"
        echo ""
        ;;
esac
