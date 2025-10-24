#!/usr/bin/env python3
"""
实时测试滚仓功能
模拟真实持仓场景
"""

from rolling_position_manager import RollingPositionManager

def test_rolling_scenarios():
    """测试各种盈利场景"""

    # 初始化管理器 (降低阈值到1.5%)
    manager = RollingPositionManager(
        profit_threshold_pct=1.5,
        roll_ratio=0.5,
        max_rolls=2,
        min_roll_interval_minutes=3
    )

    print("=" * 60)
    print("V3.5 滚仓功能测试 (阈值: 1.5%)")
    print("=" * 60)
    print()

    # 场景1: 盈利0.82% (真实场景 - 不触发)
    print("场景1: SOL多单盈利 0.82%")
    pos1 = {
        'symbol': 'SOLUSDT',
        'pnl_pct': 0.82,
        'quantity': 0.2,
        'entry_price': 192.42,
        'side': 'LONG'
    }
    should_roll, reason, qty = manager.should_roll_position(pos1)
    print(f"  结果: {'✅ 触发滚仓' if should_roll else '❌ 不触发'}")
    print(f"  原因: {reason}")
    print(f"  加仓数量: {qty:.4f}" if should_roll else "")
    print()

    # 场景2: 盈利1.6% (超过新阈值 - 应该触发)
    print("场景2: SOL多单盈利 1.6%")
    pos2 = {
        'symbol': 'SOLUSDT',
        'pnl_pct': 1.6,
        'quantity': 0.2,
        'entry_price': 192.42,
        'side': 'LONG'
    }
    should_roll, reason, qty = manager.should_roll_position(pos2)
    print(f"  结果: {'✅ 触发滚仓' if should_roll else '❌ 不触发'}")
    print(f"  原因: {reason}")
    print(f"  加仓数量: {qty:.4f}" if should_roll else "")
    print()

    # 场景3: 空单盈利 -0.08% (真实场景 - 亏损)
    print("场景3: SOL空单盈利 -0.08%")
    pos3 = {
        'symbol': 'SOLUSDT',
        'pnl_pct': -0.08,
        'quantity': -2.79,
        'entry_price': 189.15,
        'side': 'SHORT'
    }
    should_roll, reason, qty = manager.should_roll_position(pos3)
    print(f"  结果: {'✅ 触发滚仓' if should_roll else '❌ 不触发'}")
    print(f"  原因: {reason}")
    print()

    # 场景4: 空单盈利 2.0% (超过阈值 - 应该触发)
    print("场景4: SOL空单盈利 2.0%")
    pos4 = {
        'symbol': 'SOLUSDT',
        'pnl_pct': 2.0,
        'quantity': -2.79,
        'entry_price': 189.15,
        'side': 'SHORT'
    }
    should_roll, reason, qty = manager.should_roll_position(pos4)
    print(f"  结果: {'✅ 触发滚仓' if should_roll else '❌ 不触发'}")
    print(f"  原因: {reason}")
    print(f"  加仓数量: {abs(qty):.4f}" if should_roll else "")

    if should_roll:
        # 模拟记录滚仓
        manager.record_roll('SOLUSDT')
        roll_info = manager.get_roll_info('SOLUSDT')
        print(f"  滚仓记录: {roll_info['roll_count']}/{roll_info['max_rolls']} 次")

    print()
    print("=" * 60)
    print("✅ 测试完成!")
    print()
    print("关键配置:")
    print(f"  滚仓阈值: {manager.profit_threshold_pct}%")
    print(f"  加仓比例: {manager.roll_ratio * 100}%")
    print(f"  最大滚仓: {manager.max_rolls} 次")
    print(f"  最小间隔: {manager.min_roll_interval_minutes} 分钟")
    print("=" * 60)

if __name__ == "__main__":
    test_rolling_scenarios()
