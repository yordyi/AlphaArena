"""
Alpha Arena 配置文件
集中管理所有可调参数
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==================== AI 模型配置 ====================

# DeepSeek推理模型（昂贵但深度）使用策略
REASONER_INTERVAL_SECONDS = 600  # 推理模型最小调用间隔（秒）- 默认10分钟

# 强制使用推理模型的场景（即使未到时间间隔）
USE_REASONER_FOR_OPENING = True  # 开仓决策使用推理模型
USE_REASONER_FOR_HIGH_VOLATILITY = True  # 高波动市场（24h>5%）使用推理模型
USE_REASONER_FOR_LARGE_LOSS = True  # 大额亏损持仓（>10%）使用推理模型

# ==================== 日志管理配置 ====================

# 胜率显示策略
MIN_TRADES_FOR_WINRATE = 20  # 最少多少笔交易才显示胜率（避免误导AI）
SHOW_WINRATE_IN_PROMPT = False  # 是否在AI prompt中显示胜率（开发阶段建议False）

# AI参考历史数据起始日期（格式：YYYY-MM-DD，None表示全部历史）
AI_REFERENCE_START_DATE = None  # 例如: '2025-10-22' 表示只让AI看这天之后的数据

# ==================== 交易配置 ====================

# Binance API
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# 交易参数
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '20'))
MAX_POSITION_PCT = float(os.getenv('MAX_POSITION_PCT', '10'))
DEFAULT_LEVERAGE = int(os.getenv('DEFAULT_LEVERAGE', '3'))
TRADING_INTERVAL_SECONDS = int(os.getenv('TRADING_INTERVAL_SECONDS', '120'))

# 交易对
TRADING_SYMBOLS_STR = os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT')
TRADING_SYMBOLS = [s.strip() for s in TRADING_SYMBOLS_STR.split(',')]

# 交易冷却期
TRADE_COOLDOWN_SECONDS = 900  # 失败后冷却15分钟

# ==================== 风险管理配置 ====================

MAX_PORTFOLIO_RISK = 0.02  # 单笔交易最大风险（2%）
MAX_DRAWDOWN = 0.15  # 最大回撤（15%）
MAX_DAILY_LOSS = 0.05  # 每日最大亏损（5%）
MAX_POSITIONS = 10  # 最大持仓数量

# ==================== 性能追踪配置 ====================

PERFORMANCE_DATA_FILE = 'performance_data.json'
AI_DECISIONS_FILE = 'ai_decisions.json'
LOG_CONFIG_FILE = 'log_config.json'

# ==================== 高级功能配置 ====================

# 高级仓位管理策略
ENABLE_ADVANCED_STRATEGIES = True  # 是否启用高级策略（ROLL, PYRAMID等）
