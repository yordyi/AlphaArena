#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业交易终端日志格式化器
参考 Bloomberg Terminal / 专业量化系统设计
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any


class ProTradingFormatter(logging.Formatter):
    """
    专业交易终端日志格式化器
    特性：
    - 简洁时间戳
    - 智能模块名映射
    - 丰富的视觉指示器
    - 表格化数据支持
    - 实时市场数据格式化
    """

    # ANSI颜色代码
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'UNDERLINE': '\033[4m',

        # 基础色
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',

        # 亮色
        'BRIGHT_BLACK': '\033[90m',
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
        'BRIGHT_WHITE': '\033[97m',

        # 背景色
        'BG_RED': '\033[41m',
        'BG_GREEN': '\033[42m',
        'BG_YELLOW': '\033[43m',
        'BG_BLUE': '\033[44m',

        # DeepSeek 专属品牌色 RGB(41, 148, 255)
        'DEEPSEEK_BLUE': '\033[38;2;41;148;255m',
    }

    # 模块名映射（专业化显示）
    MODULE_NAMES = {
        '__main__': 'DeepSeek',
        'alpha_arena_bot': 'DeepSeek',
        'ai_trading_engine': 'AI-ENGINE',
        'deepseek_client': 'AI-MODEL',
        'binance_client': 'EXCHANGE',
        'market_analyzer': 'ANALYZER',
        'risk_manager': 'RISK',
        'performance_tracker': 'PERF',
        'web_dashboard': 'WEB',
        'trailing_stop_manager': 'STOP',
        'runtime_state_manager': 'STATE',
    }

    # 日志级别颜色与符号
    LEVEL_STYLES = {
        'DEBUG': {'color': COLORS['DIM'] + COLORS['CYAN'], 'symbol': '›'},
        'INFO': {'color': COLORS['BRIGHT_WHITE'], 'symbol': '•'},
        'WARNING': {'color': COLORS['BRIGHT_YELLOW'], 'symbol': '⚠'},
        'ERROR': {'color': COLORS['BRIGHT_RED'], 'symbol': '✗'},
        'CRITICAL': {'color': COLORS['BG_RED'] + COLORS['WHITE'], 'symbol': '!!!'},
    }

    # 标签颜色映射（增强版）
    TAG_COLORS = {
        # 系统相关
        '[SYSTEM]': COLORS['BRIGHT_CYAN'],
        '[SUCCESS]': COLORS['BRIGHT_GREEN'],
        '[CONFIG]': COLORS['CYAN'],

        # 交易相关
        '[MONEY]': COLORS['BRIGHT_GREEN'],
        '[ANALYZE]': COLORS['BRIGHT_BLUE'],
        '[TREND-UP]': COLORS['GREEN'],
        '[TREND-DOWN]': COLORS['RED'],
        '[ACCOUNT]': COLORS['BRIGHT_CYAN'],
        '[TARGET]': COLORS['MAGENTA'],
        '[POSITION]': COLORS['YELLOW'],

        # AI相关
        '[AI]': COLORS['BRIGHT_MAGENTA'],
        '[AI-THINK]': COLORS['MAGENTA'],
        '[CHAT]': COLORS['CYAN'],
        '[IDEA]': COLORS['YELLOW'],

        # 时间相关
        '[TIME]': COLORS['BRIGHT_BLACK'],
        '[TIMER]': COLORS['BRIGHT_BLACK'],
        '[WAIT]': COLORS['YELLOW'],

        # 动作相关
        '[LOOP]': COLORS['BLUE'],
        '[SEARCH]': COLORS['CYAN'],
        '[PIN]': COLORS['YELLOW'],
        '[HOLD]': COLORS['BOLD'] + COLORS['BRIGHT_YELLOW'],  # 加粗亮黄色，更醒目
        '[BUY]': COLORS['BOLD'] + COLORS['BRIGHT_GREEN'],    # 加粗亮绿色
        '[SELL]': COLORS['BOLD'] + COLORS['BRIGHT_RED'],     # 加粗亮红色
        '[CLOSE]': COLORS['BOLD'] + COLORS['BRIGHT_YELLOW'], # 加粗亮黄色

        # 状态相关
        '[OK]': COLORS['BRIGHT_GREEN'],
        '[ERROR]': COLORS['BRIGHT_RED'],
        '[WARNING]': COLORS['BRIGHT_YELLOW'],
        '[NEW]': COLORS['BRIGHT_CYAN'],
        '[HOT]': COLORS['BRIGHT_RED'],
        '[CELEBRATE]': COLORS['BRIGHT_GREEN'],

        # 性能相关
        '[PERF]': COLORS['BRIGHT_BLUE'],
        '[LATENCY]': COLORS['BRIGHT_BLACK'],
        '[RISK]': COLORS['BRIGHT_YELLOW'],

        # 其他
        '[MOBILE]': COLORS['CYAN'],
        '[WEB]': COLORS['BLUE'],
        '[SECURE]': COLORS['GREEN'],
        '[KEY]': COLORS['YELLOW'],
    }

    # 箭头指示器（已禁用 - 用户要求去掉）
    # ARROWS = {
    #     'up': COLORS['BRIGHT_GREEN'] + '↑' + COLORS['RESET'],
    #     'down': COLORS['BRIGHT_RED'] + '↓' + COLORS['RESET'],
    #     'flat': COLORS['BRIGHT_BLACK'] + '→' + COLORS['RESET'],
    # }

    def __init__(self, fmt=None, datefmt=None, style='%', compact=True):
        """
        初始化格式化器

        Args:
            fmt: 日志格式（会被覆盖）
            datefmt: 时间格式
            style: 格式风格
            compact: 是否使用紧凑模式（专业交易终端风格）
        """
        self.compact = compact
        # 紧凑模式：只显示时间和消息
        if compact:
            fmt = '%(message)s'
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        """格式化日志记录"""
        # 获取时间戳（紧凑格式）
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]

        # 获取模块名（映射为专业名称）
        module = self.MODULE_NAMES.get(record.name, record.name.upper()[:8])

        # 获取级别样式
        level_style = self.LEVEL_STYLES.get(record.levelname, self.LEVEL_STYLES['INFO'])
        level_symbol = level_style['symbol']
        level_color = level_style['color']

        # 构建消息
        message = record.getMessage()

        if self.compact:
            # 紧凑格式：HH:MM:SS.fff | MODULE | 消息
            # DeepSeek专属品牌蓝色显示 RGB(41, 148, 255)
            prefix = (
                f"{self.COLORS['BRIGHT_BLACK']}{timestamp}{self.COLORS['RESET']} "
                f"{self.COLORS['DIM']}|{self.COLORS['RESET']} "
                f"{self.COLORS['DEEPSEEK_BLUE']}{module:<8}{self.COLORS['RESET']} "
                f"{level_color}{level_symbol}{self.COLORS['RESET']} "
            )
            formatted = prefix + message
        else:
            # 标准格式
            formatted = super().format(record)

        # 应用颜色和增强
        formatted = self._colorize_message(formatted, record.levelname)

        return formatted

    def _colorize_message(self, message: str, level: str) -> str:
        """为消息添加颜色和视觉增强"""

        # 1. 为标签添加颜色
        for tag, color in self.TAG_COLORS.items():
            if tag in message:
                # 直接应用颜色，不添加额外符号
                colored_tag = f'{color}{tag}{self.COLORS["RESET"]}'
                message = message.replace(tag, colored_tag)

        # 2. 为交易对添加颜色和加粗（BTCUSDT, ETHUSDT等）
        symbol_pattern = r'\b([A-Z]{3,}USDT)\b'
        message = re.sub(
            symbol_pattern,
            lambda m: f'{self.COLORS["BOLD"]}{self.COLORS["BRIGHT_WHITE"]}{m.group(1)}{self.COLORS["RESET"]}',
            message
        )

        # 3. 为金额添加颜色（$xx.xx格式）
        amount_pattern = r'\$(-?\d+(?:,\d{3})*(?:\.\d{2,})?)'
        def colorize_amount(match):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                if amount >= 0:
                    color = self.COLORS['BRIGHT_GREEN']
                else:
                    color = self.COLORS['BRIGHT_RED']
                return f'{color}${match.group(1)}{self.COLORS["RESET"]}'
            except:
                return match.group(0)
        message = re.sub(amount_pattern, colorize_amount, message)

        # 4. 为百分比添加颜色（不添加箭头）
        percent_pattern = r'([+-]?\d+(?:\.\d+)?)%'
        def colorize_percent(match):
            percent_str = match.group(1)
            try:
                value = float(percent_str)
                if value > 0:
                    color = self.COLORS['BRIGHT_GREEN']
                elif value < 0:
                    color = self.COLORS['BRIGHT_RED']
                else:
                    color = self.COLORS['BRIGHT_BLACK']

                # 格式化为带符号的百分比
                formatted = f"{'+' if value > 0 else ''}{percent_str}"
                return f'{color}{formatted}%{self.COLORS["RESET"]}'
            except:
                return match.group(0)
        message = re.sub(percent_pattern, colorize_percent, message)

        # 5. 为信心度添加颜色和进度条
        confidence_pattern = r'信心[度:]?\s*[:：]?\s*(\d+)%'
        def colorize_confidence(match):
            confidence = int(match.group(1))

            # 选择颜色
            if confidence >= 80:
                color = self.COLORS['BRIGHT_GREEN']
                bar_char = '█'
            elif confidence >= 60:
                color = self.COLORS['GREEN']
                bar_char = '▓'
            elif confidence >= 40:
                color = self.COLORS['YELLOW']
                bar_char = '▒'
            else:
                color = self.COLORS['RED']
                bar_char = '░'

            # 简单进度条（5格）
            filled = int(confidence / 20)
            bar = bar_char * filled + '·' * (5 - filled)

            return f'信心:{color}{confidence}%{self.COLORS["RESET"]} {color}{bar}{self.COLORS["RESET"]}'
        message = re.sub(confidence_pattern, colorize_confidence, message)

        # 6. 为杠杆添加颜色（不添加风险符号）
        leverage_pattern = r'(\d+)x'
        def colorize_leverage(match):
            leverage = int(match.group(1))
            if leverage >= 10:
                color = self.COLORS['BRIGHT_RED']
            elif leverage >= 5:
                color = self.COLORS['YELLOW']
            elif leverage >= 3:
                color = self.COLORS['BRIGHT_YELLOW']
            else:
                color = self.COLORS['GREEN']
            return f'{color}{match.group(1)}x{self.COLORS["RESET"]}'
        message = re.sub(leverage_pattern, colorize_leverage, message)

        # 7. 为延迟时间添加颜色
        latency_pattern = r'(\d+)ms'
        def colorize_latency(match):
            ms = int(match.group(1))
            if ms < 100:
                color = self.COLORS['BRIGHT_GREEN']
            elif ms < 300:
                color = self.COLORS['YELLOW']
            else:
                color = self.COLORS['BRIGHT_RED']
            return f'{color}{ms}ms{self.COLORS["RESET"]}'
        message = re.sub(latency_pattern, colorize_latency, message)

        # 8. 为价格添加加粗和颜色
        price_pattern = r'价格[：:]\s*\$?(\d+(?:,\d{3})*(?:\.\d{2,})?)'
        message = re.sub(
            price_pattern,
            lambda m: f'价格: {self.COLORS["BOLD"]}{self.COLORS["BRIGHT_WHITE"]}${m.group(1)}{self.COLORS["RESET"]}',
            message
        )

        # 9. 增强分隔线
        if '=' * 10 in message:
            message = message.replace('=' * 60, self.COLORS['DIM'] + '─' * 80 + self.COLORS['RESET'])
            message = message.replace('=' * 50, self.COLORS['DIM'] + '─' * 70 + self.COLORS['RESET'])

        return message

    @staticmethod
    def format_table_row(data: Dict[str, Any], widths: Dict[str, int]) -> str:
        """
        格式化表格行

        Args:
            data: 数据字典 {列名: 值}
            widths: 列宽字典 {列名: 宽度}

        Returns:
            格式化的表格行
        """
        row = []
        for key, width in widths.items():
            value = str(data.get(key, ''))
            row.append(value.ljust(width))
        return ' │ '.join(row)

    @staticmethod
    def format_box(lines: list, title: Optional[str] = None, width: int = 80) -> str:
        """
        创建文本框

        Args:
            lines: 文本行列表
            title: 标题
            width: 宽度

        Returns:
            格式化的文本框
        """
        c = ProTradingFormatter.COLORS

        result = []

        # 顶部边框
        if title:
            title_str = f" {title} "
            padding = (width - len(title_str)) // 2
            top = f"{c['DIM']}┌{'─' * padding}{c['RESET']}{c['BRIGHT_CYAN']}{title_str}{c['RESET']}{c['DIM']}{'─' * (width - padding - len(title_str))}┐{c['RESET']}"
        else:
            top = f"{c['DIM']}┌{'─' * width}┐{c['RESET']}"
        result.append(top)

        # 内容行
        for line in lines:
            # 去除可能的ANSI代码以计算实际长度
            clean_line = re.sub(r'\033\[[0-9;]+m', '', line)
            padding = width - len(clean_line)
            result.append(f"{c['DIM']}│{c['RESET']} {line}{' ' * padding}{c['DIM']}│{c['RESET']}")

        # 底部边框
        bottom = f"{c['DIM']}└{'─' * width}┘{c['RESET']}"
        result.append(bottom)

        return '\n'.join(result)


def setup_pro_logging(logger, level=logging.INFO, compact=True):
    """
    为logger设置专业交易终端风格日志

    Args:
        logger: logging.Logger对象
        level: 日志级别
        compact: 是否使用紧凑模式
    """
    # 移除现有的handler
    logger.handlers = []

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 使用专业格式化器
    pro_formatter = ProTradingFormatter(compact=compact)
    console_handler.setFormatter(pro_formatter)

    logger.addHandler(console_handler)
    logger.setLevel(level)


# 测试代码
if __name__ == "__main__":
    import time

    # 创建测试logger
    test_logger = logging.getLogger("alpha_arena_bot")
    setup_pro_logging(test_logger, compact=True)

    print("\n" + "=" * 100)
    print("专业交易终端日志格式演示")
    print("=" * 100 + "\n")

    # 测试基础日志
    test_logger.info("[SYSTEM] Alpha Arena Bot 初始化完成")
    test_logger.info("[SUCCESS] 连接到 Binance Futures API")
    test_logger.info("[MONEY] 账户余额: $21,335.67 (从Binance API实时获取)")
    test_logger.info("[ANALYZE] 交易对: ETHUSDT, SOLUSDT, BNBUSDT")
    test_logger.info("[AI] 使用模型: DeepSeek Chat V3.1")

    time.sleep(0.5)

    # 测试市场数据
    test_logger.info("")
    test_logger.info("[ANALYZE] ETHUSDT 市场数据:")
    test_logger.info("  价格: $3,245.67 +2.3% | 成交量: 1.2M | API延迟: 89ms")
    test_logger.info("  RSI: 58.2 | MACD: 趋势向上 | BB: 中轨附近")

    time.sleep(0.5)

    # 测试AI决策
    test_logger.info("")
    test_logger.info("[AI] ETHUSDT AI决策:")
    test_logger.info("  动作: [BUY] 开多单 | 信心度: 85% | 杠杆: 3x")
    test_logger.info("  理由: 突破阻力位，成交量放大，趋势强劲")
    test_logger.info("  止损: -2.5% | 止盈: +5.8% | 盈亏比: 2.3")

    time.sleep(0.5)

    # 测试交易执行
    test_logger.info("")
    test_logger.info("[OK] 订单执行成功:")
    test_logger.info("  ETHUSDT 开多 | 数量: 0.15 | 入场价: $3,245.67 | 杠杆: 3x")
    test_logger.info("  订单ID: 12345678 | 执行延迟: 145ms | 滑点: 0.02%")

    time.sleep(0.5)

    # 测试性能指标
    test_logger.info("")
    test_logger.info("[PERF] 实时性能指标:")
    test_logger.info("  总收益: +15.6% | 今日: +2.3% | 胜率: 68.5% | 盈亏比: 2.1")
    test_logger.info("  最大回撤: -8.2% | 夏普比率: 1.85 | API延迟: 92ms")

    time.sleep(0.5)

    # 测试警告和错误
    test_logger.warning("[WARNING] 账户回撤接近阈值: -7.8% (阈值: -8%)")
    test_logger.warning("[RISK] 高杠杆仓位: BTCUSDT 15x ⚠")
    test_logger.error("[ERROR] API连接超时: 重试中... (3/5)")

    time.sleep(0.5)

    # 测试账户概览（不使用框式边框）
    test_logger.info("")
    test_logger.info("[ACCOUNT] 账户概览:")
    test_logger.info("  账户价值: $23,456.78  |  可用余额: $12,345.67  |  保证金使用: 45.2%")
    test_logger.info("  持仓数量: 3  |  总盈亏: +$2,456.78 (+11.7%)  |  今日收益: +$345.67 (+1.5%)")
    test_logger.info("  胜率: 68.5%  |  盈亏比: 2.1  |  最大回撤: -8.2%")

    print("\n" + "─" * 100)
    print("演示完成 - 专业交易终端日志格式")
    print("─" * 100 + "\n")
