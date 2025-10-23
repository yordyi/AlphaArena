#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：验证AITradingEngine与增强功能的集成
"""

import os
import logging
from dotenv import load_dotenv
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager
from ai_trading_engine import AITradingEngine

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_ai_engine_integration():
    """测试AI引擎集成"""
    print("\n" + "="*60)
    print("🤖 测试AI交易引擎集成")
    print("="*60)

    try:
        # 初始化所有组件
        binance_client = BinanceClient(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET'),
            testnet=os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
        )

        market_analyzer = MarketAnalyzer(binance_client)

        # 风险管理配置
        risk_config = {
            'max_portfolio_risk': 0.02,
            'max_position_size': 0.7,  # 最大70%
            'max_leverage': 30,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.1,
            'max_drawdown': 0.15,
            'max_positions': 10,
            'daily_loss_limit': 0.05
        }
        risk_manager = RiskManager(risk_config)

        # 初始化AI交易引擎（增强功能默认启用）
        ai_engine = AITradingEngine(
            deepseek_api_key=os.getenv('DEEPSEEK_API_KEY'),
            binance_client=binance_client,
            market_analyzer=market_analyzer,
            risk_manager=risk_manager,
            enable_enhanced_features=True  # 显式启用增强功能
        )

        print(f"✅ AI交易引擎初始化成功")
        print(f"   增强功能状态: {'✅ 已启用' if ai_engine.enhanced_features_enabled else '❌ 未启用'}")

        if ai_engine.enhanced_features_enabled:
            # 验证运行状态管理器
            if ai_engine.runtime_manager:
                state = ai_engine.runtime_manager.get_state()
                print(f"   运行时长: {ai_engine.runtime_manager.get_runtime_summary()}")
                print(f"   AI调用次数: {state['total_ai_calls']}")
                print(f"   交易循环次数: {state['total_trading_loops']}")

            # 验证增强引擎
            if ai_engine.enhanced_engine:
                account_summary = ai_engine.enhanced_engine.get_account_summary()
                print(f"   账户价值: ${account_summary['current_account_value']:.2f}")

        return True

    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 Alpha Arena 集成测试")
    print("="*60)

    success = test_ai_engine_integration()

    # 测试摘要
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)

    if success:
        print("✅ 集成测试通过")
        print("\n🎉 系统已准备就绪，可以启动！")
        print("\n运行以下命令启动系统:")
        print("  ./start.sh")
        return True
    else:
        print("❌ 集成测试失败")
        print("\n请检查错误信息并修复问题")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
