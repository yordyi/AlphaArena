"""
高级仓位管理模块 - Advanced Position Management Strategies
提供专业级的仓位管理策略，供DeepSeek-V3 AI使用

策略清单：
1. 滚仓（Rolling Position）- 使用浮盈加仓，在大趋势中复利增长
2. 金字塔加仓 (Pyramiding) - 在有利价格逐步递减加仓
3. 多级止盈 (Multiple Take Profits) - 分批获利，锁定利润
4. 移动止损到盈亏平衡 (Move Stop to Breakeven) - 盈利后保护本金
5. ATR自适应止损 - 根据波动率动态调整止损
6. 动态杠杆调整 - 根据市场波动率自动调整杠杆
7. 对冲策略 (Hedging) - 开反向仓位对冲风险
8. 仓位再平衡 (Rebalancing) - 动态调整仓位大小
9. 资金费率套利 - 根据资金费率开反向套利仓位
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer


class AdvancedPositionManager:
    """高级仓位管理器 - 实现专业级交易策略"""

    def __init__(self, binance_client: BinanceClient, market_analyzer: MarketAnalyzer):
        """
        初始化高级仓位管理器

        Args:
            binance_client: Binance API客户端
            market_analyzer: 市场分析器（用于获取ATR等指标）
        """
        self.client = binance_client
        self.analyzer = market_analyzer
        self.logger = logging.getLogger(__name__)

    # ==================== 1. 滚仓策略 ====================

    def can_roll_position(self, symbol: str, profit_threshold_pct: float = 10.0,
                          max_rolls: int = 3) -> Tuple[bool, str, float]:
        """
        检查是否可以进行滚仓（使用浮盈加仓）

        滚仓策略：
        - 当浮盈达到一定百分比时，使用部分浮盈开新仓
        - 在强趋势中实现复利增长
        - 控制最大滚仓次数，避免过度杠杆

        Args:
            symbol: 交易对
            profit_threshold_pct: 浮盈达到多少百分比可以滚仓（默认10%）
            max_rolls: 最多允许滚几次（默认3次）

        Returns:
            (是否可以滚仓, 原因, 可用于滚仓的浮盈金额USDT)
        """
        try:
            # 获取当前持仓
            positions = self.client.get_active_positions()
            target_position = None

            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break

            if not target_position:
                return False, "无持仓", 0.0

            # 获取浮盈信息
            unrealized_pnl = float(target_position.get('unRealizedProfit', 0))
            position_amt = float(target_position.get('positionAmt', 0))
            entry_price = float(target_position.get('entryPrice', 0))
            mark_price = float(target_position.get('markPrice', 0))

            if entry_price == 0:
                return False, "入场价格为0", 0.0

            # 计算浮盈百分比
            position_value = abs(position_amt) * entry_price
            profit_pct = (unrealized_pnl / position_value) * 100

            # 检查浮盈是否达到阈值
            if profit_pct < profit_threshold_pct:
                return False, f"浮盈{profit_pct:.2f}%未达到阈值{profit_threshold_pct}%", 0.0

            # 检查是否超过最大滚仓次数（通过仓位大小推断）
            # 简化逻辑：如果当前仓位已经很大，限制继续滚仓
            available_balance = self.client.get_futures_available_balance()
            position_margin = position_value / float(target_position.get('leverage', 1))

            if position_margin > available_balance * 0.8:  # 仓位保证金超过可用余额80%
                return False, "仓位保证金已接近上限，不建议继续滚仓", 0.0

            # 计算可用于滚仓的浮盈（使用50%的浮盈）
            usable_pnl = unrealized_pnl * 0.5  # 保守策略，只用一半浮盈

            if usable_pnl < 10:  # 至少10 USDT才滚仓
                return False, f"可用浮盈{usable_pnl:.2f} USDT太少", 0.0

            self.logger.info(
                f"✅ 可以滚仓 {symbol}: 浮盈{profit_pct:.2f}% "
                f"(${unrealized_pnl:.2f}), 可用于滚仓: ${usable_pnl:.2f}"
            )

            return True, "满足滚仓条件", usable_pnl

        except Exception as e:
            self.logger.error(f"检查滚仓条件失败: {e}")
            return False, f"检查失败: {str(e)}", 0.0

    def execute_roll_position(self, symbol: str, usable_pnl: float,
                              leverage: int = 2) -> Dict:
        """
        执行滚仓：使用浮盈开新仓

        Args:
            symbol: 交易对
            usable_pnl: 可用于滚仓的浮盈金额（USDT）
            leverage: 滚仓使用的杠杆（默认2x，保守策略）

        Returns:
            订单结果
        """
        try:
            # 获取当前持仓方向
            positions = self.client.get_active_positions()
            target_position = None

            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break

            if not target_position:
                raise ValueError("无持仓，无法滚仓")

            position_amt = float(target_position.get('positionAmt', 0))
            current_price = float(target_position.get('markPrice', 0))

            # 判断持仓方向
            if position_amt > 0:
                side = 'BUY'  # 多仓，继续做多
            else:
                side = 'SELL'  # 空仓，继续做空

            # 计算滚仓数量：usable_pnl * leverage / price
            quantity = (usable_pnl * leverage) / current_price
            quantity = round(quantity, 3)  # 精度控制

            # 设置杠杆
            self.client.set_leverage(symbol, leverage)

            # 执行滚仓订单
            result = self.client.create_futures_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )

            self.logger.info(
                f"🔄 滚仓成功 {symbol}: {side} {quantity} @ ~${current_price:.2f}, "
                f"使用浮盈 ${usable_pnl:.2f}, 杠杆 {leverage}x"
            )

            return {
                'success': True,
                'order': result,
                'roll_size': usable_pnl,
                'quantity': quantity,
                'leverage': leverage
            }

        except Exception as e:
            self.logger.error(f"执行滚仓失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 2. 金字塔加仓策略 ====================

    def pyramid_add_position(self, symbol: str, side: str, base_size_usdt: float,
                             current_position_count: int = 0,
                             max_pyramids: int = 3,
                             reduction_factor: float = 0.5) -> Dict:
        """
        金字塔加仓：每次加仓递减，形成金字塔结构

        例如：
        - 第1次: 100 USDT
        - 第2次: 50 USDT  (100 * 0.5)
        - 第3次: 25 USDT  (50 * 0.5)

        Args:
            symbol: 交易对
            side: BUY 或 SELL
            base_size_usdt: 基础仓位大小（USDT）
            current_position_count: 当前已有多少层金字塔（从0开始）
            max_pyramids: 最多允许几层金字塔
            reduction_factor: 每次递减系数（默认0.5，即每次减半）

        Returns:
            订单结果
        """
        try:
            if current_position_count >= max_pyramids:
                raise ValueError(f"已达到最大金字塔层数 {max_pyramids}")

            # 计算本次加仓大小
            current_size = base_size_usdt * (reduction_factor ** current_position_count)

            if current_size < 10:  # 最小10 USDT
                raise ValueError(f"加仓大小{current_size:.2f} USDT太小")

            # 获取当前价格
            ticker = self.client.get_ticker_price(symbol)
            price = float(ticker['price'])

            # 计算数量
            quantity = current_size / price
            quantity = round(quantity, 3)

            # 执行加仓
            result = self.client.create_futures_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )

            self.logger.info(
                f"📐 金字塔加仓 {symbol} 第{current_position_count + 1}层: "
                f"{side} {quantity} @ ~${price:.2f} (${current_size:.2f} USDT)"
            )

            return {
                'success': True,
                'order': result,
                'pyramid_level': current_position_count + 1,
                'size_usdt': current_size,
                'quantity': quantity
            }

        except Exception as e:
            self.logger.error(f"金字塔加仓失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 3. 多级止盈策略 ====================

    def set_multiple_take_profits(self, symbol: str, side: str, entry_price: float,
                                   total_quantity: float,
                                   tp_levels: List[Dict]) -> List[Dict]:
        """
        设置多级止盈：在不同价格点分批获利

        Args:
            symbol: 交易对
            side: 原始方向 (BUY 多头 -> 止盈用SELL, SELL 空头 -> 止盈用BUY)
            entry_price: 入场价格
            total_quantity: 总持仓数量
            tp_levels: 止盈级别列表，格式:
                [
                    {'profit_pct': 10, 'close_pct': 30},  # 盈利10%时平30%仓位
                    {'profit_pct': 20, 'close_pct': 40},  # 盈利20%时平40%剩余
                    {'profit_pct': 30, 'close_pct': 100}  # 盈利30%时平全部剩余
                ]

        Returns:
            止盈订单结果列表
        """
        try:
            results = []
            remaining_qty = total_quantity

            # 确定止盈方向
            tp_side = 'SELL' if side == 'BUY' else 'BUY'

            for level in tp_levels:
                profit_pct = level['profit_pct']
                close_pct = level['close_pct']

                # 计算止盈价格
                if side == 'BUY':
                    tp_price = entry_price * (1 + profit_pct / 100)
                else:
                    tp_price = entry_price * (1 - profit_pct / 100)

                # 计算本级止盈数量
                qty = remaining_qty * (close_pct / 100)
                qty = round(qty, 3)

                # 创建止盈订单
                order = self.client.create_take_profit_order(
                    symbol=symbol,
                    side=tp_side,
                    quantity=qty,
                    stop_price=tp_price,
                    reduce_only=True
                )

                results.append({
                    'profit_pct': profit_pct,
                    'price': tp_price,
                    'quantity': qty,
                    'order': order
                })

                remaining_qty -= qty

                self.logger.info(
                    f"📈 设置止盈 Level {len(results)}: "
                    f"盈利{profit_pct}%时平{close_pct}%仓位 @ ${tp_price:.2f}"
                )

            return results

        except Exception as e:
            self.logger.error(f"设置多级止盈失败: {e}")
            return []

    # ==================== 4. 移动止损到盈亏平衡 ====================

    def move_stop_to_breakeven(self, symbol: str, entry_price: float,
                               profit_trigger_pct: float = 5.0,
                               breakeven_offset_pct: float = 0.1) -> Dict:
        """
        移动止损到盈亏平衡点

        当盈利达到一定百分比后，将止损移至成本价附近，保护本金

        Args:
            symbol: 交易对
            entry_price: 入场价格
            profit_trigger_pct: 达到多少盈利百分比触发（默认5%）
            breakeven_offset_pct: 盈亏平衡偏移（默认0.1%，略高于成本）

        Returns:
            操作结果
        """
        try:
            # 获取当前持仓
            positions = self.client.get_active_positions()
            target_position = None

            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break

            if not target_position:
                return {'success': False, 'error': '无持仓'}

            position_amt = float(target_position.get('positionAmt', 0))
            mark_price = float(target_position.get('markPrice', 0))

            # 检查是否达到盈利触发条件
            if position_amt > 0:  # 多仓
                profit_pct = ((mark_price - entry_price) / entry_price) * 100
                new_stop_price = entry_price * (1 + breakeven_offset_pct / 100)
                stop_side = 'SELL'
            else:  # 空仓
                profit_pct = ((entry_price - mark_price) / entry_price) * 100
                new_stop_price = entry_price * (1 - breakeven_offset_pct / 100)
                stop_side = 'BUY'

            if profit_pct < profit_trigger_pct:
                return {
                    'success': False,
                    'error': f'盈利{profit_pct:.2f}%未达到触发条件{profit_trigger_pct}%'
                }

            # 取消旧止损订单
            self.client.cancel_stop_orders(symbol)

            # 设置新止损到盈亏平衡点
            order = self.client.create_stop_loss_order(
                symbol=symbol,
                side=stop_side,
                quantity=abs(position_amt),
                stop_price=new_stop_price,
                reduce_only=True
            )

            self.logger.info(
                f"🛡️ 止损已移至盈亏平衡 {symbol}: ${new_stop_price:.2f} "
                f"(成本${entry_price:.2f}, 当前盈利{profit_pct:.2f}%)"
            )

            return {
                'success': True,
                'new_stop_price': new_stop_price,
                'profit_pct': profit_pct,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"移动止损到盈亏平衡失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 5. ATR自适应止损 ====================

    def set_atr_based_stop_loss(self, symbol: str, side: str, entry_price: float,
                                 quantity: float, atr_multiplier: float = 2.0) -> Dict:
        """
        基于ATR设置自适应止损

        ATR（平均真实波幅）反映市场波动性：
        - 高波动：止损距离更大，避免被噪音止损
        - 低波动：止损距离更小，严格风控

        Args:
            symbol: 交易对
            side: BUY 或 SELL
            entry_price: 入场价格
            quantity: 持仓数量
            atr_multiplier: ATR倍数（默认2倍，常用范围1.5-3）

        Returns:
            止损订单结果
        """
        try:
            # 获取ATR
            klines = self.client.get_klines(symbol, '1h', limit=50)
            analysis = self.analyzer.get_comprehensive_analysis(klines)

            atr = analysis.get('atr', 0)
            if atr == 0:
                raise ValueError("ATR计算失败")

            # 计算止损距离
            stop_distance = atr * atr_multiplier

            # 计算止损价格
            if side == 'BUY':
                stop_price = entry_price - stop_distance
                stop_side = 'SELL'
            else:
                stop_price = entry_price + stop_distance
                stop_side = 'BUY'

            # 创建止损订单
            order = self.client.create_stop_loss_order(
                symbol=symbol,
                side=stop_side,
                quantity=quantity,
                stop_price=stop_price,
                reduce_only=True
            )

            stop_distance_pct = (stop_distance / entry_price) * 100

            self.logger.info(
                f"📊 ATR自适应止损 {symbol}: ${stop_price:.2f} "
                f"(ATR={atr:.2f}, 距离{stop_distance_pct:.2f}%)"
            )

            return {
                'success': True,
                'stop_price': stop_price,
                'atr': atr,
                'distance_pct': stop_distance_pct,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"设置ATR止损失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 6. 动态杠杆调整 ====================

    def adjust_leverage_by_volatility(self, symbol: str, base_leverage: int = 5,
                                      min_leverage: int = 2,
                                      max_leverage: int = 10) -> Dict:
        """
        根据市场波动率动态调整杠杆

        波动率高 -> 降低杠杆（风控）
        波动率低 -> 提高杠杆（增加收益）

        Args:
            symbol: 交易对
            base_leverage: 基础杠杆（默认5x）
            min_leverage: 最小杠杆（默认2x）
            max_leverage: 最大杠杆（默认10x）

        Returns:
            调整结果
        """
        try:
            # 获取ATR和价格
            klines = self.client.get_klines(symbol, '1h', limit=50)
            analysis = self.analyzer.get_comprehensive_analysis(klines)

            atr = analysis.get('atr', 0)
            current_price = float(klines[-1][4])  # 收盘价

            if atr == 0 or current_price == 0:
                raise ValueError("数据不足")

            # 计算波动率百分比
            volatility_pct = (atr / current_price) * 100

            # 波动率分级：
            # < 1%: 低波动 -> 高杠杆
            # 1-3%: 中波动 -> 中杠杆
            # > 3%: 高波动 -> 低杠杆
            if volatility_pct < 1.0:
                recommended_leverage = min(max_leverage, base_leverage + 2)
            elif volatility_pct < 3.0:
                recommended_leverage = base_leverage
            else:
                recommended_leverage = max(min_leverage, base_leverage - 2)

            # 设置杠杆
            result = self.client.set_leverage(symbol, recommended_leverage)

            self.logger.info(
                f"⚖️ 动态调整杠杆 {symbol}: {recommended_leverage}x "
                f"(波动率{volatility_pct:.2f}%)"
            )

            return {
                'success': True,
                'leverage': recommended_leverage,
                'volatility_pct': volatility_pct,
                'result': result
            }

        except Exception as e:
            self.logger.error(f"动态调整杠杆失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 7. 对冲策略 ====================

    def open_hedge_position(self, symbol: str, hedge_ratio: float = 0.5) -> Dict:
        """
        开对冲仓位：对当前持仓开反向仓位以降低风险

        Args:
            symbol: 交易对
            hedge_ratio: 对冲比例（默认0.5，即对冲50%）

        Returns:
            对冲订单结果
        """
        try:
            # 获取当前持仓
            positions = self.client.get_active_positions()
            target_position = None

            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break

            if not target_position:
                return {'success': False, 'error': '无持仓可对冲'}

            position_amt = float(target_position.get('positionAmt', 0))

            if position_amt == 0:
                return {'success': False, 'error': '持仓数量为0'}

            # 计算对冲数量和方向
            hedge_quantity = abs(position_amt) * hedge_ratio
            hedge_quantity = round(hedge_quantity, 3)

            hedge_side = 'SELL' if position_amt > 0 else 'BUY'

            # 执行对冲订单（需要开启双向持仓模式）
            order = self.client.create_futures_order(
                symbol=symbol,
                side=hedge_side,
                order_type='MARKET',
                quantity=hedge_quantity,
                position_side='SHORT' if hedge_side == 'SELL' else 'LONG'
            )

            self.logger.info(
                f"🔰 开对冲仓位 {symbol}: {hedge_side} {hedge_quantity} "
                f"(对冲{hedge_ratio * 100}%)"
            )

            return {
                'success': True,
                'hedge_quantity': hedge_quantity,
                'hedge_ratio': hedge_ratio,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"开对冲仓位失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 8. 仓位再平衡 ====================

    def rebalance_position_size(self, symbol: str, target_size_usdt: float) -> Dict:
        """
        仓位再平衡：调整仓位到目标大小

        Args:
            symbol: 交易对
            target_size_usdt: 目标仓位大小（USDT）

        Returns:
            调整结果
        """
        try:
            # 获取当前持仓
            positions = self.client.get_active_positions()
            target_position = None

            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break

            if not target_position:
                return {'success': False, 'error': '无持仓'}

            position_amt = float(target_position.get('positionAmt', 0))
            mark_price = float(target_position.get('markPrice', 0))
            current_size_usdt = abs(position_amt) * mark_price

            # 计算需要调整的量
            diff_usdt = target_size_usdt - current_size_usdt

            if abs(diff_usdt) < 10:  # 差异小于10 USDT不调整
                return {
                    'success': True,
                    'message': f'仓位差异{diff_usdt:.2f} USDT太小，无需调整'
                }

            # 确定调整方向
            if diff_usdt > 0:  # 需要加仓
                side = 'BUY' if position_amt > 0 else 'SELL'
                quantity = abs(diff_usdt / mark_price)
            else:  # 需要减仓
                side = 'SELL' if position_amt > 0 else 'BUY'
                quantity = abs(diff_usdt / mark_price)

            quantity = round(quantity, 3)

            # 执行调整
            order = self.client.create_futures_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                reduce_only=(diff_usdt < 0)  # 减仓时设置reduce_only
            )

            self.logger.info(
                f"⚖️ 仓位再平衡 {symbol}: "
                f"${current_size_usdt:.2f} -> ${target_size_usdt:.2f} "
                f"({side} {quantity})"
            )

            return {
                'success': True,
                'adjustment': diff_usdt,
                'quantity': quantity,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"仓位再平衡失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 9. 资金费率套利 ====================

    def check_funding_arbitrage(self, symbol: str,
                                 threshold_rate: float = 0.01) -> Tuple[bool, str, float]:
        """
        检查资金费率套利机会

        当资金费率过高时，开反向仓位套利

        Args:
            symbol: 交易对
            threshold_rate: 费率阈值（默认0.01即1%）

        Returns:
            (是否有套利机会, 建议操作, 费率)
        """
        try:
            funding_info = self.client.get_current_funding_rate(symbol)
            funding_rate = float(funding_info.get('fundingRate', 0))

            # 正费率：多头支付空头 -> 开空单套利
            # 负费率：空头支付多头 -> 开多单套利
            if funding_rate > threshold_rate:
                return True, 'SELL', funding_rate
            elif funding_rate < -threshold_rate:
                return True, 'BUY', funding_rate
            else:
                return False, 'HOLD', funding_rate

        except Exception as e:
            self.logger.error(f"检查资金费率失败: {e}")
            return False, 'ERROR', 0.0
