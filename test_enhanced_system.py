#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强系统
验证所有新功能是否正常工作
"""

import os
import logging
from dotenv import load_dotenv
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from runtime_state_manager import RuntimeStateManager
from enhanced_decision_engine import EnhancedDecisionEngine

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_runtime_state():
    """测试运行状态管理器"""
    print("\n" + "="*60)
    print("📋 测试1: 运行状态管理器")
    print("="*60)

    manager = RuntimeStateManager()
    state = manager.get_state()

    print(f"✅ 当前运行时长: {manager.get_runtime_summary()}")
    print(f"✅ 总AI调用次数: {state['total_ai_calls']}")
    print(f"✅ 总交易循环次数: {state['total_trading_loops']}")

    return True


def test_binance_extensions():
    """测试BinanceClient新功能"""
    print("\n" + "="*60)
    print("📊 测试2: BinanceClient扩展功能")
    print("="*60)

    client = BinanceClient(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    )

    # 测试资金费率API
    try:
        funding_rate = client.get_current_funding_rate('BTCUSDT')
        print(f"✅ BTC资金费率: {funding_rate.get('fundingRate', 'N/A')}")
    except Exception as e:
        print(f"❌ 资金费率获取失败: {e}")
        return False

    # 测试持仓量API
    try:
        open_interest = client.get_open_interest('BTCUSDT')
        print(f"✅ BTC持仓量: {open_interest.get('openInterest', 'N/A')}")
    except Exception as e:
        print(f"❌ 持仓量获取失败: {e}")
        return False

    return True


def test_market_analyzer_extensions():
    """测试MarketAnalyzer新功能"""
    print("\n" + "="*60)
    print("📈 测试3: MarketAnalyzer扩展功能")
    print("="*60)

    client = BinanceClient(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    )
    analyzer = MarketAnalyzer(client)

    # 测试日内序列数据
    try:
        intraday = analyzer.get_intraday_series('BTCUSDT', '3m', 10)
        print(f"✅ 获取到 {len(intraday['mid_prices'])} 个价格点")
        print(f"   最新价格: {intraday['mid_prices'][-1]}")
    except Exception as e:
        print(f"❌ 日内序列获取失败: {e}")
        return False

    # 测试4小时上下文
    try:
        context_4h = analyzer.get_4h_context('BTCUSDT', 10)
        print(f"✅ 4h EMA20: {context_4h.get('ema20', 'N/A')}")
        print(f"   4h ATR14: {context_4h.get('atr14', 'N/A')}")
    except Exception as e:
        print(f"❌ 4小时上下文获取失败: {e}")
        return False

    # 测试合约数据
    try:
        futures_data = analyzer.get_futures_market_data('BTCUSDT')
        print(f"✅ 资金费率: {futures_data.get('funding_rate', 'N/A')}")
        print(f"   持仓量: {futures_data['open_interest'].get('current', 'N/A')}")
    except Exception as e:
        print(f"❌ 合约数据获取失败: {e}")
        return False

    # 测试完整市场上下文
    try:
        comprehensive = analyzer.get_comprehensive_market_context('BTCUSDT')
        print(f"✅ 完整市场上下文生成成功")
        print(f"   当前价格: {comprehensive['current_snapshot']['price']}")
        print(f"   EMA20: {comprehensive['current_snapshot']['ema20']:.2f}")
        print(f"   RSI7: {comprehensive['current_snapshot']['rsi7']:.2f}")
    except Exception as e:
        print(f"❌ 完整上下文生成失败: {e}")
        return False

    return True


def test_enhanced_decision_engine():
    """测试增强决策引擎"""
    print("\n" + "="*60)
    print("🤖 测试4: 增强决策引擎")
    print("="*60)

    # 初始化所有组件
    client = BinanceClient(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET'),
        testnet=os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    )
    analyzer = MarketAnalyzer(client)
    runtime_manager = RuntimeStateManager()
    engine = EnhancedDecisionEngine(client, analyzer, runtime_manager)

    # 测试账户摘要
    try:
        account_summary = engine.get_account_summary()
        print(f"✅ 账户总价值: ${account_summary['current_account_value']:.2f}")
        print(f"   可用余额: ${account_summary['available_balance']:.2f}")
        print(f"   未实现盈亏: ${account_summary['total_unrealized_profit']:.2f}")
    except Exception as e:
        print(f"❌ 账户摘要获取失败: {e}")
        return False

    # 测试持仓信息
    try:
        positions = engine.get_all_positions_info()
        print(f"✅ 当前持仓数量: {len(positions)}")
        if positions:
            for pos in positions:
                print(f"   {pos['symbol']}: {pos['quantity']} @ {pos['entry_price']:.2f}, PnL: ${pos['unrealized_pnl']:.2f}")
    except Exception as e:
        print(f"❌ 持仓信息获取失败: {e}")
        return False

    # 测试完整提示词生成
    try:
        prompt = engine.generate_comprehensive_prompt(['BTCUSDT', 'ETHUSDT'])
        print(f"✅ 完整AI提示词生成成功")
        print(f"   提示词长度: {len(prompt)} 字符")
        print(f"   包含运行时长: {'minutes since you started' in prompt}")
        print(f"   包含持仓量数据: {'Open Interest' in prompt}")

        # 保存提示词到文件以便检查
        with open('test_prompt_output.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"   ℹ️ 提示词已保存到 test_prompt_output.txt")

    except Exception as e:
        print(f"❌ 提示词生成失败: {e}")
        return False

    return True


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 Alpha Arena 增强系统测试")
    print("="*60)

    results = {
        '运行状态管理器': test_runtime_state(),
        'BinanceClient扩展': test_binance_extensions(),
        'MarketAnalyzer扩展': test_market_analyzer_extensions(),
        '增强决策引擎': test_enhanced_decision_engine()
    }

    # 打印测试摘要
    print("\n" + "="*60)
    print("📊 测试结果摘要")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！系统升级成功！")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
