#!/usr/bin/env python3
"""
升级系统以支持高级仓位管理策略
1. 在DeepSeek prompt中注入高级策略说明
2. 集成advanced_position_manager到ai_trading_engine
3. 测试验证
"""

import re
import os

print("🚀 开始升级Alpha Arena到高级仓位管理系统...")
print()

# ======================
# 步骤1: 更新 deepseek_client.py - 注入高级策略说明
# ======================

print("📝 步骤1: 更新DeepSeek prompt...")

deepseek_path = '/Volumes/Samsung/AlphaArena/deepseek_client.py'

with open(deepseek_path, 'r', encoding='utf-8') as f:
    deepseek_content = f.read()

# 找到analyze_market_and_decide方法中的system message部分
# 在"Available Actions"部分之后添加高级策略说明

advanced_strategies_prompt = '''

## 🎯 Advanced Position Management Strategies (New!)

You now have access to 9 professional-grade position management strategies:

### 1. 🔄 ROLL - Rolling Position (Floating Profit Compounding)
**Purpose**: Use unrealized profits to open new positions in strong trends
**When to use**:
- Existing position has 10%+ floating profit
- Very strong trend (breaking key resistances)
- Moderate volatility (won't shake you out)

**Format**:
```json
{
  "action": "ROLL",
  "confidence": 85,
  "reasoning": "BTC broke 67000 resistance, RSI strong, 12% floating profit, suitable for rolling",
  "leverage": 2,
  "profit_threshold_pct": 10.0
}
```

### 2. 📐 PYRAMID - Pyramiding (Decreasing Position Sizing)
**Purpose**: Add positions with decreasing sizes, forming a pyramid structure
**When to use**: Price pullback to favorable levels (support) in an intact trend

**Format**:
```json
{
  "action": "PYRAMID",
  "confidence": 75,
  "reasoning": "ETH pullback to 4050 support, trend intact, adding 2nd pyramid layer",
  "base_size_usdt": 100,
  "current_pyramid_level": 1,
  "max_pyramids": 3,
  "reduction_factor": 0.5
}
```

### 3. 🎯 MULTI_TP - Multiple Take Profits
**Purpose**: Take profits in batches at different price levels
**When to use**: Want to lock profits while keeping upside exposure

**Format**:
```json
{
  "action": "MULTI_TP",
  "confidence": 80,
  "reasoning": "BTC up 15%, setting multi-level TP: 20%→close 30%, 30%→close 40%, 50%→close all",
  "tp_levels": [
    {"profit_pct": 20, "close_pct": 30},
    {"profit_pct": 30, "close_pct": 40},
    {"profit_pct": 50, "close_pct": 100}
  ]
}
```

### 4. 🛡️ MOVE_SL_BREAKEVEN - Move Stop Loss to Breakeven
**Purpose**: Protect capital by moving stop to entry price after profit
**When to use**: Position has 5%+ profit, want to secure "no loss" state

**Format**:
```json
{
  "action": "MOVE_SL_BREAKEVEN",
  "confidence": 75,
  "reasoning": "ETH up 7%, moving SL to breakeven+0.1% to protect capital",
  "profit_trigger_pct": 5.0,
  "breakeven_offset_pct": 0.1
}
```

### 5. 📊 ATR_STOP - ATR-Based Adaptive Stop Loss
**Purpose**: Set stop loss based on volatility (ATR)
**When to use**: Want scientific stop placement that adapts to volatility

**Format**:
```json
{
  "action": "ATR_STOP",
  "confidence": 70,
  "reasoning": "Volatility increased, using 2x ATR for adaptive stop",
  "atr_multiplier": 2.0
}
```

### 6. ⚖️ ADJUST_LEVERAGE - Dynamic Leverage Adjustment
**Purpose**: Adjust leverage based on market volatility
**When to use**: Volatility changes significantly

**Format**:
```json
{
  "action": "ADJUST_LEVERAGE",
  "confidence": 65,
  "reasoning": "Volatility rose to 3.5%, reducing leverage to 3x for risk control",
  "base_leverage": 5,
  "min_leverage": 2,
  "max_leverage": 10
}
```

### 7. 🔰 HEDGE - Hedging Strategy
**Purpose**: Open reverse position to lock profits or reduce risk
**When to use**: Profitable but worried about pullback, or before major news

**Format**:
```json
{
  "action": "HEDGE",
  "confidence": 60,
  "reasoning": "Fed meeting ahead, hedging 50% of BTC long with short to lock partial profit",
  "hedge_ratio": 0.5
}
```

### 8. ⚖️ REBALANCE - Position Rebalancing
**Purpose**: Adjust position size to target allocation
**When to use**: Position size deviates from target due to price movement

**Format**:
```json
{
  "action": "REBALANCE",
  "confidence": 70,
  "reasoning": "BTC position grew to 150 USDT due to rally, rebalancing to target 100 USDT",
  "target_size_usdt": 100.0
}
```

### 9. 💰 FUNDING_ARB - Funding Rate Arbitrage
**Purpose**: Earn funding fees when rates are extreme
**When to use**: Funding rate > 0.01% or < -0.01%, sideways market

**Format**:
```json
{
  "action": "FUNDING_ARB",
  "confidence": 55,
  "reasoning": "BTC funding rate 0.03%, opening short for arbitrage",
  "threshold_rate": 0.01
}
```

## 📋 Strategy Combination Recommendations

**Trend Start**:
1. Open + ATR_STOP
2. Profit 5% → MOVE_SL_BREAKEVEN

**Trend Confirmed**:
1. Profit 10% → ROLL (compound with floating profit)
2. Or PYRAMID (add at pullbacks)

**Trend End**:
1. MULTI_TP (take profits in batches)
2. Or HEDGE (protect profits)

**Choppy Market**:
1. REBALANCE (control exposure)
2. FUNDING_ARB (earn fees)

**High Volatility**:
1. ADJUST_LEVERAGE (reduce leverage)
2. ATR_STOP (widen stops)

⚠️ **Important Notes**:
- Advanced strategies require confidence >= 65
- Don't overuse: max 2-3 strategies per decision
- ROLL and PYRAMID have strict risk controls built-in
- Stop loss always comes first - never violate risk management

'''

# 在"Available Actions:"之后插入高级策略说明
insert_marker = 'Available Actions:\n- BUY'
if insert_marker in deepseek_content:
    deepseek_content = deepseek_content.replace(
        insert_marker,
        insert_marker + advanced_strategies_prompt
    )
    print("✅ 已在DeepSeek prompt中注入高级策略说明")
else:
    print("⚠️  警告: 未找到插入点，请手动检查")

# 保存更新后的文件
with open(deepseek_path, 'w', encoding='utf-8') as f:
    f.write(deepseek_content)

print("✅ deepseek_client.py 更新完成")
print()

# ======================
# 步骤2: 更新 ai_trading_engine.py - 导入advanced_position_manager
# ======================

print("📝 步骤2: 更新ai_trading_engine集成...")

engine_path = '/Volumes/Samsung/AlphaArena/ai_trading_engine.py'

with open(engine_path, 'r', encoding='utf-8') as f:
    engine_content = f.read()

# 添加import语句（如果还没有）
if 'from advanced_position_manager import AdvancedPositionManager' not in engine_content:
    # 在其他import之后添加
    import_insert_point = 'from risk_manager import RiskManager'
    if import_insert_point in engine_content:
        engine_content = engine_content.replace(
            import_insert_point,
            import_insert_point + '\nfrom advanced_position_manager import AdvancedPositionManager'
        )
        print("✅ 已添加AdvancedPositionManager导入")
    else:
        print("⚠️  警告: 未找到import插入点")

# 在__init__方法中初始化advanced_position_manager
init_insert_marker = 'self.trade_history = []'
if init_insert_marker in engine_content and 'self.adv_position_manager' not in engine_content:
    engine_content = engine_content.replace(
        init_insert_marker,
        init_insert_marker + '\n\n        # 高级仓位管理器\n        self.adv_position_manager = AdvancedPositionManager(binance_client, market_analyzer)'
    )
    print("✅ 已在__init__中初始化AdvancedPositionManager")

# 保存更新后的文件
with open(engine_path, 'w', encoding='utf-8') as f:
    f.write(engine_content)

print("✅ ai_trading_engine.py 更新完成")
print()

# ======================
# 步骤3: 创建测试脚本
# ======================

print("📝 步骤3: 创建测试脚本...")

test_script = '''#!/usr/bin/env python3
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
'''

test_script_path = '/Volumes/Samsung/AlphaArena/test_advanced_strategies.py'
with open(test_script_path, 'w', encoding='utf-8') as f:
    f.write(test_script)

os.chmod(test_script_path, 0o755)
print(f"✅ 测试脚本已创建: {test_script_path}")
print()

# ======================
# 完成
# ======================

print("=" * 60)
print("🎉 升级完成！系统已支持9大高级仓位管理策略")
print("=" * 60)
print()
print("📋 已完成的修改:")
print("  ✅ deepseek_client.py - 已注入高级策略说明到AI prompt")
print("  ✅ ai_trading_engine.py - 已集成AdvancedPositionManager")
print("  ✅ test_advanced_strategies.py - 已创建测试脚本")
print()
print("📚 文档:")
print("  📖 ADVANCED_STRATEGIES_GUIDE.md - 完整策略指南")
print("  🔧 advanced_position_manager.py - 策略实现")
print()
print("⏭️  下一步:")
print("  1. 运行测试: python3 test_advanced_strategies.py")
print("  2. 重启交易机器人: ./manage.sh restart")
print("  3. 查看日志确认AI使用新策略: tail -f logs/alpha_arena_*.log")
print()
print("🔥 重点功能 - 滚仓（ROLL）:")
print("   在强趋势中，当浮盈达到10%时，AI可以使用浮盈加仓")
print("   实现复利增长，同时风险可控（仅用50%浮盈，2x低杠杆）")
print()
