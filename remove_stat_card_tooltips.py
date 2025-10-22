#!/usr/bin/env python3
"""
完全移除统计卡片的tooltip功能
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 移除统计卡片tooltip功能...")

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 移除所有stat-card的data-tooltip属性
# 匹配模式: <div class="stat-card" data-tooltip="...">
pattern = r'<div class="stat-card" data-tooltip="[^"]*">'
replacement = r'<div class="stat-card">'

content = re.sub(pattern, replacement, content)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 统计卡片tooltip已完全移除!")
print("\n📋 修改内容:")
print("  ✓ 移除所有统计卡片的data-tooltip属性")
print("  ✓ 卡片hover时不再显示任何tooltip")
print("  ✓ 数据正常显示,不会被遮挡")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 硬刷新浏览器")
print("  3. 测试鼠标悬停效果")
