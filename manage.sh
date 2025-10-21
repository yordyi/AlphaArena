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
        echo "📝 查看日志..."
        tail -f logs/alpha_arena_*.log
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
    print('║   Alpha Arena - DeepSeek-V3 Status   ║')
    print('╠══════════════════════════════════════╣')
    print(f'║ Account Value: \${metrics.get(\"account_value\", 0):,.2f}')
    print(f'║ Total Return:  {metrics.get(\"total_return_pct\", 0):+.2f}%')
    print(f'║ Sharpe Ratio:  {metrics.get(\"sharpe_ratio\", 0):.2f}')
    print(f'║ Total Trades:  {metrics.get(\"total_trades\", 0)}')
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
        echo "Alpha Arena 管理脚本"
        echo ""
        echo "用法: ./manage.sh [命令]"
        echo ""
        echo "命令:"
        echo "  start      - 启动交易机器人"
        echo "  dashboard  - 启动 Web 仪表板"
        echo "  logs       - 查看实时日志"
        echo "  status     - 查看当前状态"
        echo "  install    - 安装依赖"
        echo "  stop       - 停止机器人"
        echo "  restart    - 重启机器人"
        echo "  screen     - 在 screen 后台启动"
        echo "  help       - 显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  ./manage.sh start      # 启动机器人"
        echo "  ./manage.sh dashboard  # 启动仪表板"
        echo "  ./manage.sh screen     # 后台运行"
        ;;
esac
