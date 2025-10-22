#!/usr/bin/env python3
"""
优化DeepSeek决策区域显示
- 缩小标题字体
- 减小标题边距
- 突出决策卡片
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 优化DeepSeek决策区域显示...")

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 缩小标题字体和边距（让卡片成为主体）
old_title_style = r"""        \.decisions-sidebar h2 \{
            font-size: 0\.95rem;
            font-weight: 600;
            margin: 0 0 1\.2rem 0;"""

new_title_style = r"""        .decisions-sidebar h2 {
            font-size: 0.75rem;
            font-weight: 500;
            margin: 0 0 0.8rem 0;"""

content = re.sub(old_title_style, new_title_style, content)

# 2. 增大决策卡片间距，让卡片更突出
old_container_gap = r"""        #decisions-container \{
            display: flex;
            flex-direction: column;
            gap: 1\.25rem;"""

new_container_gap = r"""        #decisions-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;"""

content = re.sub(old_container_gap, new_container_gap, content)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ DeepSeek决策区域已优化!")
print("\n📋 修改内容:")
print("  ✓ 标题字体: 0.95rem → 0.75rem (缩小21%)")
print("  ✓ 标题下边距: 1.2rem → 0.8rem (减少33%)")
print("  ✓ 标题字重: 600 → 500 (更轻盈)")
print("  ✓ 卡片间距: 1.25rem → 1.5rem (增加20%)")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 硬刷新浏览器 (Cmd+Shift+R)")
print("  3. 决策卡片现在是主体，标题更低调")
