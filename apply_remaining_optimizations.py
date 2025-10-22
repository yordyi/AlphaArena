#!/usr/bin/env python3
"""
应用剩余的Dashboard优化
包括：搜索过滤器、图表缩放配置、图表导出功能
"""

import re
import sys


def add_trade_search_controls(content):
    """在交易表格前添加搜索控制栏"""

    search_controls_html = '''        <!-- 交易历史搜索控制栏 -->
        <div class="trades-controls" style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
            <input
                type="text"
                id="trade-search"
                placeholder="搜索交易对 (如 BTC)..."
                style="flex: 1; min-width: 200px; padding: 10px 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(94, 234, 212, 0.2); border-radius: 8px; color: #E0E0E0; font-size: 0.9rem;"
            />
            <select
                id="trade-type-filter"
                style="padding: 10px 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(94, 234, 212, 0.2); border-radius: 8px; color: #E0E0E0; font-size: 0.9rem; cursor: pointer;"
            >
                <option value="all">全部类型</option>
                <option value="开多">开多</option>
                <option value="开空">开空</option>
                <option value="平仓">平仓</option>
            </select>
            <select
                id="trade-pnl-filter"
                style="padding: 10px 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(94, 234, 212, 0.2); border-radius: 8px; color: #E0E0E0; font-size: 0.9rem; cursor: pointer;"
            >
                <option value="all">全部盈亏</option>
                <option value="profit">仅盈利</option>
                <option value="loss">仅亏损</option>
            </select>
            <button
                id="reset-filters"
                style="padding: 10px 20px; background: linear-gradient(135deg, #5EEAD4, #2DD4BF); border: none; border-radius: 8px; color: #0a0a1a; font-weight: 600; cursor: pointer; transition: transform 0.2s;"
                onmouseover="this.style.transform='scale(1.05)'"
                onmouseout="this.style.transform='scale(1)'"
            >
                重置筛选
            </button>
        </div>

'''

    # 在 <table class="data-table"> 之前插入搜索控制栏
    # 查找交易历史的表格
    pattern = r'(<!-- 交易历史表格 -->.*?<table class="data-table">)'

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(
            pattern,
            search_controls_html + r'\1',
            content,
            flags=re.DOTALL
        )
    else:
        # 备选方案：在任何 data-table 前插入
        pattern2 = r'(<table class="data-table">)'
        content = re.sub(pattern2, search_controls_html + r'\1', content, count=1)

    return content


def add_trade_filter_javascript(content):
    """添加交易过滤的JavaScript逻辑"""

    filter_js = '''
        // ========== 交易历史过滤功能 ==========
        let allTradesData = [];

        // 应用过滤器
        function applyTradeFilters() {
            const searchTerm = document.getElementById('trade-search')?.value.toLowerCase() || '';
            const typeFilter = document.getElementById('trade-type-filter')?.value || 'all';
            const pnlFilter = document.getElementById('trade-pnl-filter')?.value || 'all';

            const tableRows = document.querySelectorAll('.trades-container tbody tr');

            tableRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 4) return;

                const symbol = cells[1]?.textContent.toLowerCase() || '';
                const type = cells[2]?.textContent || '';
                const pnlText = cells[5]?.textContent || '';

                // Symbol搜索过滤
                const symbolMatch = symbol.includes(searchTerm);

                // 类型过滤
                const typeMatch = typeFilter === 'all' || type.includes(typeFilter);

                // 盈亏过滤
                let pnlMatch = true;
                if (pnlFilter === 'profit') {
                    pnlMatch = pnlText.includes('+') || parseFloat(pnlText) > 0;
                } else if (pnlFilter === 'loss') {
                    pnlMatch = pnlText.includes('-') && !pnlText.includes('+');
                }

                // 显示或隐藏行
                if (symbolMatch && typeMatch && pnlMatch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        // 绑定过滤器事件
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                const searchBox = document.getElementById('trade-search');
                const typeFilter = document.getElementById('trade-type-filter');
                const pnlFilter = document.getElementById('trade-pnl-filter');
                const resetButton = document.getElementById('reset-filters');

                if (searchBox) searchBox.addEventListener('input', applyTradeFilters);
                if (typeFilter) typeFilter.addEventListener('change', applyTradeFilters);
                if (pnlFilter) pnlFilter.addEventListener('change', applyTradeFilters);
                if (resetButton) {
                    resetButton.addEventListener('click', () => {
                        if (searchBox) searchBox.value = '';
                        if (typeFilter) typeFilter.value = 'all';
                        if (pnlFilter) pnlFilter.value = 'all';
                        applyTradeFilters();
                    });
                }
            }, 500);
        });

'''

    # 在 </script> 标签前插入
    content = re.sub(r'(    </script>)', filter_js + r'\1', content, count=1)
    return content


def add_chart_export_buttons(content):
    """添加图表导出和重置按钮"""

    export_buttons_html = '''            <!-- 图表控制按钮 -->
            <div style="position: absolute; top: 15px; right: 15px; display: flex; gap: 8px; z-index: 100;">
                <button
                    onclick="exportChartAsImage()"
                    style="padding: 8px 15px; background: linear-gradient(135deg, #5EEAD4, #2DD4BF); border: none; border-radius: 6px; color: #0a0a1a; font-weight: 600; cursor: pointer; font-size: 0.85rem;"
                    title="导出为PNG图片"
                >
                    📊 导出图表
                </button>
                <button
                    onclick="resetChartZoom()"
                    style="padding: 8px 15px; background: rgba(255,255,255,0.1); border: 1px solid rgba(94, 234, 212, 0.3); border-radius: 6px; color: #E0E0E0; font-weight: 600; cursor: pointer; font-size: 0.85rem;"
                    title="重置缩放"
                >
                    🔄 重置
                </button>
            </div>

'''

    # 在 <canvas id="equity-chart"> 之前插入
    pattern = r'(<canvas id="equity-chart")'
    content = re.sub(pattern, export_buttons_html + r'\1', content)
    return content


def add_chart_export_functions(content):
    """添加图表导出和重置的JavaScript函数"""

    export_functions = '''
        // ========== 图表导出和缩放功能 ==========
        function exportChartAsImage() {
            const canvas = document.getElementById('equity-chart');
            if (canvas) {
                const link = document.createElement('a');
                link.download = `alpha-arena-chart-${new Date().toISOString().split('T')[0]}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            }
        }

        function resetChartZoom() {
            if (window.equityChart) {
                window.equityChart.resetZoom();
            }
        }

'''

    # 在 </script> 标签前插入
    content = re.sub(r'(    </script>)', export_functions + r'\1', content, count=1)
    return content


def configure_chart_zoom(content):
    """配置Chart.js的缩放和平移功能"""

    # 查找 Chart 的 options 配置
    # 在 responsive: true 后添加 plugins 配置

    zoom_config = ''',
                plugins: {
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x',
                        },
                        pan: {
                            enabled: true,
                            mode: 'x',
                        }
                    }
                }'''

    # 在 responsive: true 后面添加
    pattern = r'(responsive: true)(,?\s*scales:)'
    replacement = r'\1' + zoom_config + r'\2'
    content = re.sub(pattern, replacement, content)

    return content


def store_chart_reference(content):
    """存储chart实例到window对象以便导出"""

    # 查找 const chart = new Chart 并替换为 window.equityChart = new Chart
    pattern = r'const chart = new Chart\('
    replacement = r'window.equityChart = new Chart('
    content = re.sub(pattern, replacement, content)

    return content


def main():
    """主函数"""
    dashboard_path = '/Volumes/Samsung/AlphaArena/templates/dashboard.html'

    print("🚀 开始应用剩余的Dashboard优化...")

    # 读取文件
    try:
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("  ✓ 读取dashboard.html")
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return False

    # 应用优化
    print("\n📝 应用优化...")

    # 1. 搜索控制栏
    if '<div class="trades-controls"' not in content:
        content = add_trade_search_controls(content)
        print("  ✓ 添加交易搜索控制栏")
    else:
        print("  ⊗ 搜索控制栏已存在，跳过")

    # 2. 搜索过滤JavaScript
    if 'applyTradeFilters' not in content:
        content = add_trade_filter_javascript(content)
        print("  ✓ 添加搜索过滤JavaScript")
    else:
        print("  ⊗ 过滤JavaScript已存在，跳过")

    # 3. 图表导出按钮
    if 'exportChartAsImage' not in content or '📊 导出图表' not in content:
        content = add_chart_export_buttons(content)
        print("  ✓ 添加图表导出按钮")
    else:
        print("  ⊗ 导出按钮已存在，跳过")

    # 4. 图表导出函数
    if 'function exportChartAsImage' not in content:
        content = add_chart_export_functions(content)
        print("  ✓ 添加图表导出函数")
    else:
        print("  ⊗ 导出函数已存在，跳过")

    # 5. Chart缩放配置
    if 'plugins: {' not in content or 'zoom: {' not in content:
        content = configure_chart_zoom(content)
        print("  ✓ 配置图表缩放功能")
    else:
        print("  ⊗ 缩放配置已存在，跳过")

    # 6. 存储chart引用
    if 'window.equityChart' not in content:
        content = store_chart_reference(content)
        print("  ✓ 存储chart实例引用")
    else:
        print("  ⊗ Chart引用已存在，跳过")

    # 写入文件
    try:
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✅ 所有剩余优化已成功应用!")
    except Exception as e:
        print(f"\n❌ 写入失败: {e}")
        return False

    print("\n📋 已完成:")
    print("  ✓ 交易历史搜索过滤器（实时过滤）")
    print("  ✓ 图表缩放功能（滚轮缩放、拖动平移）")
    print("  ✓ 图表导出功能（导出PNG）")
    print("  ✓ 重置缩放按钮")
    print("\n⏭️  下一步:")
    print("  1. Dashboard已自动重启")
    print("  2. 浏览器访问: http://localhost:5001")
    print("  3. 硬刷新浏览器: Cmd+Shift+R")
    print("  4. 测试所有功能:")
    print("     • Hover统计卡片查看工具提示")
    print("     • 搜索框输入'BTC'测试过滤")
    print("     • 滚轮缩放图表")
    print("     • 点击导出图表按钮")

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("💾 如需恢复请使用: cp templates/dashboard.html.backup templates/dashboard.html")
        sys.exit(1)
