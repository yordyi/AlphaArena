#!/bin/bash
###############################################################################
# Alpha Arena - 清理重启脚本 (V3.4)
# 功能: 安全地清理所有旧进程并重启单一实例
###############################################################################

set -e  # 遇到错误立即退出

echo "🔄 Alpha Arena 清理重启脚本 v3.3"
echo "========================================"
echo ""

# 步骤1: 清理所有旧进程
echo "🧹 [1/5] 清理旧进程..."
pkill -9 -f "alpha_arena_bot.py" 2>/dev/null || echo "  ℹ️  没有运行中的bot进程"
pkill -9 -f "web_dashboard.py" 2>/dev/null || echo "  ℹ️  没有运行中的dashboard进程"
sleep 3

# 步骤2: 验证进程已清理
echo ""
echo "✅ [2/5] 验证进程清理..."
BOT_COUNT=$(ps aux | grep -c "[a]lpha_arena_bot.py" || true)
DASH_COUNT=$(ps aux | grep -c "[w]eb_dashboard.py" || true)

if [ "$BOT_COUNT" -gt 0 ] || [ "$DASH_COUNT" -gt 0 ]; then
    echo "  ⚠️  警告: 仍有进程残留，强制清理..."
    pkill -9 -f "python.*alpha_arena" 2>/dev/null || true
    sleep 2
fi

# 步骤3: 创建日志目录
echo ""
echo "📁 [3/5] 准备日志目录..."
mkdir -p logs backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 步骤4: 备份性能数据
echo ""
echo "💾 [4/5] 备份性能数据..."
if [ -f "performance_data.json" ]; then
    cp performance_data.json "backups/performance_data_${TIMESTAMP}.json"
    echo "  ✅ 备份完成: backups/performance_data_${TIMESTAMP}.json"
else
    echo "  ℹ️  没有找到performance_data.json"
fi

# 步骤5: 启动新实例
echo ""
echo "🚀 [5/5] 启动系统..."
echo ""

# 启动Bot
echo "  [Bot] 启动中..."
python3 alpha_arena_bot.py > "logs/bot_${TIMESTAMP}.log" 2>&1 &
BOT_PID=$!
echo "  ✅ Bot已启动 (PID: $BOT_PID)"

# 等待2秒
sleep 2

# 启动Dashboard
echo "  [Dashboard] 启动中..."
python3 web_dashboard.py > "logs/dashboard_${TIMESTAMP}.log" 2>&1 &
DASH_PID=$!
echo "  ✅ Dashboard已启动 (PID: $DASH_PID)"

# 等待3秒让服务启动
sleep 3

echo ""
echo "========================================"
echo "✅ 系统重启完成！"
echo ""

# 显示运行状态
echo "📊 当前运行状态:"
echo "----------------------------------------"
ps aux | grep -E "(alpha_arena_bot|web_dashboard)" | grep -v grep | \
    awk '{printf "  PID: %-6s | CPU: %5s%% | MEM: %5s%% | %s\n", $2, $3, $4, $11}'

echo ""
echo "🌐 访问地址:"
echo "  Dashboard: http://localhost:5001"
echo "  Bot日志: tail -f logs/bot_${TIMESTAMP}.log"
echo ""
echo "🔍 健康检查: python3 health_monitor.py"
echo "========================================"
