#!/usr/bin/env python3
"""
修复小账户高价币种交易问题
- 智能杠杆调整：确保名义价值≥20 USDT
- 解决"计算数量为0"的问题
"""

import os
import sys

print("🔧 修复小账户交易问题")
print("=" * 70)

# 读取ai_trading_engine.py
print("\n📝 正在优化 ai_trading_engine.py...")
try:
    with open('ai_trading_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到需要替换的部分（开多单）
    old_long_code = """    def _open_long_position(self, symbol: str, amount: float, leverage: int,
                           stop_loss_pct: float, take_profit_pct: float) -> Dict:
        \"\"\"开多单\"\"\"
        try:
            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    new_long_code = """    def _open_long_position(self, symbol: str, amount: float, leverage: int,
                           stop_loss_pct: float, take_profit_pct: float) -> Dict:
        \"\"\"开多单\"\"\"
        try:
            # 获取当前价格（需要先获取价格才能计算杠杆）
            current_price = self.market_analyzer.get_current_price(symbol)

            # 🔧 智能杠杆调整：确保名义价值≥20 USDT（币安最小要求）
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

    if old_long_code in content:
        content = content.replace(old_long_code, new_long_code)
        print("  ✅ _open_long_position 已优化")
    else:
        print("  ⚠️  开多单代码未找到或已修改")

    # 找到需要替换的部分（开空单）
    old_short_code = """    def _open_short_position(self, symbol: str, amount: float, leverage: int,
                            stop_loss_pct: float, take_profit_pct: float) -> Dict:
        \"\"\"开空单\"\"\"
        try:
            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price"""

    new_short_code = """    def _open_short_position(self, symbol: str, amount: float, leverage: int,
                            stop_loss_pct: float, take_profit_pct: float) -> Dict:
        \"\"\"开空单\"\"\"
        try:
            # 获取当前价格（需要先获取价格才能计算杠杆）
            current_price = self.market_analyzer.get_current_price(symbol)

            # 🔧 智能杠杆调整：确保名义价值≥20 USDT（币安最小要求）
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

    if old_short_code in content:
        content = content.replace(old_short_code, new_short_code)
        print("  ✅ _open_short_position 已优化")
    else:
        print("  ⚠️  开空单代码未找到或已修改")

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
print("  ✅ 智能杠杆调整: 自动提高杠杆以满足币安最小名义价值要求")
print("  ✅ 解决小账户无法交易高价币种的问题")
print("  ✅ 保持AI决策的完整性（仍使用AI建议的杠杆，除非不满足最低要求）")

print("\n💡 工作原理:")
print("  1. 检查: 名义价值(保证金×杠杆) < $20?")
print("  2. 计算: 达到$20所需的最小杠杆")
print("  3. 调整: 使用 max(AI杠杆, 最小杠杆)，最大25倍")
print("  4. 示例: $2.25保证金 → 需要9倍杠杆 → 名义价值$20.25 ✓")

print("\n⏭️  下一步:")
print("  重启交易机器人:")
print("  ./manage.sh restart")
print()
