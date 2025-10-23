#!/usr/bin/env python3
"""
日志优化脚本 - 一次性处理所有优化
"""

import re
import sys

def optimize_alpha_arena_bot(filepath):
    """优化 alpha_arena_bot.py"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 去掉空白分隔线 (第一个分隔线保留，其他的去掉或改为换行)
    # 搜索: self.logger.info("") 后面跟着 self.logger.info(f"\n{'─' * 80}")
    content = re.sub(
        r'self\.logger\.info\(""\)\s+self\.logger\.info\(f"\\n\{\'─\' \* 80\}"\)',
        '',
        content
    )

    # 2. 移除API延迟显示
    # 匹配: |  API延迟: xxx
    content = re.sub(
        r'\s+\|  API延迟: \{.*?\}',
        '',
        content
    )

    # 3. 英文替换为中文
    replacements = {
        'Alpha Arena Trading Bot': 'DeepSeek AI 交易机器人',
        'SUCCESS.*Alpha Arena': 'SUCCESS.*DeepSeek AI 交易',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已优化: {filepath}")

def optimize_pro_log_formatter(filepath):
    """优化 pro_log_formatter.py - 去掉箭头符号"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 去掉箭头符号
    arrow_replacements = {
        '↑': '',
        '↓': '',
        '→': '',
        '↗': '',
        '↘': '',
        '⚠⚠⚠': '高风险',
        '⚠⚠': '中风险',
        '⚠': '注意',
    }

    for arrow, replacement in arrow_replacements.items():
        content = content.replace(arrow, replacement)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已优化: {filepath}")

if __name__ == '__main__':
    optimize_alpha_arena_bot('/Volumes/Samsung/AlphaArena/alpha_arena_bot.py')
    optimize_pro_log_formatter('/Volumes/Samsung/AlphaArena/pro_log_formatter.py')
    print("\n✓ 所有优化完成！")
