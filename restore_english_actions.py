#!/usr/bin/env python3
"""
恢复AI决策动作的英文显示
移除中文映射,直接显示英文动作名称 (HOLD/BUY/SELL/OPEN_LONG/OPEN_SHORT等)
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 恢复决策动作英文显示...")

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 注释掉actionMap的定义 (保留但不使用)
old_action_map = r"""                            // 动作名称中文映射
                            const actionMap = \{
                                'HOLD': '持有',
                                'BUY': '买入',
                                'SELL': '卖出',
                                'OPEN_LONG': '开多',
                                'OPEN_SHORT': '开空',
                                'CLOSE': '平仓',
                                'CLOSE_LONG': '平多',
                                'CLOSE_SHORT': '平空'
                            \};"""

new_action_map = r"""                            // 动作名称直接使用英文 (中文映射已禁用)
                            // const actionMap = {
                            //     'HOLD': '持有',
                            //     'BUY': '买入',
                            //     'SELL': '卖出',
                            //     'OPEN_LONG': '开多',
                            //     'OPEN_SHORT': '开空',
                            //     'CLOSE': '平仓',
                            //     'CLOSE_LONG': '平多',
                            //     'CLOSE_SHORT': '平空'
                            // };"""

content = re.sub(old_action_map, new_action_map, content)

# 2. 修改actionText的赋值,直接使用decision.action
old_action_text = r"actionText = actionMap\[decision\.action\] \|\| decision\.action;"
new_action_text = r"actionText = decision.action;"

content = re.sub(old_action_text, new_action_text, content)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 决策动作已恢复英文显示!")
print("\n📋 修改内容:")
print("  ✓ 注释掉中文映射 (actionMap)")
print("  ✓ 动作直接显示英文原文")
print("\n📝 动作显示:")
print("  • HOLD")
print("  • BUY / SELL")
print("  • OPEN_LONG / OPEN_SHORT")
print("  • CLOSE / CLOSE_LONG / CLOSE_SHORT")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 硬刷新浏览器 (Cmd+Shift+R)")
