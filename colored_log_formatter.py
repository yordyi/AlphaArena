"""
彩色日志格式化器 - 为Python logging添加颜色支持
适配iTerm2和其他支持ANSI颜色的终端
"""

import logging
import re


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    根据日志级别和内容自动添加颜色
    """

    # ANSI颜色代码
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',

        # 前景色
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
    }

    # 日志级别颜色
    LEVEL_COLORS = {
        'DEBUG': COLORS['DIM'] + COLORS['CYAN'],
        'INFO': COLORS['BRIGHT_WHITE'],
        'WARNING': COLORS['BRIGHT_YELLOW'],
        'ERROR': COLORS['BRIGHT_RED'],
        'CRITICAL': COLORS['BOLD'] + COLORS['BRIGHT_RED'],
    }

    # 标签颜色映射
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
        '[HOLD]': COLORS['YELLOW'],

        # 状态相关
        '[OK]': COLORS['BRIGHT_GREEN'],
        '[ERROR]': COLORS['BRIGHT_RED'],
        '[WARNING]': COLORS['BRIGHT_YELLOW'],
        '[NEW]': COLORS['BRIGHT_CYAN'],
        '[HOT]': COLORS['BRIGHT_RED'],
        '[CELEBRATE]': COLORS['BRIGHT_GREEN'],

        # 其他
        '[MOBILE]': COLORS['CYAN'],
        '[WEB]': COLORS['BLUE'],
        '[SECURE]': COLORS['GREEN'],
        '[KEY]': COLORS['YELLOW'],
    }

    # 交易对颜色
    SYMBOL_COLOR = COLORS['BOLD'] + COLORS['BRIGHT_WHITE']

    # 金额颜色（根据正负）
    POSITIVE_AMOUNT_COLOR = COLORS['BRIGHT_GREEN']
    NEGATIVE_AMOUNT_COLOR = COLORS['BRIGHT_RED']

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        """格式化日志记录，添加颜色"""
        # 获取原始消息
        message = super().format(record)

        # 只在终端输出时添加颜色（不影响文件日志）
        if not hasattr(record, 'no_color') or not record.no_color:
            message = self._colorize_message(message, record.levelname)

        return message

    def _colorize_message(self, message: str, level: str) -> str:
        """为消息添加颜色"""
        # 1. 为日志级别添加颜色
        level_color = self.LEVEL_COLORS.get(level, self.COLORS['WHITE'])
        message = message.replace(f' - {level} - ', f' - {level_color}{level}{self.COLORS["RESET"]} - ')

        # 2. 为标签添加颜色
        for tag, color in self.TAG_COLORS.items():
            if tag in message:
                colored_tag = f'{color}{tag}{self.COLORS["RESET"]}'
                message = message.replace(tag, colored_tag)

        # 3. 为交易对添加颜色（BTCUSDT, ETHUSDT等）
        symbol_pattern = r'\b([A-Z]{3,}USDT)\b'
        message = re.sub(
            symbol_pattern,
            lambda m: f'{self.SYMBOL_COLOR}{m.group(1)}{self.COLORS["RESET"]}',
            message
        )

        # 4. 为金额添加颜色（$xx.xx格式）
        amount_pattern = r'\$(-?\d+(?:,\d{3})*(?:\.\d{2})?)'
        def colorize_amount(match):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                color = self.POSITIVE_AMOUNT_COLOR if amount >= 0 else self.NEGATIVE_AMOUNT_COLOR
                return f'{color}${match.group(1)}{self.COLORS["RESET"]}'
            except:
                return match.group(0)
        message = re.sub(amount_pattern, colorize_amount, message)

        # 5. 为百分比添加颜色（+x.x%或-x.x%格式）
        percent_pattern = r'([+-]\d+(?:\.\d+)?%)'
        def colorize_percent(match):
            percent_str = match.group(1)
            if percent_str.startswith('+'):
                color = self.POSITIVE_AMOUNT_COLOR
            elif percent_str.startswith('-'):
                color = self.NEGATIVE_AMOUNT_COLOR
            else:
                color = self.COLORS['WHITE']
            return f'{color}{percent_str}{self.COLORS["RESET"]}'
        message = re.sub(percent_pattern, colorize_percent, message)

        # 6. 为信心度添加颜色
        confidence_pattern = r'信心度[：:] ?(\d+)%'
        def colorize_confidence(match):
            confidence = int(match.group(1))
            if confidence >= 80:
                color = self.COLORS['BRIGHT_GREEN']
            elif confidence >= 60:
                color = self.COLORS['GREEN']
            elif confidence >= 40:
                color = self.COLORS['YELLOW']
            else:
                color = self.COLORS['RED']
            return f'信心度: {color}{match.group(1)}%{self.COLORS["RESET"]}'
        message = re.sub(confidence_pattern, colorize_confidence, message)

        # 7. 为杠杆添加颜色
        leverage_pattern = r'(\d+)x'
        def colorize_leverage(match):
            leverage = int(match.group(1))
            if leverage >= 10:
                color = self.COLORS['BRIGHT_RED']
            elif leverage >= 5:
                color = self.COLORS['YELLOW']
            else:
                color = self.COLORS['GREEN']
            return f'{color}{match.group(1)}x{self.COLORS["RESET"]}'
        message = re.sub(leverage_pattern, colorize_leverage, message)

        return message


def setup_colored_logging(logger, level=logging.INFO):
    """
    为logger设置彩色日志输出

    Args:
        logger: logging.Logger对象
        level: 日志级别
    """
    # 移除现有的handler
    logger.handlers = []

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 使用彩色格式化器
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)

    logger.addHandler(console_handler)
    logger.setLevel(level)


# 测试代码
if __name__ == "__main__":
    # 创建测试logger
    test_logger = logging.getLogger("test")
    setup_colored_logging(test_logger)

    # 测试不同类型的日志
    test_logger.info("[SYSTEM] Alpha Arena Bot 初始化完成")
    test_logger.info("[SUCCESS] Alpha Arena Trading Bot 启动")
    test_logger.info("[MONEY] 账户余额: $21,335.67 (从Binance API实时获取)")
    test_logger.info("[ANALYZE] 交易对: ETHUSDT, SOLUSDT, BNBUSDT")
    test_logger.info("[TIME] 交易间隔: 120秒")
    test_logger.info("[AI] AI 模型: DeepSeek Chat V3.1")
    test_logger.info("")
    test_logger.info("[LOOP] 开始第 1 轮交易循环")
    test_logger.info("[ACCOUNT] 账户状态:")
    test_logger.info("  余额: $21,335.67")
    test_logger.info("  总收益率: +15.23%")
    test_logger.info("  未实现盈亏: -$123.45")
    test_logger.info("")
    test_logger.info("[ANALYZE] 分析 BTCUSDT...")
    test_logger.info("[ETHUSDT] 开始分析...")
    test_logger.info("[ETHUSDT] AI决策 (deepseek-chat-v3.1): HOLD (信心度: 85%)")
    test_logger.info("[OK] 开多单成功: BTCUSDT, 数量: 0.001, 杠杆: 3x")
    test_logger.info("[OK] 开空单成功: ETHUSDT, 数量: 0.010, 杠杆: 15x")
    test_logger.warning("[WARNING] 近5笔胜率较低: 35.0%")
    test_logger.error("[ERROR] API连接失败")
