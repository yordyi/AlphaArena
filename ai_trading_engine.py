"""
AI 驱动的交易引擎
集成 DeepSeek API 进行智能交易决策
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
import time
import pandas as pd
import os

from deepseek_client import DeepSeekClient
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager
from advanced_position_manager import AdvancedPositionManager
from trailing_stop_manager import TrailingStopManager

# 增强功能：运行状态和增强决策引擎
try:
    from runtime_state_manager import RuntimeStateManager
    from enhanced_decision_engine import EnhancedDecisionEngine
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False


class AITradingEngine:
    """AI 交易引擎"""

    def __init__(self, deepseek_api_key: str, binance_client: BinanceClient,
                 market_analyzer: MarketAnalyzer, risk_manager: RiskManager,
                 performance_tracker=None, roll_tracker=None,
                 enable_enhanced_features: bool = True):
        """
        初始化 AI 交易引擎

        Args:
            deepseek_api_key: DeepSeek API 密钥
            binance_client: Binance 客户端
            market_analyzer: 市场分析器
            risk_manager: 风险管理器
            performance_tracker: 性能追踪器（用于保存交易到文件）
            roll_tracker: ROLL状态追踪器
            enable_enhanced_features: 是否启用增强功能（运行状态追踪、丰富市场数据）
        """
        self.deepseek = DeepSeekClient(deepseek_api_key)
        self.binance = binance_client
        self.market_analyzer = market_analyzer
        self.risk_manager = risk_manager
        self.performance = performance_tracker  # 性能追踪器
        self.roll_tracker = roll_tracker  # ROLL追踪器

        self.logger = logging.getLogger(__name__)
        self.trade_history = []

        # 高级仓位管理器
        self.adv_position_manager = AdvancedPositionManager(binance_client, market_analyzer)

        # [NEW] ATR动态追踪止损管理器
        self.trailing_stop_manager = TrailingStopManager(atr_multiplier=2.0)
        self.logger.info("[OK] ATR动态止损管理器已启用（ATR倍数: 2.0x）")

        # 交易冷却期 (symbol -> timestamp)
        # 防止在短时间内重复尝试失败的交易
        self.trade_cooldown = {}
        self.cooldown_seconds = 900  # 15分钟冷却期

        # 推理模型时间跟踪
        # Chat模型: 每120秒分析（快速反应）
        # Reasoner模型: 每300秒深度分析（重大决策）
        self.last_reasoner_time = 0
        self.reasoner_interval = 600  # 10分钟执行一次Reasoner（降低成本）

        # [NEW] 增强功能初始化
        self.enhanced_features_enabled = enable_enhanced_features and ENHANCED_FEATURES_AVAILABLE
        if self.enhanced_features_enabled:
            try:
                self.runtime_manager = RuntimeStateManager()
                self.enhanced_engine = EnhancedDecisionEngine(
                    binance_client,
                    market_analyzer,
                    self.runtime_manager
                )
                self.logger.info("[OK] 增强功能已启用（运行状态追踪、丰富市场数据）")
            except Exception as e:
                self.logger.warning(f"[WARNING] 增强功能初始化失败，使用标准模式: {e}")
                self.enhanced_features_enabled = False
        else:
            if not ENHANCED_FEATURES_AVAILABLE:
                self.logger.info("ℹ️ 增强功能模块不可用，使用标准模式")
            self.runtime_manager = None
            self.enhanced_engine = None

    def analyze_and_trade(self, symbol: str, max_position_pct: float = 10.0, runtime_stats: Dict = None) -> Dict:
        """
        分析市场并执行交易

        Args:
            symbol: 交易对（如 BTCUSDT）
            max_position_pct: 最大仓位百分比
            runtime_stats: 可选的系统运行统计信息（由bot实例提供）

        Returns:
            交易结果
        """
        try:
            # [NEW] 0a. 更新运行状态（如果启用了增强功能）
            if self.enhanced_features_enabled and self.runtime_manager:
                self.runtime_manager.update_runtime()
                self.runtime_manager.increment_trading_loops()

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

            # 1. 检查最近胜率（仅在有足够交易历史时显示）
            # [V3.4 FIX] 只有在有真实交易记录（pnl不全为0）时才显示胜率警告
            if len(self.trade_history) >= 5:
                # 检查是否有真实交易（至少有一笔非零pnl）
                has_real_trades = any(t.get('pnl', 0) != 0 for t in self.trade_history[-5:])

                if has_real_trades:
                    recent_win_rate = self._calculate_recent_win_rate(n=5)
                    if recent_win_rate < 0.4:
                        self.logger.warning(f"[{symbol}] [WARNING] 近5笔胜率较低: {recent_win_rate*100:.1f}% - AI将根据这个信息自主决策")
                    elif recent_win_rate > 0.6:
                        self.logger.info(f"[{symbol}] [INFO] 近5笔胜率良好: {recent_win_rate*100:.1f}%")
                    else:
                        self.logger.info(f"[{symbol}] [INFO] 近5笔胜率: {recent_win_rate*100:.1f}%")
                else:
                    # 全新系统，无真实交易历史，不显示警告
                    self.logger.debug(f"[{symbol}] [DEBUG] 无有效交易历史，跳过胜率检查")

            # 2. 收集市场数据
            self.logger.info(f"[{symbol}] 开始分析...")

            # [NEW] 如果启用了增强功能，使用MarketAnalyzer获取完整市场上下文
            if self.enhanced_features_enabled and self.market_analyzer:
                market_data = self.market_analyzer.get_comprehensive_market_context(symbol)
                self.logger.debug(f"[{symbol}] [OK] 使用增强市场数据（包含历史序列、4h上下文、资金费率、持仓量）")
            else:
                market_data = self._gather_market_data(symbol)

            # 2. 获取账户信息（传递runtime_stats）
            account_info = self._get_account_info(runtime_stats=runtime_stats)

            # 3. 双模型决策系统：推理模型 + 日常模型
            # 判断是否使用推理模型（Reasoner）
            use_reasoner = self._should_use_reasoner(symbol, market_data, account_info)

            if use_reasoner:
                self.logger.info(f"[{symbol}] [深度分析] 调用 DeepSeek Chat V3.1...")
                ai_result = self.deepseek.analyze_with_reasoning(
                    market_data=market_data,
                    account_info=account_info,
                    trade_history=self.trade_history[-10:]
                )
            else:
                self.logger.info(f"[{symbol}] [快速分析] 调用 DeepSeek Chat V3.1...")
                ai_result = self.deepseek.analyze_market_and_decide(
                    market_data,
                    account_info,
                    self.trade_history
                )

            # [NEW] AI调用后更新计数
            if self.enhanced_features_enabled and self.runtime_manager:
                self.runtime_manager.increment_ai_calls()

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
                self.logger.info(f"[{symbol}] [AI-THINK] 推理过程: {reasoning_content[:300]}...")

            # 4. [OK] 完全信任AI决策，不设置信心阈值
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

    def analyze_position_for_closing(self, symbol: str, position: Dict, runtime_stats: Dict = None) -> Dict:
        """
        评估现有持仓是否应该平仓

        Args:
            symbol: 交易对
            position: 当前持仓信息
            runtime_stats: 可选的系统运行统计信息（由bot实例提供）

        Returns:
            评估结果，包含AI决策
        """
        try:
            from datetime import datetime, timezone

            self.logger.info(f"[{symbol}] [SEARCH] AI评估持仓...")

            # 获取市场数据
            market_data = self._gather_market_data(symbol)

            # 获取账户信息（传递runtime_stats）
            account_info = self._get_account_info(runtime_stats=runtime_stats)

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
                account_info,
                roll_tracker=self.roll_tracker  # [V3.3] 传入ROLL追踪器
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

    def _get_account_info(self, runtime_stats: Dict = None) -> Dict:
        """
        获取账户信息

        Args:
            runtime_stats: 可选的系统运行统计信息（由bot实例提供）
        """
        try:
            # 获取合约余额
            futures_balance = self.binance.get_futures_usdt_balance()

            # 获取持仓
            positions = self.binance.get_active_positions()

            # 计算未实现盈亏
            total_unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)

            account_info = {
                'balance': futures_balance,
                'total_value': futures_balance + total_unrealized_pnl,
                'positions': positions,
                'unrealized_pnl': total_unrealized_pnl
            }

            # [NEW] 如果提供了runtime_stats，添加到account_info
            if runtime_stats:
                account_info['runtime_stats'] = runtime_stats

            return account_info

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
        # [OK] 完全由DeepSeek决定！所有参数都由AI自主决策
        # fallback值仅在AI未返回时使用（理论上不应该发生）
        position_size_pct = min(decision.get('position_size', 1), max_position_pct)  # AI未返回时用最保守的1%

        # 杠杆：由AI自主决定，不设默认值
        leverage = decision.get('leverage')
        if leverage is None:
            self.logger.error(f"[ERROR] AI未返回杠杆建议，跳过此次交易")
            return {'success': False, 'error': 'AI未返回杠杆建议'}

        leverage = int(leverage)

        # 🔒 杠杆上限 - 最大20倍（与DeepSeek提示词保持一致）
        MAX_LEVERAGE = 20
        if leverage > MAX_LEVERAGE:
            self.logger.warning(f"[WARNING] AI建议杠杆{leverage}x超过上限{MAX_LEVERAGE}x，已强制降至{MAX_LEVERAGE}x")
            leverage = MAX_LEVERAGE
        elif leverage < 1:
            self.logger.warning(f"[WARNING] AI建议杠杆{leverage}x过低，已强制调至1x")
            leverage = 1

        stop_loss_pct = decision.get('stop_loss_pct', 1) / 100  # AI未返回时最保守1%止损
        take_profit_pct = decision.get('take_profit_pct', 2) / 100  # AI未返回时最保守2%止盈

        # 获取账户余额
        balance = self.binance.get_futures_usdt_balance()
        # 使用DeepSeek决定的仓位大小
        trade_amount = balance * (position_size_pct / 100)

        try:
            # 统一处理开多动作 (BUY 或 OPEN_LONG)
            if action in ['BUY', 'OPEN_LONG']:
                # 开多单
                result = self._open_long_position(
                    symbol, trade_amount, leverage,
                    stop_loss_pct, take_profit_pct
                )
                return result

            # 统一处理开空动作 (SELL 或 OPEN_SHORT)
            elif action in ['SELL', 'OPEN_SHORT']:
                # 开空单
                result = self._open_short_position(
                    symbol, trade_amount, leverage,
                    stop_loss_pct, take_profit_pct
                )
                return result

            elif action in ['CLOSE', 'CLOSE_LONG', 'CLOSE_SHORT']:
                # 平仓（支持精确方向和部分平仓）

                # 1. 确定平仓方向
                position_side = 'BOTH'  # 默认平所有
                if action == 'CLOSE_LONG':
                    position_side = 'LONG'
                elif action == 'CLOSE_SHORT':
                    position_side = 'SHORT'

                # 2. 检查是否部分平仓（从AI决策中获取）
                close_percentage = decision.get('close_percentage', 100)

                # 3. 执行平仓
                if close_percentage < 100:
                    # 部分平仓
                    self.logger.info(f"[ANALYZE] [{symbol}] 执行部分平仓: {close_percentage}%, 方向: {position_side}")
                    result = self.binance.close_position_partial(
                        symbol,
                        percentage=close_percentage,
                        position_side=position_side
                    )
                else:
                    # 全部平仓
                    self.logger.info(f"[ANALYZE] [{symbol}] 执行全部平仓, 方向: {position_side}")
                    result = self.binance.close_position(symbol, position_side=position_side)

                # 4. 检查平仓是否真的成功
                success = 'orderId' in result or 'clientOrderId' in result

                if not success and result.get('msg') == 'No position to close':
                    self.logger.warning(f"[WARNING] [{symbol}] 没有持仓可平仓")
                    return {'success': False, 'action': action, 'error': '没有持仓'}

                # 5. 平仓成功后取消所有止损止盈订单
                if success:
                    try:
                        cancel_result = self.binance.cancel_stop_orders(symbol)
                        if cancel_result.get('success'):
                            cancelled_count = cancel_result.get('cancelled_count', 0)
                            if cancelled_count > 0:
                                self.logger.info(f"[OK] [{symbol}] 已自动取消 {cancelled_count} 个止损止盈挂单")
                    except Exception as e:
                        self.logger.warning(f"[WARNING] [{symbol}] 取消挂单失败（不影响平仓）: {e}")

                return {'success': success, 'action': action, 'result': result}

            elif action == 'HOLD':
                return {'success': True, 'action': 'HOLD'}

            else:
                self.logger.error(f"[ERROR] 未知操作: {action}")
                return {'success': False, 'error': f'未知操作: {action}'}

        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
            return {'success': False, 'error': str(e)}

    def _open_long_position(self, symbol: str, amount: float, leverage: int,
                           stop_loss_pct: float, take_profit_pct: float) -> Dict:
        """开多单"""
        try:
            # 获取当前价格（需要先获取价格才能计算杠杆）
            current_price = self.market_analyzer.get_current_price(symbol)

            # [CONFIG] 智能杠杆调整：同时满足币安名义价值和精度要求
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
                self.logger.info(f"[IDEA] [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                               f"(名义价值 ${amount*original_leverage:.2f} → ${amount*leverage:.2f}, "
                               f"精度要求: ≥{min_qty} {symbol.replace('USDT', '')})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

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
            elif 'DOGE' in symbol:
                quantity = round(raw_quantity, 0)  # DOGE: 整数
            else:
                quantity = round(raw_quantity, 1)  # 默认: 0.1 (大多数山寨币)

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

            # 设置止损（positionSide已足够，无需reduce_only）
            self.binance.create_futures_order(
                symbol=symbol,
                side='SELL',
                order_type='STOP_MARKET',
                quantity=quantity,
                position_side='LONG',
                stopPrice=stop_loss
            )

            # 设置止盈（positionSide已足够，无需reduce_only）
            self.binance.create_futures_order(
                symbol=symbol,
                side='SELL',
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                position_side='LONG',
                stopPrice=take_profit
            )

            self.logger.info(f"[OK] 开多单成功: {symbol}, 数量: {quantity}, 杠杆: {leverage}x, 止损: {stop_loss}, 止盈: {take_profit}")

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
            self.logger.error(f"[ERROR] 开多单失败: {e}")
            return {'success': False, 'error': str(e)}

    def _open_short_position(self, symbol: str, amount: float, leverage: int,
                            stop_loss_pct: float, take_profit_pct: float) -> Dict:
        """开空单"""
        try:
            # 获取当前价格（需要先获取价格才能计算杠杆）
            current_price = self.market_analyzer.get_current_price(symbol)

            # [CONFIG] 智能杠杆调整：同时满足币安名义价值和精度要求
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
                self.logger.info(f"[IDEA] [{symbol}] 智能杠杆调整: {original_leverage}x → {leverage}x "
                               f"(名义价值 ${amount*original_leverage:.2f} → ${amount*leverage:.2f}, "
                               f"精度要求: ≥{min_qty} {symbol.replace('USDT', '')})")

            # 设置杠杆
            self.binance.set_leverage(symbol, leverage)

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
            elif 'DOGE' in symbol:
                quantity = round(raw_quantity, 0)  # DOGE: 整数
            else:
                quantity = round(raw_quantity, 1)  # 默认: 0.1 (大多数山寨币)

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

            # 设置止损（positionSide已足够，无需reduce_only）
            self.binance.create_futures_order(
                symbol=symbol,
                side='BUY',
                order_type='STOP_MARKET',
                quantity=quantity,
                position_side='SHORT',
                stopPrice=stop_loss
            )

            # 设置止盈（positionSide已足够，无需reduce_only）
            self.binance.create_futures_order(
                symbol=symbol,
                side='BUY',
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                position_side='SHORT',
                stopPrice=take_profit
            )

            self.logger.info(f"[OK] 开空单成功: {symbol}, 数量: {quantity}, 杠杆: {leverage}x, 止损: {stop_loss}, 止盈: {take_profit}")

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
            self.logger.error(f"[ERROR] 开空单失败: {e}")
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

        # [FIX] 同时保存到performance_data.json（如果performance tracker可用）
        if self.performance:
            try:
                self.performance.record_trade({
                    'symbol': symbol,
                    'action': decision['action'],
                    'entry_price': trade_result.get('entry_price') or trade_result.get('price'),
                    'quantity': trade_result.get('quantity'),
                    'leverage': decision.get('leverage', 1),
                    'stop_loss': decision.get('stop_loss'),
                    'take_profit': decision.get('take_profit'),
                    'confidence': decision['confidence'],
                    'reasoning': decision['reasoning']
                })
                self.logger.debug(f"[RECORD] 交易已保存到performance_data.json: {symbol} {decision['action']}")
            except Exception as e:
                self.logger.error(f"[ERROR] 保存交易到performance_data.json失败: {e}")

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

        双模型协同机制：
        - Chat模型：每120秒分析，快速响应市场变化
        - Reasoner模型：每300秒深度分析，重大决策时刻

        推理模型使用场景（优先级从高到低）：
        1. 时间触发：每300秒执行一次深度分析
        2. 开仓决策（新仓位）
        3. 重大市场变化（24h波动>5%）
        4. 连续亏损后（近3笔全亏）

        Args:
            symbol: 交易对
            market_data: 市场数据
            account_info: 账户信息

        Returns:
            True表示使用推理模型，False使用日常模型
        """
        current_time = time.time()

        # 条件0：时间触发 - 每300秒执行一次Reasoner深度分析
        if current_time - self.last_reasoner_time >= self.reasoner_interval:
            self.last_reasoner_time = current_time
            self.logger.info(f"[{symbol}] [定时] 10分钟深度分析 - 使用 DeepSeek Chat V3.1")
            return True

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
            # 开仓决策也更新Reasoner时间戳，避免重复深度分析
            self.last_reasoner_time = current_time
            self.logger.info(f"[{symbol}] [开仓决策] 深度分析 - 使用 DeepSeek Chat V3.1")
            return True
        
        # 条件2：重大市场变化（24h波动>5%）
        price_change_24h = abs(market_data.get('price_change_24h', 0))
        if price_change_24h > 5:
            self.logger.info(f"[{symbol}] [重大市场变化 {price_change_24h:.1f}%] 深度分析 - 使用 DeepSeek Chat V3.1")
            return True
        
        # 条件3：连续亏损（近3笔全亏）
        if len(self.trade_history) >= 3:
            recent_3 = self.trade_history[-3:]
            all_loss = all(t.get('pnl', 0) < 0 for t in recent_3)
            if all_loss:
                self.logger.info(f"[{symbol}] [连续亏损] 深度分析 - 使用 DeepSeek Chat V3.1")
                return True
        
        # 条件4：账户回撤较大（>10%）
        initial_balance = account_info.get('initial_balance', 100)
        current_balance = account_info.get('balance', 100)
        drawdown_pct = ((initial_balance - current_balance) / initial_balance * 100) if initial_balance > 0 else 0
        if drawdown_pct > 10:
            self.logger.info(f"[{symbol}] [账户回撤 {drawdown_pct:.1f}%] 深度分析 - 使用 DeepSeek Chat V3.1")
            return True
        
        # 条件5：高胜率时可使用推理模型优化策略
        recent_win_rate = self._calculate_recent_win_rate(n=5)
        if recent_win_rate > 0.7:
            self.logger.info(f"[{symbol}] [高胜率 {recent_win_rate*100:.0f}%] 深度分析优化 - 使用 DeepSeek Chat V3.1")
            return True
        
        # 其他情况：快速分析（持仓评估、常规监控）
        self.logger.info(f"[{symbol}] [常规评估] 快速分析 - DeepSeek Chat V3.1")
        return False
