#!/usr/bin/env python3
"""
修复AI决策卡片布局:
1. 将REASONER标签移到右上角
2. 左边只显示动作文字,右边显示REASONER+币种对+时间
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🔧 重新调整决策卡片布局...")

with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换决策卡片头部布局
old_header = r'''                                    <div class="decision-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            \$\{modelBadge\}
                                            <span class="decision-main-action \$\{actionClass\}" style="text-shadow: 0 2px 8px rgba\(0,0,0,0\.3\);">\$\{actionText\}</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span style="background: rgba\(0,0,0,0\.3\); color: \$\{isReasonerModel \? '#A78BFA' : '#2DD4BF'\}; padding: 4px 10px; border-radius: 6px; font-size: 0\.7rem; font-weight: 700; letter-spacing: 0\.05em; border: 1px solid \$\{isReasonerModel \? 'rgba\(139, 127, 216, 0\.4\)' : 'rgba\(45, 212, 191, 0\.4\)'\};"\>\$\{decision\.symbol\}</span>
                                            <span class="decision-time" style="font-size: 0\.7rem; color: rgba\(255,255,255,0\.5\); font-family: 'JetBrains Mono', monospace; font-weight: 600;"\>\$\{detailedTime\}</span>
                                        </div>
                                    </div>'''

new_header = r'''                                    <div class="decision-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <div style="display: flex; align-items: center;">
                                            <span class="decision-main-action ${actionClass}" style="text-shadow: 0 2px 8px rgba(0,0,0,0.3);">${actionText}</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            ${modelBadge}
                                            <span style="background: rgba(0,0,0,0.3); color: ${isReasonerModel ? '#A78BFA' : '#2DD4BF'}; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid ${isReasonerModel ? 'rgba(139, 127, 216, 0.4)' : 'rgba(45, 212, 191, 0.4)'};">${decision.symbol}</span>
                                            <span class="decision-time" style="font-size: 0.7rem; color: rgba(255,255,255,0.5); font-family: 'JetBrains Mono', monospace; font-weight: 600;">${detailedTime}</span>
                                        </div>
                                    </div>'''

# 执行替换
content = re.sub(old_header, new_header, content)

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 决策卡片布局已调整!")
print("\n📋 布局变化:")
print("  ✓ 左边: 动作文字(持有/开多/开空)")
print("  ✓ 右边: REASONER标签 + 币种对 + 时间")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 硬刷新浏览器")
