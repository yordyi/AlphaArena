"""
AI 驱动的交易引擎
集成 DeepSeek API 进行智能交易决策
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
import time
import pandas as pd

from deepseek_client import DeepSeekClient
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager


class AITradingEngine:
    """AI 交易引擎"""

    def __init__(self, deepseek_api_key: str, binance_client: BinanceClient,
                 market_analyzer: MarketAnalyzer, risk_manager: RiskManager):
        """
        初始化 AI 交易引擎

        Args:
            deepseek_api_key: DeepSeek API 密钥
            binance_client: Binance 客户端
            market_analyzer: 市场分析器
            risk_manager: 风险管理器
        """
        self.deepseek = DeepSeekClient(deepseek_api_key)
        self.binance = binance_client
        self.market_analyzer = market_analyzer
        self.risk_manager = risk_manager

        self.logger = logging.getLogger(__name__)
        self.trade_history = []

        # 交易冷却期 (symbol -> timestamp)
        # 防止在短时间内重复尝试失败的交易
        self.trade_cooldown = {}
        self.cooldown_seconds = 900  # 15分钟冷却期

    def analyze_and_trade(self, symbol: str, max_position_pct: float = 10.0) -> Dict:
        """
        分析市场并执行交易

        Args:
            symbol: 交易对（如 BTCUSDT）
            max_position_pct: 最大仓位百分比

        Returns:
            交易结果
        """
        try:
            # 0. 检查冷却期（防止重复尝试失败的交易）
            current_time = time.time()
            if symbol in self.trade_cooldown:
                cooldown_until = self.trade_cooldown[symbol]
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    self.logger.info(f"[{symbol}] 冷却期中，还需等待 {remaining//60}分{remaining%60}秒")
                    return {
                        'success': True,
                        'action': 'COOLDOWN',
                        'reason': f'冷却期中（还需{remaining//60}分钟）'
                    }

            # 1. 检查最近胜率（仅记录，不阻止交易）
            recent_win_rate = self._calculate_recent_win_rate(n=5)
            if len(self.trade_history) >= 5:
                if recent_win_rate < 0.4:
                    self.logger.warning(f"[{symbol}] ⚠️  近5笔胜率较低: {recent_win_rate*100:.1f}% - AI将根据这个信息自主决策")
                elif recent_win_rate > 0.6:
                    self.logger.info(f"[{symbol}] ✅ 近5笔胜率良好: {recent_win_rate*100:.1f}%")
                else:
                    self.logger.info(f"[{symbol}] 📊 近5笔胜率: {recent_win_rate*100:.1f}%")

            # 2. 收集市场数据
            self.logger.info(f"[{symbol}] 开始分析...")
            market_data = self._gather_market_data(symbol)

            # 2. 获取账户信息
            account_info = self._get_account_info()

            # 3. 双模型决策系统：推理模型 + 日常模型
            # 判断是否使用推理模型（Reasoner）
            use_reasoner = self._should_use_reasoner(symbol, market_data, account_info)

            if use_reasoner:
                self.logger.info(f"[{symbol}] 🧠 调用 DeepSeek Reasoner 推理模型...")
                ai_result = self.deepseek.analyze_with_reasoning(
                    market_data=market_data,
                    account_info=account_info,
                    trade_history=self.trade_history[-10:]
                )
            else:
                self.logger.info(f"[{symbol}] 💬 调用 DeepSeek Chat 日常模型...")
                ai_result = self.deepseek.analyze_market_and_decide(
                    market_data,
                    account_info,
                    self.trade_history
                )

            if not ai_result['success']:
                return {
                    'success': False,
                    'error': 'AI 决策失败',
                    'details': ai_result
                }

            decision = ai_result['decision']
            model_used = ai_result.get('model_used', 'deepseek-chat')
            reasoning_content = ai_result.get('reasoning_content', '')

            self.logger.info(f"[{symbol}] AI决策 ({model_used}): {decision['action']} (信心度: {decision['confidence']}%)")
            self.logger.info(f"[{symbol}] 理由: {decision['reasoning']}")
            if reasoning_content:
                self.logger.info(f"[{symbol}] 🧠 推理过程: {reasoning_content[:300]}...")

            # 4. ✅ 完全信任AI决策，不设置信心阈值
            # DeepSeek会根据自己的判断决定信心度，我们完全尊重AI的自主权

            # 执行交易
            trade_result = self._execute_trade(symbol, decision, max_position_pct)

            # 如果交易失败，设置冷却期（防止重复尝试）
            if not trade_result.get('success', False):
                self.trade_cooldown[symbol] = time.time() + self.cooldown_seconds
                self.logger.info(f"[{symbol}] 交易失败，设置 {self.cooldown_seconds//60} 分钟冷却期")

            # 记录交易历史
            self._record_trade(symbol, decision, trade_result)

            return {
                'success': True,
                'symbol': symbol,
                'ai_decision': decision,
                'trade_result': trade_result
            }

        except Exception as e:
            self.logger.error(f"[{symbol}] 交易执行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_position_for_closing(self, symbol: str, position: Dict) -> Dict:
        """
        评估现有持仓是否应该平仓

        Args:
            symbol: 交易对
            position: 当前持仓信息

        Returns:
            评估结果，包含AI决策
        """
        try:
            from datetime import datetime, timezone

            self.logger.info(f"[{symbol}] 🔍 AI评估持仓...")

            # 获取市场数据
            market_data = self._gather_market_data(symbol)

            # 获取账户信息
            account_info = self._get_account_info()

            # 构建持仓信息
            entry_price = float(position.get('entryPrice', 0))
            current_price = market_data['current_price']
            unrealized_pnl = float(position.get('unRealizedProfit', 0))
            position_amt = float(position.get('positionAmt', 0))
            leverage = int(position.get('leverage', 1))

            # 计算持仓盈亏百分比（相对于名义价值）
            notional_value = abs(position_amt) * entry_price
            pnl_pct = (unrealized_pnl / notional_value * 100) if notional_value > 0 else 0

            # 计算持仓时间
            try:
                update_time = int(position.get('updateTime', 0))
                if update_time > 0:
                    update_dt = datetime.fromtimestamp(update_time / 1000, tz=timezone.utc)
                    holding_duration = datetime.now(timezone.utc) - update_dt
                    holding_hours = holding_duration.total_seconds() / 3600
                    holding_time_str = f"{holding_hours:.1f}小时"
                else:
                    holding_time_str = "未知"
            except Exception:
                holding_time_str = "未知"

            # 判断持仓方向
            if position_amt > 0:
                position_side = 'LONG'
            else:
                position_side = 'SHORT'

            position_info = {
                'symbol': symbol,
                'side': position_side,
                'entry_price': entry_price,
                'current_price': current_price,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': round(pnl_pct, 2),
                'leverage': leverage,
                'holding_time': holding_time_str,
                'position_amt': abs(position_amt),
                'notional_value': round(notional_value, 2)
            }

            self.logger.info(f"[{symbol}] 持仓: {position_side} {abs(position_amt)} ({leverage}x杠杆)")
            self.logger.info(f"[{symbol}] 开仓价: ${entry_price:.2f}, 当前价: ${current_price:.2f}")
            self.logger.info(f"[{symbol}] 盈亏: ${unrealized_pnl:+.2f} ({pnl_pct:+.2f}%)")

            # 调用DeepSeek评估持仓
            decision = self.deepseek.evaluate_position_for_closing(
                position_info,
                market_data,
                account_info
            )

            self.logger.info(f"[{symbol}] AI决策: {decision.get('action', 'HOLD')}")
            self.logger.info(f"[{symbol}] 信心度: {decision.get('confidence', 0)}%")
            self.logger.info(f"[{symbol}] 理由: {decision.get('reasoning', '')}")

            return {
                'success': True,
                'decision': decision
            }

        except Exception as e:
            self.logger.error(f"[{symbol}] 持仓评估失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def _gather_market_data(self, symbol: str) -> Dict:
        """收集市场数据"""
        try:
            # 获取市场概览
            overview = self.market_analyzer.get_market_overview(symbol)

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 获取 K 线数据计算技术指标（使用 MarketAnalyzer）
            df = self.market_analyzer.get_kline_data(symbol, '1h', limit=100)

            # 计算技术指标
            rsi = self.market_analyzer.calculate_rsi(df, period=14)
            macd_line, signal_line, histogram = self.market_analyzer.calculate_macd(df)
            upper_band, middle_band, lower_band = self.market_analyzer.calculate_bollinger_bands(df, period=20)

            # 计算移动平均线
            sma_20 = self.market_analyzer.calculate_sma(df, 20)
            sma_50 = self.market_analyzer.calculate_sma(df, 50)

            # 提取收盘价列表（用于其他计算）
            closes = df['close'].tolist()

            # 提取价格信息
            price_info = overview.get('price_info', {})

            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_change_24h': price_info.get('change_percent', 0),
                'volume_24h': price_info.get('quote_volume_24h', 0),
                'rsi': round(rsi.iloc[-1], 2) if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50,
                'macd': {
                    'macd': round(macd_line.iloc[-1], 4) if len(macd_line) > 0 else 0,
                    'signal': round(signal_line.iloc[-1], 4) if len(signal_line) > 0 else 0,
                    'histogram': round(histogram.iloc[-1], 4) if len(histogram) > 0 else 0
                },
                'bollinger_bands': {
                    'upper': round(upper_band.iloc[-1], 2) if len(upper_band) > 0 else 0,
                    'middle': round(middle_band.iloc[-1], 2) if len(middle_band) > 0 else 0,
                    'lower': round(lower_band.iloc[-1], 2) if len(lower_band) > 0 else 0
                },
                'moving_averages': {
                    'sma_20': round(sma_20.iloc[-1], 2) if len(sma_20) > 0 else 0,
                    'sma_50': round(sma_50.iloc[-1], 2) if len(sma_50) > 0 else 0
                },
                'trend': self._determine_trend(current_price, sma_20.iloc[-1] if len(sma_20) > 0 else current_price, sma_50.iloc[-1] if len(sma_50) > 0 else current_price),
                'support_levels': self._find_support_levels(closes),
                'resistance_levels': self._find_resistance_levels(closes),
                'atr': self._calculate_atr(df)
            }

        except Exception as e:
            self.logger.error(f"收集市场数据失败: {e}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
            raise

    def _get_account_info(self) -> Dict:
        """获取账户信息"""
        try:
            # 获取合约余额
            futures_balance = self.binance.get_futures_usdt_balance()

            # 获取持仓
            positions = self.binance.get_active_positions()

            # 计算未实现盈亏
            total_unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)

            return {
                'balance': futures_balance,
                'total_value': futures_balance + total_unrealized_pnl,
                'positions': positions,
                'unrealized_pnl': total_unrealized_pnl
            }

        except Exception as e:
            self.logger.error(f"获取账户信息失败: {e}")
            raise

    def _execute_trade(self, symbol: str, decision: Dict, max_position_pct: float) -> Dict:
        """
        执行交易决策

        Args:
            symbol: 交易对
            decision: AI 决策
            max_position_pct: 最大仓位百分比

        Returns:
            交易结果
        """
        action = decision['action']
        # ✅ 完全由DeepSeek决定！所有参数都由AI自主决策
        # fallback值仅在AI未返回时使用（理论上不应该发生）
        position_size_pct = min(decision.get('position_size', 1), max_position_pct)  # AI未返回时用最保守的1%
        leverage = decision.get('leverage', 1)  # AI未返回时不使用杠杆

        # 🔒 V5.0: 杠杆铁律 - 强制上限20x
        MAX_LEVERAGE = 20
        if leverage > MAX_LEVERAGE:
            self.logger.warning(f"⚠️ AI建议杠杆{leverage}x超过上限{MAX_LEVERAGE}x，已强制降至{MAX_LEVERAGE}x")
            leverage = MAX_LEVERAGE

        stop_loss_pct = decision.get('stop_loss_pct', 1) / 100  # AI未返回时最保守1%止损
        take_profit_pct = decision.get('take_profit_pct', 2) / 100  # AI未返回时最保守2%止盈

        # 获取账户余额
        balance = self.binance.get_futures_usdt_balance()
        # 使用DeepSeek决定的仓位大小
        trade_amount = balance * (position_size_pct / 100)

        try:
            if action == 'BUY':
                # 开多单
                result = self._open_long_position(
                    symbol, trade_amount, leverage,
                    stop_loss_pct, take_profit_pct
                )
                return result

            elif action == 'SELL':
                # 开空单
                result = self._open_short_position(
                    symbol, trade_amount, leverage,
                    stop_loss_pct, take_profit_pct
                )
                return result

            elif action == 'CLOSE':
                # 平仓
                result = self.binance.close_position(symbol)
                return {'success': True, 'action': 'CLOSE', 'result': result}

            elif action == 'HOLD':
                return {'success': True, 'action': 'HOLD'}

            else:
                return {'success': False, 'error': f'未知操作: {action}'}

        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
            return {'success': False, 'error': str(e)}

    def _open_long_position(self, symbol: str, amount: float, leverage: int,
                           stop_loss_pct: float, take_profit_pct: float) -> Dict:
        """开多单"""
        try:
            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price

            # 根据交易对设置精度（币安合约规则）
            if 'BTC' in symbol:
                quantity = round(raw_quantity, 3)  # BTC: 0.001
            elif 'ETH' in symbol:
                quantity = round(raw_quantity, 3)  # ETH: 0.001
            elif 'BNB' in symbol:
                quantity = round(raw_quantity, 1)  # BNB: 0.1
            elif 'SOL' in symbol:
                quantity = round(raw_quantity, 1)  # SOL: 0.1
            else:
                quantity = round(raw_quantity, 3)  # 默认: 0.001

            # 确保不为0（小账户可能出现）
            if quantity == 0:
                self.logger.warning(f"{symbol} 计算数量为0，账户太小无法交易")
                return {'success': False, 'error': '账户余额太小，无法满足最低交易量'}

            # 计算止损止盈价格（四舍五入到2位小数，USDT精度要求）
            stop_loss = round(current_price * (1 - stop_loss_pct), 2)
            take_profit = round(current_price * (1 + take_profit_pct), 2)

            # 开多单
            order = self.binance.create_futures_order(
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quantity=quantity,
                position_side='LONG'
            )

            # 设置止损（不使用reduce_only参数）
            self.binance.create_futures_order(
                symbol=symbol,
                side='SELL',
                order_type='STOP_MARKET',
                quantity=quantity,
                position_side='LONG',
                stopPrice=stop_loss
            )

            # 设置止盈（不使用reduce_only参数）
            self.binance.create_futures_order(
                symbol=symbol,
                side='SELL',
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                position_side='LONG',
                stopPrice=take_profit
            )

            self.logger.info(f"✅ 开多单成功: {symbol}, 数量: {quantity}, 杠杆: {leverage}x, 止损: {stop_loss}, 止盈: {take_profit}")

            return {
                'success': True,
                'action': 'OPEN_LONG',
                'symbol': symbol,
                'quantity': quantity,
                'leverage': leverage,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"❌ 开多单失败: {e}")
            return {'success': False, 'error': str(e)}

    def _open_short_position(self, symbol: str, amount: float, leverage: int,
                            stop_loss_pct: float, take_profit_pct: float) -> Dict:
        """开空单"""
        try:
            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 计算数量并按交易对调整精度
            raw_quantity = (amount * leverage) / current_price

            # 根据交易对设置精度（币安合约规则）
            if 'BTC' in symbol:
                quantity = round(raw_quantity, 3)  # BTC: 0.001
            elif 'ETH' in symbol:
                quantity = round(raw_quantity, 3)  # ETH: 0.001
            elif 'BNB' in symbol:
                quantity = round(raw_quantity, 1)  # BNB: 0.1
            elif 'SOL' in symbol:
                quantity = round(raw_quantity, 1)  # SOL: 0.1
            else:
                quantity = round(raw_quantity, 3)  # 默认: 0.001

            # 确保不为0（小账户可能出现）
            if quantity == 0:
                self.logger.warning(f"{symbol} 计算数量为0，账户太小无法交易")
                return {'success': False, 'error': '账户余额太小，无法满足最低交易量'}

            # 计算止损止盈价格（四舍五入到2位小数，USDT精度要求）
            stop_loss = round(current_price * (1 + stop_loss_pct), 2)
            take_profit = round(current_price * (1 - take_profit_pct), 2)

            # 开空单
            order = self.binance.create_futures_order(
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=quantity,
                position_side='SHORT'
            )

            # 设置止损（不使用reduce_only参数）
            self.binance.create_futures_order(
                symbol=symbol,
                side='BUY',
                order_type='STOP_MARKET',
                quantity=quantity,
                position_side='SHORT',
                stopPrice=stop_loss
            )

            # 设置止盈（不使用reduce_only参数）
            self.binance.create_futures_order(
                symbol=symbol,
                side='BUY',
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                position_side='SHORT',
                stopPrice=take_profit
            )

            self.logger.info(f"✅ 开空单成功: {symbol}, 数量: {quantity}, 杠杆: {leverage}x, 止损: {stop_loss}, 止盈: {take_profit}")

            return {
                'success': True,
                'action': 'OPEN_SHORT',
                'symbol': symbol,
                'quantity': quantity,
                'leverage': leverage,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'order': order
            }

        except Exception as e:
            self.logger.error(f"❌ 开空单失败: {e}")
            return {'success': False, 'error': str(e)}

    def _record_trade(self, symbol: str, decision: Dict, trade_result: Dict):
        """记录交易历史"""
        trade_record = {
            'time': datetime.now().isoformat(),
            'symbol': symbol,
            'action': decision['action'],
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            'result': trade_result,
            'pnl': trade_result.get('pnl', 0)
        }

        self.trade_history.append(trade_record)

        # 只保留最近 100 笔交易
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]

    def _determine_trend(self, current_price: float, sma_20: float, sma_50: float) -> str:
        """判断趋势"""
        if current_price > sma_20 > sma_50:
            return "强势上涨"
        elif current_price > sma_20:
            return "温和上涨"
        elif current_price < sma_20 < sma_50:
            return "强势下跌"
        elif current_price < sma_20:
            return "温和下跌"
        else:
            return "震荡"

    def _find_support_levels(self, closes: List[float]) -> List[float]:
        """寻找支撑位"""
        recent_lows = []
        for i in range(10, len(closes) - 10):
            if closes[i] == min(closes[i-10:i+10]):
                recent_lows.append(closes[i])
        return sorted(recent_lows)[-3:] if recent_lows else []

    def _find_resistance_levels(self, closes: List[float]) -> List[float]:
        """寻找阻力位"""
        recent_highs = []
        for i in range(10, len(closes) - 10):
            if closes[i] == max(closes[i-10:i+10]):
                recent_highs.append(closes[i])
        return sorted(recent_highs)[-3:] if recent_highs else []

    def _calculate_recent_win_rate(self, n: int = 5) -> float:
        """
        计算最近N笔交易的胜率

        Args:
            n: 最近N笔交易

        Returns:
            胜率 (0.0-1.0)
        """
        if not self.trade_history or len(self.trade_history) == 0:
            return 0.5  # 无历史数据时返回50%

        recent_trades = self.trade_history[-n:]
        wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)

        if len(recent_trades) == 0:
            return 0.5

        return wins / len(recent_trades)

    def _calculate_atr(self, df) -> float:
        """计算 ATR（接受 DataFrame）"""
        try:
            import pandas as pd
            tr_list = []
            for i in range(1, min(15, len(df))):
                high = df['high'].iloc[i]
                low = df['low'].iloc[i]
                prev_close = df['close'].iloc[i-1]
                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                tr_list.append(tr)
            return round(sum(tr_list) / len(tr_list), 2) if tr_list else 0
        except Exception:
            return 0

    def _should_use_reasoner(self, symbol: str, market_data: Dict, account_info: Dict) -> bool:
        """
        判断是否应该使用推理模型（Reasoner）
        
        推理模型使用场景（优先级从高到低）：
        1. 开仓决策（新仓位）
        2. 重大市场变化（24h波动>5%）
        3. 连续亏损后（近3笔全亏）
        4. 账户回撤较大（>10%）
        5. 高风险操作（杠杆>10x）
        
        日常模型使用场景：
        1. 持仓评估（是否平仓）
        2. 常规市场监控
        3. 低波动市场
        
        Args:
            symbol: 交易对
            market_data: 市场数据
            account_info: 账户信息
            
        Returns:
            True表示使用推理模型，False使用日常模型
        """
        # 条件1：开仓决策使用推理模型（最重要）
        # 检查是否已有持仓
        has_position = False
        try:
            positions = self.binance.get_positions()
            for pos in positions:
                if pos['symbol'] == symbol and float(pos.get('positionAmt', 0)) != 0:
                    has_position = True
                    break
        except:
            pass
        
        if not has_position:
            self.logger.info(f"[{symbol}] ✅ 开仓决策 → 使用推理模型")
            return True
        
        # 条件2：重大市场变化（24h波动>5%）
        price_change_24h = abs(market_data.get('price_change_24h', 0))
        if price_change_24h > 5:
            self.logger.info(f"[{symbol}] ✅ 重大市场变化({price_change_24h:.1f}%) → 使用推理模型")
            return True
        
        # 条件3：连续亏损（近3笔全亏）
        if len(self.trade_history) >= 3:
            recent_3 = self.trade_history[-3:]
            all_loss = all(t.get('pnl', 0) < 0 for t in recent_3)
            if all_loss:
                self.logger.info(f"[{symbol}] ✅ 连续亏损 → 使用推理模型深度分析")
                return True
        
        # 条件4：账户回撤较大（>10%）
        initial_balance = account_info.get('initial_balance', 100)
        current_balance = account_info.get('balance', 100)
        drawdown_pct = ((initial_balance - current_balance) / initial_balance * 100) if initial_balance > 0 else 0
        if drawdown_pct > 10:
            self.logger.info(f"[{symbol}] ✅ 账户回撤({drawdown_pct:.1f}%) → 使用推理模型")
            return True
        
        # 条件5：高胜率时可使用推理模型优化策略
        recent_win_rate = self._calculate_recent_win_rate(n=5)
        if recent_win_rate > 0.7:
            self.logger.info(f"[{symbol}] ✅ 高胜率({recent_win_rate*100:.0f}%) → 使用推理模型优化")
            return True
        
        # 其他情况：使用日常模型（持仓评估、常规监控）
        self.logger.info(f"[{symbol}] 💬 常规评估 → 使用日常模型")
        return False
