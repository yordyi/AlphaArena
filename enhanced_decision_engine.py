#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强决策引擎
整合所有市场数据，生成完整的AI决策输入
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedDecisionEngine:
    """增强的决策引擎，整合所有市场上下文"""

    def __init__(self, binance_client, market_analyzer, runtime_state_manager):
        """
        初始化增强决策引擎

        Args:
            binance_client: Binance客户端
            market_analyzer: 市场分析器
            runtime_state_manager: 运行状态管理器
        """
        self.binance_client = binance_client
        self.market_analyzer = market_analyzer
        self.runtime_state = runtime_state_manager

    def get_all_positions_info(self) -> List[Dict]:
        """
        获取所有持仓的详细信息（包含清算价、未实现盈亏）

        Returns:
            持仓信息列表
        """
        try:
            positions = self.binance_client.get_active_positions()
            enriched_positions = []

            for pos in positions:
                symbol = pos['symbol']
                entry_price = float(pos['entryPrice'])
                position_amt = float(pos['positionAmt'])
                leverage = int(pos['leverage'])
                unrealized_pnl = float(pos['unRealizedProfit'])
                liquidation_price = float(pos.get('liquidationPrice', 0))

                # 获取当前价格
                current_price = self.market_analyzer.get_current_price(symbol)

                enriched_positions.append({
                    'symbol': symbol,
                    'quantity': abs(position_amt),
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'liquidation_price': liquidation_price,
                    'unrealized_pnl': unrealized_pnl,
                    'leverage': leverage,
                    'position_side': 'LONG' if position_amt > 0 else 'SHORT',
                    'notional_usd': abs(position_amt) * current_price
                })

            return enriched_positions

        except Exception as e:
            logger.error(f"获取持仓信息失败: {e}")
            return []

    def get_account_summary(self) -> Dict:
        """
        获取账户摘要（包括总价值、收益率等）

        Returns:
            账户摘要
        """
        try:
            account_info = self.binance_client.get_futures_account_info()
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
            total_unrealized_profit = float(account_info.get('totalUnrealizedProfit', 0))
            total_margin_balance = float(account_info.get('totalMarginBalance', 0))
            available_balance = float(account_info.get('availableBalance', 0))

            return {
                'total_wallet_balance': total_wallet_balance,
                'total_unrealized_profit': total_unrealized_profit,
                'total_margin_balance': total_margin_balance,
                'available_balance': available_balance,
                'current_account_value': total_margin_balance
            }

        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return {
                'total_wallet_balance': 0,
                'total_unrealized_profit': 0,
                'total_margin_balance': 0,
                'available_balance': 0,
                'current_account_value': 0
            }

    def generate_comprehensive_prompt(self, symbols: List[str]) -> str:
        """
        生成完整的AI决策提示词（模拟用户展示的格式）

        Args:
            symbols: 要分析的交易对列表

        Returns:
            完整的提示词字符串
        """
        # 更新运行状态
        self.runtime_state.update_runtime()
        runtime_info = self.runtime_state.get_state()

        # 获取账户信息
        account_summary = self.get_account_summary()
        positions = self.get_all_positions_info()

        # 生成提示词头部
        prompt = f"""It has been {runtime_info['total_runtime_minutes']} minutes since you started trading.
The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} and you've been invoked {runtime_info['total_ai_calls']} times.

Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

CURRENT MARKET STATE FOR ALL COINS

"""

        # 为每个交易对生成数据
        for symbol in symbols:
            try:
                logger.info(f"正在生成 {symbol} 的市场数据...")

                # 获取完整市场上下文
                market_context = self.market_analyzer.get_comprehensive_market_context(symbol)

                snapshot = market_context['current_snapshot']
                intraday = market_context['intraday_series']
                context_4h = market_context['long_term_context_4h']
                futures = market_context['futures_market']

                prompt += f"""
ALL {symbol} DATA

current_price = {snapshot['price']}, current_ema20 = {snapshot['ema20']:.2f}, current_macd = {snapshot['macd']:.3f}, current_rsi (7 period) = {snapshot['rsi7']:.3f}

In addition, here is the latest {symbol} open interest and funding rate for perps:
Open Interest: Latest: {futures['open_interest']['current']:.2f} Average: {futures['open_interest']['average']:.2f}
Funding Rate: {futures['funding_rate']:.6f}

Intraday series (3-minute intervals, oldest → latest):
Mid prices: {intraday['mid_prices']}
EMA indicators (20-period): {intraday['ema20_values']}
MACD indicators: {intraday['macd_values']}
RSI indicators (7-Period): {intraday['rsi7_values']}
RSI indicators (14-Period): {intraday['rsi14_values']}

Longer-term context (4-hour timeframe):
20-Period EMA: {context_4h['ema20']} vs. 50-Period EMA: {context_4h['ema50']}
3-Period ATR: {context_4h['atr3']} vs. 14-Period ATR: {context_4h['atr14']}
Current Volume: {context_4h['current_volume']:.2f} vs. Average Volume: {context_4h['average_volume']:.2f}
MACD indicators: {context_4h['macd_series']}
RSI indicators (14-Period): {context_4h['rsi14_series']}

"""
            except Exception as e:
                logger.error(f"生成 {symbol} 数据失败: {e}")
                continue

        # 添加账户信息
        prompt += f"""
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Available Cash: {account_summary['available_balance']:.2f}
Current Account Value: {account_summary['current_account_value']:.2f}
Total Unrealized PnL: {account_summary['total_unrealized_profit']:.2f}

"""

        # 添加当前持仓信息
        if positions:
            prompt += "Current live positions & performance:\n"
            for pos in positions:
                prompt += f"""- Symbol: {pos['symbol']}, Quantity: {pos['quantity']:.4f}, Entry Price: {pos['entry_price']:.2f}, Current Price: {pos['current_price']:.2f}, Liquidation Price: {pos['liquidation_price']:.2f}, Unrealized PnL: {pos['unrealized_pnl']:.2f}, Leverage: {pos['leverage']}x, Notional: ${pos['notional_usd']:.2f}
"""
        else:
            prompt += "No open positions.\n"

        prompt += "\n现在，基于以上所有市场数据和账户状态，请做出交易决策。\n"

        return prompt

    def parse_enhanced_decision(self, decision_dict: Dict) -> Dict:
        """
        解析增强的决策结果（包含invalidation_condition、risk_usd等）

        Args:
            decision_dict: AI返回的决策字典

        Returns:
            增强后的决策字典
        """
        # 添加新字段的默认值
        enhanced_decision = decision_dict.copy()

        # 如果没有invalidation_condition，生成一个
        if 'invalidation_condition' not in enhanced_decision:
            action = enhanced_decision.get('action', 'HOLD')
            stop_loss_pct = enhanced_decision.get('stop_loss_pct', 2.0)

            if action in ['OPEN_LONG', 'LONG']:
                enhanced_decision['invalidation_condition'] = f"4-hour close below entry price - {stop_loss_pct}%"
            elif action in ['OPEN_SHORT', 'SHORT']:
                enhanced_decision['invalidation_condition'] = f"4-hour close above entry price + {stop_loss_pct}%"
            else:
                enhanced_decision['invalidation_condition'] = "No specific condition"

        # 如果没有risk_usd，计算一个
        if 'risk_usd' not in enhanced_decision:
            account_summary = self.get_account_summary()
            available_balance = account_summary['available_balance']
            position_size_pct = enhanced_decision.get('position_size', 0)
            stop_loss_pct = enhanced_decision.get('stop_loss_pct', 2.0)

            # 风险金额 = 仓位大小 * 止损百分比
            position_size_usd = available_balance * (position_size_pct / 100)
            enhanced_decision['risk_usd'] = position_size_usd * (stop_loss_pct / 100)

        return enhanced_decision


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    print("Enhanced Decision Engine module loaded successfully")
