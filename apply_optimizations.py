#!/usr/bin/env python3
"""
自动应用Dashboard优化
包括：工具提示、搜索过滤器、图表优化
"""

import re
import sys

def apply_tooltip_css(content):
    """添加工具提示CSS样式"""
    tooltip_css = """
        /* ========== 工具提示样式 ========== */
        [data-tooltip] {
            position: relative;
            cursor: help;
        }

        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(-8px);
            background: linear-gradient(135deg, #1a1b2e, #16213e);
            color: #E0E0E0;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            white-space: nowrap;
            z-index: 10000;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(94, 234, 212, 0.3);
            animation: tooltipFadeIn 0.2s ease;
        }

        [data-tooltip]:hover::before {
            content: '';
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(0px);
            border: 6px solid transparent;
            border-top-color: #1a1b2e;
            z-index: 10001;
        }

        @keyframes tooltipFadeIn {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(-12px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(-8px);
            }
        }
"""

    # 在footer样式前插入
    footer_pattern = r'(        \.footer \{)'
    content = re.sub(footer_pattern, tooltip_css + r'\1', content)
    return content


def apply_tooltip_attributes(content):
    """为统计卡片添加data-tooltip属性"""

    tooltips = {
        '💰 账户价值': '账户中的总资产价值，包含未实现盈亏',
        '📈 总回报率': '相对于初始资金的收益率百分比',
        '📊 夏普比率': '风险调整后的收益指标，>1为优秀，>2为卓越',
        '📉 最大回撤': '账户价值从峰值到谷底的最大跌幅',
        '🎯 胜率': '盈利交易占总交易数的百分比',
        '🔢 总交易笔数': '已执行的总交易笔数（包括买入和卖出）',
        '📍 持仓数量': '当前持有的活跃合约仓位数量',
        '💵 未实现盈亏': '未平仓合约的当前盈亏，实时波动'
    }

    for title, tooltip in tooltips.items():
        # 匹配 <div class="stat-card"> ... <h3>title</h3>
        pattern = r'(<div class="stat-card">)\s*\n\s*(<h3>' + re.escape(title) + '</h3>)'
        replacement = r'\1 data-tooltip="' + tooltip + r'"\n                        \2'
        content = re.sub(pattern, replacement, content)

    return content


def add_chart_zoom_plugin(content):
    """添加Chart.js Zoom插件"""
    # 在Chart.js CDN后添加Zoom插件
    chartjs_pattern = r'(<script src="https://cdn\.jsdelivr\.net/npm/chart\.js"></script>)'
    zoom_plugin = r'\1\n    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>'
    content = re.sub(chartjs_pattern, zoom_plugin, content)
    return content


def main():
    """主函数"""
    dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

    print("🚀 开始应用Dashboard优化...")

    # 读取文件
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("  ✓ 读取dashboard.html")

    # 应用优化
    print("\n📝 应用优化...")

    # 1. 工具提示CSS
    content = apply_tooltip_css(content)
    print("  ✓ 添加工具提示CSS样式")

    # 2. 工具提示属性
    content = apply_tooltip_attributes(content)
    print("  ✓ 为统计卡片添加tooltip属性")

    # 3. Chart.js Zoom插件
    content = add_chart_zoom_plugin(content)
    print("  ✓ 添加Chart.js Zoom插件")

    # 写入文件
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✅ 所有优化已成功应用!")
    print("\n📋 已完成:")
    print("  ✓ 工具提示功能")
    print("  ✓ Chart.js Zoom插件")
    print("\n⏭️  下一步:")
    print("  1. 重启Dashboard: pkill -9 -f 'web_dashboard.py' && python3 web_dashboard.py &")
    print("  2. 浏览器硬刷新: Cmd+Shift+R")
    print("  3. Hover统计卡片查看工具提示")
    print("\n💡 提示: 搜索过滤器和图表导出功能需要手动添加（见优化指南）")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("💾 请使用备份恢复: cp templates/dashboard.html.backup templates/dashboard.html")
        sys.exit(1)
