#!/usr/bin/env python3
"""
修复智能杠杆调整 - 考虑精度要求
确保调整后的数量满足币安精度规则
"""

import os
import sys

print("🔧 修复智能杠杆调整（精度版本）")
print("=" * 70)

# 读取ai_trading_engine.py
print("\n📝 正在优化 ai_trading_engine.py...")
try:
    with open('ai_trading_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到并替换开多单的智能杠杆调整部分
    old_long_leverage_code = """            # 🔧 智能杠杆调整：确保名义价值≥20 USDT（币安最小要求）
            min_notional = 20  # 币安最小名义价值
            notional_value = amount * leverage

            if notional_value < min_notional:
                # 计算达到最小名义价值所需的杠杆
                required_leverage = int(min_notional / amount) + 1

                # 使用较大的杠杆（AI建议 vs 最小要求）
                original_leverage = leverage
                leverage = min(max(leverage, required_leverage), 25)  # 最大25倍

                if leverage != original_leverage:
                    self.logger.info(f"💡 [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                                   f"(确保名义价值≥${min_notional})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    new_long_leverage_code = """            # 🔧 智能杠杆调整：同时满足币安名义价值和精度要求
            # 先确定精度规则
            if 'BTC' in symbol:
                precision = 3  # BTC: 0.001
                min_qty = 0.001
            elif 'ETH' in symbol:
                precision = 3  # ETH: 0.001
                min_qty = 0.001
            elif 'BNB' in symbol:
                precision = 1  # BNB: 0.1
                min_qty = 0.1
            elif 'SOL' in symbol:
                precision = 1  # SOL: 0.1
                min_qty = 0.1
            elif 'DOGE' in symbol:
                precision = 0  # DOGE: 整数
                min_qty = 1.0
            else:
                precision = 1  # 默认: 0.1
                min_qty = 0.1

            # 计算满足精度要求所需的最小名义价值
            min_notional_for_precision = min_qty * current_price
            min_notional = max(20, min_notional_for_precision)  # 至少$20，或满足精度要求

            # 计算所需杠杆
            required_leverage = int(min_notional / amount) + 1
            original_leverage = leverage
            leverage = min(max(leverage, required_leverage), 25)  # 最大25倍

            if leverage != original_leverage:
                self.logger.info(f"💡 [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                               f"(名义价值 ${amount*original_leverage:.2f} → ${amount*leverage:.2f}, "
                               f"精度要求: ≥{min_qty} {symbol.replace('USDT', '')})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    if old_long_leverage_code in content:
        content = content.replace(old_long_leverage_code, new_long_leverage_code)
        print("  ✅ _open_long_position 智能杠杆已优化（精度版）")
    else:
        print("  ⚠️  开多单智能杠杆代码未找到，尝试查找旧版本...")

    # 开空单相同修复
    old_short_leverage_code = """            # 🔧 智能杠杆调整：确保名义价值≥20 USDT（币安最小要求）
            min_notional = 20  # 币安最小名义价值
            notional_value = amount * leverage

            if notional_value < min_notional:
                # 计算达到最小名义价值所需的杠杆
                required_leverage = int(min_notional / amount) + 1

                # 使用较大的杠杆（AI建议 vs 最小要求）
                original_leverage = leverage
                leverage = min(max(leverage, required_leverage), 25)  # 最大25倍

                if leverage != original_leverage:
                    self.logger.info(f"💡 [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                                   f"(确保名义价值≥${min_notional})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    new_short_leverage_code = """            # 🔧 智能杠杆调整：同时满足币安名义价值和精度要求
            # 先确定精度规则
            if 'BTC' in symbol:
                precision = 3  # BTC: 0.001
                min_qty = 0.001
            elif 'ETH' in symbol:
                precision = 3  # ETH: 0.001
                min_qty = 0.001
            elif 'BNB' in symbol:
                precision = 1  # BNB: 0.1
                min_qty = 0.1
            elif 'SOL' in symbol:
                precision = 1  # SOL: 0.1
                min_qty = 0.1
            elif 'DOGE' in symbol:
                precision = 0  # DOGE: 整数
                min_qty = 1.0
            else:
                precision = 1  # 默认: 0.1
                min_qty = 0.1

            # 计算满足精度要求所需的最小名义价值
            min_notional_for_precision = min_qty * current_price
            min_notional = max(20, min_notional_for_precision)  # 至少$20，或满足精度要求

            # 计算所需杠杆
            required_leverage = int(min_notional / amount) + 1
            original_leverage = leverage
            leverage = min(max(leverage, required_leverage), 25)  # 最大25倍

            if leverage != original_leverage:
                self.logger.info(f"💡 [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                               f"(名义价值 ${amount*original_leverage:.2f} → ${amount*leverage:.2f}, "
                               f"精度要求: ≥{min_qty} {symbol.replace('USDT', '')})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    if old_short_leverage_code in content:
        content = content.replace(old_short_leverage_code, new_short_leverage_code)
        print("  ✅ _open_short_position 智能杠杆已优化（精度版）")
    else:
        print("  ⚠️  开空单智能杠杆代码未找到")

    # 写回文件
    with open('ai_trading_engine.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("\n✅ ai_trading_engine.py 修改完成！")

except Exception as e:
    print(f"\n❌ 修改失败: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 修复完成！")
print("=" * 70)

print("\n📋 优化内容:")
print("  ✅ 精度感知的智能杠杆调整")
print("  ✅ 确保名义价值 ≥ max($20, 币种最小精度×价格)")
print("  ✅ 示例: BNB $1070, 需要 0.1×$1070=$107 → 需要杠杆≥$107/$2.25≈48x")
print("  ✅ 但会限制在25x最大杠杆，因此小账户可能仍无法交易高价币")

print("\n💡 根本原因:")
print("  • BNB最小精度: 0.1个")
print("  • BNB当前价格: ~$1070")
print("  • 账户可用: ~$2.25 (10%)")
print("  • 需要名义价值: 0.1×$1070 = $107")
print("  • 所需杠杆: $107/$2.25 ≈ 48x ❌ 超过25x限制")

print("\n🎯 解决方案:")
print("  1. 选项A: 提高账户余额")
print("  2. 选项B: 降低最大持仓比例限制（比如20%而不是10%）")
print("  3. 选项C: 仅交易低价币种（SOL, DOGE, XRP等）")
print("  4. 选项D: 接受现状，小账户无法交易所有币种")

print("\n⏭️  下一步:")
print("  修改后需要重启交易机器人:")
print("  pkill -9 -f 'alpha_arena_bot.py' && sleep 2 && ./manage.sh start")
print()
