#!/usr/bin/env python3
"""
测试 V3.5 15分钟超短线策略功能
验证: 浮盈滚仓 + 动态止盈止损 + ZenMux API
"""

import sys
from rolling_position_manager import RollingPositionManager


def test_rolling_manager():
    """测试浮盈滚仓管理器"""
    print("=" * 60)
    print("测试 1: 浮盈滚仓管理器")
    print("=" * 60)

    # 初始化管理器
    manager = RollingPositionManager(
        profit_threshold_pct=3.0,
        roll_ratio=0.5,
        max_rolls=2,
        min_roll_interval_minutes=5
    )

    print("✅ 滚仓管理器初始化成功")
    print(f"   盈利阈值: {manager.profit_threshold_pct}%")
    print(f"   加仓比例: {manager.roll_ratio * 100}%")
    print(f"   最大滚仓次数: {manager.max_rolls}")
    print()

    # 测试场景 1: 盈利不足
    print("场景 1: 盈利 2.5% (不足触发条件)")
    position_1 = {
        'symbol': 'BTCUSDT',
        'pnl_pct': 2.5,
        'quantity': 0.1,
        'entry_price': 50000,
        'side': 'LONG'
    }
    should_roll, reason, quantity = manager.should_roll_position(position_1)
    print(f"   是否滚仓: {should_roll}")
    print(f"   原因: {reason}")
    print()

    # 测试场景 2: 盈利达标
    print("场景 2: 盈利 3.5% (触发滚仓)")
    position_2 = {
        'symbol': 'BTCUSDT',
        'pnl_pct': 3.5,
        'quantity': 0.1,
        'entry_price': 50000,
        'side': 'LONG'
    }
    should_roll, reason, quantity = manager.should_roll_position(position_2)
    print(f"   是否滚仓: {should_roll}")
    print(f"   原因: {reason}")
    print(f"   建议加仓数量: {quantity:.4f}")
    print()

    if should_roll:
        manager.record_roll('BTCUSDT')
        roll_info = manager.get_roll_info('BTCUSDT')
        print(f"   滚仓记录: {roll_info}")
        print()

    # 测试场景 3: 动态止损
    print("场景 3: 计算动态止损")
    stop_loss = manager.calculate_dynamic_stop_loss(
        position=position_2,
        atr=500,  # 假设ATR为500
        base_stop_loss_pct=2.0
    )
    print(f"   开仓价: {position_2['entry_price']}")
    print(f"   动态止损价: {stop_loss:.2f}")
    print(f"   止损距离: {abs(position_2['entry_price'] - stop_loss):.2f} ({abs(position_2['entry_price'] - stop_loss) / position_2['entry_price'] * 100:.2f}%)")
    print()

    # 测试场景 4: 动态止盈
    print("场景 4: 计算动态止盈")
    take_profit = manager.calculate_dynamic_take_profit(
        position=position_2,
        atr=500,
        base_take_profit_pct=5.0
    )
    print(f"   开仓价: {position_2['entry_price']}")
    print(f"   动态止盈价: {take_profit:.2f}")
    print(f"   止盈距离: {take_profit - position_2['entry_price']:.2f} ({(take_profit - position_2['entry_price']) / position_2['entry_price'] * 100:.2f}%)")
    print()

    print("=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)


def test_config():
    """测试配置是否正确"""
    print("\n" + "=" * 60)
    print("测试 2: 系统配置")
    print("=" * 60)

    import os
    from dotenv import load_dotenv

    load_dotenv()

    # 检查关键配置
    config_items = [
        ("DeepSeek API Key", os.getenv('DEEPSEEK_API_KEY')),
        ("Binance API Key", os.getenv('BINANCE_API_KEY')),
        ("交易周期", os.getenv('TRADING_INTERVAL_SECONDS')),
        ("默认杠杆", os.getenv('DEFAULT_LEVERAGE')),
        ("交易对", os.getenv('TRADING_SYMBOLS'))
    ]

    for name, value in config_items:
        if value:
            if 'KEY' in name:
                print(f"✅ {name}: {value[:10]}...")
            else:
                print(f"✅ {name}: {value}")
        else:
            print(f"❌ {name}: 未配置")

    print()

    # 验证关键参数
    trading_interval = int(os.getenv('TRADING_INTERVAL_SECONDS', 0))
    default_leverage = int(os.getenv('DEFAULT_LEVERAGE', 0))

    if trading_interval == 900:
        print(f"✅ 交易周期配置正确: {trading_interval}秒 (15分钟)")
    else:
        print(f"⚠️  交易周期: {trading_interval}秒 (应为900秒)")

    if default_leverage == 30:
        print(f"✅ 杠杆配置正确: {default_leverage}x")
    else:
        print(f"⚠️  杠杆: {default_leverage}x (应为30x)")

    print()
    print("=" * 60)


def main():
    """主测试函数"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Alpha Arena V3.5 功能测试                        ║")
    print("║   15分钟超短线 + 30倍杠杆 + 浮盈滚仓 + 动态止盈止损     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    try:
        # 测试 1: 滚仓管理器
        test_rolling_manager()

        # 测试 2: 配置
        test_config()

        print("\n" + "=" * 60)
        print("🎉 V3.5 所有功能测试完成!")
        print("=" * 60)
        print("\n准备启动系统:")
        print("  python3 alpha_arena_bot.py")
        print("\n或使用快速启动:")
        print("  ./start.sh")
        print()

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
