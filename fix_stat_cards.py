#!/usr/bin/env python3
"""
修复stat-card的data-tooltip属性位置错误
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 修复 stat-card 属性位置...")

# 读取文件
with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有错误的 data-tooltip 位置
# 将 <div class="stat-card"> data-tooltip="xxx" 修复为 <div class="stat-card" data-tooltip="xxx">
pattern = r'<div class="stat-card">\s+data-tooltip="([^"]+)"'
replacement = r'<div class="stat-card" data-tooltip="\1">'

content = re.sub(pattern, replacement, content)

# 写回文件
with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 所有 stat-card 属性已修复!")
print("⏭️  重启 Dashboard 以应用更改...")
