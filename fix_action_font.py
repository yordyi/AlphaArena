#!/usr/bin/env python3
"""
调整AI决策动作文字的字体大小和粗细
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 调整动作文字样式...")

# 读取文件
with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 调整动作文字样式 - 减小字号和字重
old_style = r'''        \.decision-main-action \{
            font-size: 1\.4rem;
            font-weight: 900;
            letter-spacing: 0\.08em;'''

new_style = r'''        .decision-main-action {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.05em;'''

content = re.sub(old_style, new_style, content)

# 写回文件
with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 动作文字样式已调整!")
print("\n📋 优化内容:")
print("  ✓ 字体大小: 1.4rem → 1.05rem（减小25%）")
print("  ✓ 字体粗细: 900 → 700（更轻盈）")
print("  ✓ 字间距: 0.08em → 0.05em（更紧凑）")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 浏览器硬刷新")
