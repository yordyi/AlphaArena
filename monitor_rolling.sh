#!/bin/bash
# V3.5 滚仓功能实时监控脚本

echo "═══════════════════════════════════════════════════════════"
echo "  Alpha Arena V3.5 - 滚仓功能监控"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 检查bot是否运行
echo "📊 系统状态:"
BOT_PID=$(ps aux | grep alpha_arena_bot.py | grep -v grep | awk '{print $2}')
if [ -n "$BOT_PID" ]; then
    echo "  ✅ Bot运行中 (PID: $BOT_PID)"
else
    echo "  ❌ Bot未运行"
    exit 1
fi
echo ""

# 获取最新日志文件
LOG_FILE="logs/alpha_arena_$(date +%Y%m%d).log"
if [ ! -f "$LOG_FILE" ]; then
    LOG_FILE="bot.log"
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️  日志文件未找到"
    exit 1
fi

echo "📝 最新日志文件: $LOG_FILE"
echo ""

# 显示账户状态
echo "💰 账户状态 (最新):"
grep -A 2 "\[ACCOUNT\] 账户状态:" "$LOG_FILE" | tail -n 3 | sed 's/^/  /'
echo ""

# 显示滚仓检查记录
echo "🎯 滚仓检查记录 (最近5次):"
grep "\[ROLL-CHECK\]" "$LOG_FILE" | tail -n 15 | sed 's/^/  /'
echo ""

# 显示滚仓执行记录
echo "✅ 滚仓执行记录:"
ROLL_COUNT=$(grep -c "滚仓成功" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$ROLL_COUNT" -gt 0 ]; then
    grep "🎯 \[ROLL\]" "$LOG_FILE" -A 5 | tail -n 20 | sed 's/^/  /'
else
    echo "  ⏳ 暂无滚仓执行记录 (等待盈利达到1.5%阈值)"
fi
echo ""

# 显示当前持仓
echo "📈 当前持仓:"
grep "\[SEARCH\]" "$LOG_FILE" | tail -n 3 | sed 's/^/  /'
echo ""

# 显示最新AI决策
echo "🤖 最新AI决策 (最近1次):"
grep "\[AI\] DEEPSEEK" "$LOG_FILE" | tail -n 1 | sed 's/^/  /'
echo ""

# 配置信息
echo "⚙️  V3.5 配置:"
echo "  滚仓阈值: 1.5%"
echo "  加仓比例: 50%"
echo "  最大滚仓: 2次"
echo "  最小间隔: 3分钟"
echo "  交易周期: 120秒 (2分钟)"
echo "  杠杆倍数: 30x"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "💡 提示:"
echo "  - 实时监控: tail -f $LOG_FILE | grep ROLL"
echo "  - 查看完整日志: tail -f $LOG_FILE"
echo "  - 停止bot: ./manage.sh stop 或 kill $BOT_PID"
echo "═══════════════════════════════════════════════════════════"
