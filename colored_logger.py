"""
彩色日志工具 - 提供精美的终端日志输出
使用ANSI颜色代码和Unicode符号替代表情符号
"""

class Colors:
    """ANSI颜色代码"""
    # 基础颜色
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class Symbols:
    """Unicode文字符号（非表情）"""
    # 状态符号
    SUCCESS = '✓'
    ERROR = '✗'
    WARNING = '!'
    INFO = 'i'
    ARROW_RIGHT = '→'
    ARROW_LEFT = '←'
    ARROW_UP = '↑'
    ARROW_DOWN = '↓'

    # 交易符号
    BUY = '↑ BUY'
    SELL = '↓ SELL'
    HOLD = '= HOLD'
    CLOSE = '× CLOSE'

    # 市场符号
    BULLISH = '⤴'
    BEARISH = '⤵'
    NEUTRAL = '⤍'

    # 系统符号
    SYSTEM = '●'
    AI = '◆'
    BINANCE = '▣'
    ANALYZE = '◐'

    # 数据符号
    MONEY = '$'
    PERCENT = '%'
    CHART = '▬'
    POSITION = '■'

    # 分隔符
    SEPARATOR = '━'
    DOT = '•'
    BRACKET_LEFT = '['
    BRACKET_RIGHT = ']'


class ColoredLogger:
    """彩色日志格式化工具"""

    @staticmethod
    def format_header(text: str, width: int = 60) -> str:
        """格式化标题头"""
        separator = Symbols.SEPARATOR * width
        padded_text = text.center(width)
        return f"{Colors.BRIGHT_CYAN}{separator}\n{padded_text}\n{separator}{Colors.RESET}"

    @staticmethod
    def success(text: str) -> str:
        """成功消息（绿色）"""
        return f"{Colors.BRIGHT_GREEN}{Symbols.BRACKET_LEFT}{Symbols.SUCCESS}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def error(text: str) -> str:
        """错误消息（红色）"""
        return f"{Colors.BRIGHT_RED}{Symbols.BRACKET_LEFT}{Symbols.ERROR}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def warning(text: str) -> str:
        """警告消息（黄色）"""
        return f"{Colors.BRIGHT_YELLOW}{Symbols.BRACKET_LEFT}{Symbols.WARNING}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def info(text: str) -> str:
        """信息消息（蓝色）"""
        return f"{Colors.BRIGHT_BLUE}{Symbols.BRACKET_LEFT}{Symbols.INFO}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def ai_message(text: str) -> str:
        """AI相关消息（品红色）"""
        return f"{Colors.BRIGHT_MAGENTA}{Symbols.BRACKET_LEFT}{Symbols.AI}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def market_message(text: str) -> str:
        """市场消息（青色）"""
        return f"{Colors.BRIGHT_CYAN}{Symbols.BRACKET_LEFT}{Symbols.ANALYZE}{Symbols.BRACKET_RIGHT} {text}{Colors.RESET}"

    @staticmethod
    def trade_action(action: str, symbol: str, details: str = "") -> str:
        """交易动作"""
        action_map = {
            'BUY': (Symbols.BUY, Colors.BRIGHT_GREEN),
            'SELL': (Symbols.SELL, Colors.BRIGHT_RED),
            'HOLD': (Symbols.HOLD, Colors.YELLOW),
            'CLOSE': (Symbols.CLOSE, Colors.BRIGHT_RED)
        }

        symbol_text, color = action_map.get(action.upper(), (action, Colors.WHITE))
        base = f"{color}{Symbols.BRACKET_LEFT}{symbol_text}{Symbols.BRACKET_RIGHT} {symbol}{Colors.RESET}"

        if details:
            base += f" {Colors.DIM}{Symbols.ARROW_RIGHT} {details}{Colors.RESET}"

        return base

    @staticmethod
    def money(amount: float, currency: str = "USDT") -> str:
        """货币格式化（绿色）"""
        color = Colors.BRIGHT_GREEN if amount >= 0 else Colors.BRIGHT_RED
        return f"{color}{Symbols.MONEY}{amount:,.2f} {currency}{Colors.RESET}"

    @staticmethod
    def percent(value: float) -> str:
        """百分比格式化"""
        color = Colors.BRIGHT_GREEN if value >= 0 else Colors.BRIGHT_RED
        sign = '+' if value > 0 else ''
        return f"{color}{sign}{value:.2f}{Symbols.PERCENT}{Colors.RESET}"

    @staticmethod
    def symbol_tag(symbol: str) -> str:
        """交易对标签"""
        return f"{Colors.BOLD}{Colors.BRIGHT_WHITE}{symbol}{Colors.RESET}"

    @staticmethod
    def status_tag(status: str, color_code: str = None) -> str:
        """状态标签"""
        if color_code is None:
            color_code = Colors.BRIGHT_CYAN
        return f"{color_code}{Symbols.BRACKET_LEFT}{status}{Symbols.BRACKET_RIGHT}{Colors.RESET}"

    @staticmethod
    def separator_line(char: str = Symbols.SEPARATOR, width: int = 60) -> str:
        """分隔线"""
        return f"{Colors.DIM}{char * width}{Colors.RESET}"

    @staticmethod
    def key_value(key: str, value: str, key_color: str = Colors.BRIGHT_WHITE,
                  value_color: str = Colors.CYAN) -> str:
        """键值对格式"""
        return f"{key_color}{key}:{Colors.RESET} {value_color}{value}{Colors.RESET}"

    @staticmethod
    def box(text: str, width: int = 60) -> str:
        """文本框"""
        top_bottom = '┌' + '─' * (width - 2) + '┐'
        bottom = '└' + '─' * (width - 2) + '┘'
        padded_text = f"│ {text.ljust(width - 4)} │"
        return f"{Colors.BRIGHT_CYAN}{top_bottom}\n{padded_text}\n{bottom}{Colors.RESET}"


# 便捷函数
def log_success(text: str) -> str:
    """快捷成功日志"""
    return ColoredLogger.success(text)


def log_error(text: str) -> str:
    """快捷错误日志"""
    return ColoredLogger.error(text)


def log_warning(text: str) -> str:
    """快捷警告日志"""
    return ColoredLogger.warning(text)


def log_info(text: str) -> str:
    """快捷信息日志"""
    return ColoredLogger.info(text)


def log_ai(text: str) -> str:
    """快捷AI日志"""
    return ColoredLogger.ai_message(text)


def log_market(text: str) -> str:
    """快捷市场日志"""
    return ColoredLogger.market_message(text)


# 测试代码
if __name__ == "__main__":
    print(ColoredLogger.format_header("Alpha Arena Trading Bot"))
    print()
    print(ColoredLogger.success("系统初始化成功"))
    print(ColoredLogger.info("正在连接Binance API..."))
    print(ColoredLogger.ai_message("DeepSeek Chat V3.1 已就绪"))
    print(ColoredLogger.market_message("开始分析 BTCUSDT"))
    print()
    print(ColoredLogger.trade_action('BUY', 'BTCUSDT', '价格: $45000, 杠杆: 3x'))
    print(ColoredLogger.trade_action('HOLD', 'ETHUSDT', '信心度: 65%'))
    print(ColoredLogger.trade_action('CLOSE', 'SOLUSDT', '获利: +2.5%'))
    print()
    print(ColoredLogger.key_value("账户余额", ColoredLogger.money(21.33)))
    print(ColoredLogger.key_value("总收益率", ColoredLogger.percent(5.67)))
    print(ColoredLogger.key_value("持仓数量", "3"))
    print()
    print(ColoredLogger.warning("近5笔胜率较低: 35%"))
    print(ColoredLogger.error("API连接失败"))
    print()
    print(ColoredLogger.separator_line())
    print(ColoredLogger.status_tag("运行中", Colors.BRIGHT_GREEN))
    print(ColoredLogger.status_tag("待机", Colors.YELLOW))
    print(ColoredLogger.status_tag("错误", Colors.BRIGHT_RED))
