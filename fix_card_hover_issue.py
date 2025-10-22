#!/usr/bin/env python3
"""
修复决策卡片hover时的遮挡问题
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 修复决策卡片hover问题...")

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 在工具提示样式后添加排除决策卡片的规则
tooltip_exclusion_css = '''
        /* 禁用决策卡片及其子元素的工具提示功能 */
        .decision-card [data-tooltip],
        .decision-card[data-tooltip],
        #decisions-container [data-tooltip] {
            cursor: default;
        }

        .decision-card [data-tooltip]:hover::after,
        .decision-card [data-tooltip]:hover::before,
        .decision-card[data-tooltip]:hover::after,
        .decision-card[data-tooltip]:hover::before,
        #decisions-container [data-tooltip]:hover::after,
        #decisions-container [data-tooltip]:hover::before {
            content: none;
            display: none;
        }

'''

# 在@keyframes tooltipFadeIn 后面添加新的CSS规则
pattern = r'(@keyframes tooltipFadeIn \{[^}]+\}[^}]+\})'
replacement = r'\1\n' + tooltip_exclusion_css

content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 决策卡片hover问题已修复!")
print("\n📋 修复内容:")
print("  ✓ 禁用决策卡片区域的工具提示功能")
print("  ✓ 防止tooltip遮挡卡片内容")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 硬刷新浏览器")
print("  3. 测试鼠标悬停效果")
