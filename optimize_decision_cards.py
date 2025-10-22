#!/usr/bin/env python3
"""
优化AI决策卡片:
1. 调整卡片间距（更紧凑精致）
2. 在卡片顶部显示币种对
"""

import re

dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

print("🎨 优化AI决策卡片...")

# 读取文件
with open(dashboard_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 调整卡片间距 - 从 1.75rem 改为 1.25rem
print("  ✓ 调整卡片间距（1.75rem → 1.25rem）")
content = re.sub(r'gap: 1\.75rem;', 'gap: 1.25rem;', content)
content = re.sub(r'bottom: -1\.75rem;', 'bottom: -1.25rem;', content)

# 2. 在决策卡片头部添加币种对显示
# 找到决策头部的 HTML 模板，在时间旁边添加symbol
print("  ✓ 在卡片顶部添加币种对显示")

# 修改决策头部HTML - 在时间前面添加币种对
old_header = r'''<div class="decision-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            \$\{modelBadge\}
                                            <span class="decision-main-action \$\{actionClass\}" style="text-shadow: 0 2px 8px rgba\(0,0,0,0\.3\);">\$\{actionText\}</span>
                                        </div>
                                        <span class="decision-time" style="font-size: 0\.75rem; color: rgba\(255,255,255,0\.6\); font-family: 'JetBrains Mono', monospace; font-weight: 600;">\$\{detailedTime\}</span>
                                    </div>'''

new_header = r'''<div class="decision-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            ${modelBadge}
                                            <span class="decision-main-action ${actionClass}" style="text-shadow: 0 2px 8px rgba(0,0,0,0.3);">${actionText}</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span style="background: rgba(0,0,0,0.3); color: ${isReasonerModel ? '#A78BFA' : '#2DD4BF'}; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid ${isReasonerModel ? 'rgba(139, 127, 216, 0.4)' : 'rgba(45, 212, 191, 0.4)'};">${decision.symbol}</span>
                                            <span class="decision-time" style="font-size: 0.7rem; color: rgba(255,255,255,0.5); font-family: 'JetBrains Mono', monospace; font-weight: 600;">${detailedTime}</span>
                                        </div>
                                    </div>'''

# 执行替换
content = re.sub(old_header, new_header, content, flags=re.MULTILINE | re.DOTALL)

# 写回文件
with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 优化完成!")
print("\n📋 优化内容:")
print("  ✓ 卡片间距: 1.75rem → 1.25rem（更紧凑）")
print("  ✓ 币种对显示: 添加到卡片右上角")
print("  ✓ 时间字体: 调整为更小尺寸（0.7rem）")
print("\n⏭️  下一步:")
print("  1. 重启 Dashboard")
print("  2. 浏览器硬刷新（Cmd+Shift+R）")
print("  3. 查看优化效果")
