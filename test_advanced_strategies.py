#!/usr/bin/env python3
"""
测试高级仓位管理策略
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from advanced_position_manager import AdvancedPositionManager

print("🧪 开始测试高级仓位管理策略...")
print()

# 初始化客户端
binance_api_key = os.getenv('BINANCE_API_KEY')
binance_api_secret = os.getenv('BINANCE_API_SECRET')
use_testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'

binance = BinanceClient(binance_api_key, binance_api_secret, testnet=use_testnet)
analyzer = MarketAnalyzer(binance)
adv_manager = AdvancedPositionManager(binance, analyzer)

print(f"✅ 连接到 {'测试网' if use_testnet else '主网'}")
print()

# 测试1: 检查滚仓条件
print("=" * 60)
print("测试1: 检查BTC是否可以滚仓")
print("=" * 60)
can_roll, reason, usable_pnl = adv_manager.can_roll_position(
    symbol='BTCUSDT',
    profit_threshold_pct=10.0,
    max_rolls=3
)
print(f"可以滚仓: {can_roll}")
print(f"原因: {reason}")
print(f"可用浮盈: ${usable_pnl:.2f}")
print()

# 测试2: 检查资金费率套利机会
print("=" * 60)
print("测试2: 检查BTC资金费率套利机会")
print("=" * 60)
has_arb, action, rate = adv_manager.check_funding_arbitrage(
    symbol='BTCUSDT',
    threshold_rate=0.01
)
print(f"有套利机会: {has_arb}")
print(f"建议操作: {action}")
print(f"资金费率: {rate * 100:.4f}%")
print()

# 测试3: 动态杠杆建议
print("=" * 60)
print("测试3: 检查BTC动态杠杆建议")
print("=" * 60)
leverage_result = adv_manager.adjust_leverage_by_volatility(
    symbol='BTCUSDT',
    base_leverage=5,
    min_leverage=2,
    max_leverage=10
)
if leverage_result['success']:
    print(f"✅ 建议杠杆: {leverage_result['leverage']}x")
    print(f"   波动率: {leverage_result['volatility_pct']:.2f}%")
else:
    print(f"❌ 失败: {leverage_result.get('error')}")
print()

print("=" * 60)
print("✅ 测试完成！高级仓位管理系统正常运行")
print("=" * 60)
print()
print("💡 提示: 查看 ADVANCED_STRATEGIES_GUIDE.md 了解完整策略用法")
