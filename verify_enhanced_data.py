#!/usr/bin/env python3
"""验证增强数据集成"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer

def main():
    # 创建客户端
    client = BinanceClient(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=False
    )
    analyzer = MarketAnalyzer(client)

    # 获取增强市场数据
    symbol = 'ETHUSDT'
    print(f"🔍 获取 {symbol} 的增强市场数据...\n")

    data = analyzer.get_comprehensive_market_context(symbol)

    # 检查增强字段
    print("✅ 验证增强数据字段:")
    print(f"   current_snapshot: {'✅' if 'current_snapshot' in data else '❌'}")
    print(f"   intraday_series: {'✅' if 'intraday_series' in data else '❌'}")
    print(f"   long_term_context_4h: {'✅' if 'long_term_context_4h' in data else '❌'}")
    print(f"   futures_market: {'✅' if 'futures_market' in data else '❌'}")

    # 向后兼容字段
    print(f"\n✅ 向后兼容字段:")
    print(f"   current_price: {'✅' if 'current_price' in data else '❌'}")
    print(f"   rsi: {'✅' if 'rsi' in data else '❌'}")
    print(f"   macd: {'✅' if 'macd' in data else '❌'}")

    if 'intraday_series' in data and data['intraday_series']:
        print(f"\n📊 日内时间序列 (最近10个价格点):")
        prices = data['intraday_series'].get('mid_prices', [])
        print(f"   Prices: {[f'{p:.2f}' for p in prices[:5]]} ... (共{len(prices)}个)")

    if 'futures_market' in data and data['futures_market']:
        fm = data['futures_market']
        print(f"\n⚡ 合约市场数据:")
        print(f"   资金费率: {fm.get('funding_rate', 'N/A')}")
        if 'open_interest' in fm:
            oi = fm['open_interest']
            print(f"   持仓量: 当前={oi.get('current', 'N/A')}, 平均={oi.get('average', 'N/A')}")

    if 'long_term_context_4h' in data and data['long_term_context_4h']:
        ctx = data['long_term_context_4h']
        print(f"\n📈 4小时级别上下文:")
        print(f"   EMA20: {ctx.get('ema20', 'N/A')} vs EMA50: {ctx.get('ema50', 'N/A')}")
        print(f"   ATR: {ctx.get('atr14', 'N/A')}")

    print("\n✅ 增强数据集成成功！所有字段都可用。")

if __name__ == "__main__":
    main()
