#!/usr/bin/env python3
"""
DeepSeek Ai Trade Bot
永不停机的 AI 驱动量化交易系统
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict
import signal

# 导入模块
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager
from ai_trading_engine import AITradingEngine
from performance_tracker import PerformanceTracker
from pro_log_formatter import ProTradingFormatter
from roll_tracker import RollTracker  # [NEW V2.0] ROLL状态追踪器
from advanced_position_manager import AdvancedPositionManager  # [NEW V2.0] 高级仓位管理


class AlphaArenaBot:
    """DeepSeek Ai Trade Bot"""

    def __init__(self):
        """初始化机器人"""
        # 设置日志
        self._setup_logging()

        # 加载配置
        self._load_config()

        # 初始化组件
        self._init_components()

        # 运行标志
        self.running = True

        # 账户信息显示时间控制（每120秒显示一次）
        self.last_account_display_time = 0
        self.account_display_interval = 120  # 秒

        # [NEW] 系统运行统计（每次重启后重新计数）
        self.start_time = datetime.now()
        self.total_invocations = 0  # AI调用总次数

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("[SYSTEM] DeepSeek Ai Trade Bot 初始化完成")

    def _setup_logging(self):
        """设置日志"""
        # 创建 logs 目录
        os.makedirs('logs', exist_ok=True)

        # 创建logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # 清除现有handlers

        # 文件日志handler（不带颜色）
        file_handler = logging.FileHandler(f'logs/alpha_arena_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # 控制台日志handler（专业交易终端格式）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ProTradingFormatter(compact=True)
        console_handler.setFormatter(console_formatter)

        # 添加handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _load_config(self):
        """加载配置"""
        from dotenv import load_dotenv
        load_dotenv()

        # Binance 配置
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_api_secret = os.getenv('BINANCE_API_SECRET')
        self.testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'

        # DeepSeek 配置
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')

        # 交易配置
        self.initial_capital = float(os.getenv('INITIAL_CAPITAL', 10000))
        self.max_position_pct = float(os.getenv('MAX_POSITION_PCT', 10))
        self.default_leverage = int(os.getenv('DEFAULT_LEVERAGE', 3))
        self.trading_interval = int(os.getenv('TRADING_INTERVAL_SECONDS', 300))

        # 交易对
        symbols_str = os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT')
        self.trading_symbols = [s.strip() for s in symbols_str.split(',')]

        self.logger.info(f"配置加载完成: {len(self.trading_symbols)} 个交易对")

    def _init_components(self):
        """初始化所有组件"""
        # Binance 客户端
        self.binance = BinanceClient(
            api_key=self.binance_api_key,
            api_secret=self.binance_api_secret,
            testnet=self.testnet
        )

        # [NEW] 从Binance API获取实际账户余额，替代配置文件中的初始资金
        try:
            actual_balance = self.binance.get_futures_usdt_balance()
            self.logger.info(f"[OK] 实际余额: ${actual_balance:,.2f}")
            # 使用实际余额替代配置文件值
            self.initial_capital = actual_balance
        except Exception as e:
            self.logger.warning(f"[WARNING] 无法获取Binance余额，使用配置文件值: {e}")
            # 回退到配置文件值
            pass

        # 市场分析器
        self.market_analyzer = MarketAnalyzer(self.binance)

        # 风险管理器
        risk_config = {
            'max_portfolio_risk': 0.02,
            'max_position_size': self.max_position_pct / 100,
            'max_leverage': 30,  # 统一为30倍，与AI决策范围一致
            'default_stop_loss_pct': 0.015,  # 1.5%止损，与交易策略一致
            'default_take_profit_pct': 0.05,  # 5%止盈
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_open_positions': 10,
            'max_daily_trades': 100
        }
        self.risk_manager = RiskManager(risk_config)

        # 性能追踪器（使用实际余额） - 必须在AI引擎之前初始化
        self.performance = PerformanceTracker(
            initial_capital=self.initial_capital,
            data_file='performance_data.json'
        )

        # AI 交易引擎
        self.ai_engine = AITradingEngine(
            deepseek_api_key=self.deepseek_api_key,
            binance_client=self.binance,
            market_analyzer=self.market_analyzer,
            risk_manager=self.risk_manager,
            performance_tracker=self.performance  # [FIX] 传入性能追踪器
        )

        # [NEW V2.0] ROLL状态追踪器
        self.roll_tracker = RollTracker(data_file='roll_state.json')

        # [NEW V2.0] 高级仓位管理器
        self.position_manager = AdvancedPositionManager(
            binance_client=self.binance,
            market_analyzer=self.market_analyzer
        )

    def _signal_handler(self, signum, frame):
        """信号处理器（优雅关闭）"""
        self.logger.info(f"\n收到信号 {signum}, 正在优雅关闭...")
        self.running = False

    def run_forever(self):
        """永久运行主循环"""
        self.logger.info("=" * 60)
        self.logger.info("[SUCCESS] DeepSeek Ai Trade Bot 启动")
        self.logger.info(f"[MONEY] 账户余额: ${self.initial_capital:,.2f}")
        self.logger.info(f"[ANALYZE] 交易对: {', '.join(self.trading_symbols)}")
        self.logger.info(f"[TIME]  交易间隔: {self.trading_interval}秒")
        self.logger.info(f"[AI] AI 模型: DeepSeek Chat V3.1")
        self.logger.info("=" * 60)

        cycle_count = 0

        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"[LOOP] 开始第 {cycle_count} 轮交易循环")
                self.logger.info(f"[TIME] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info(f"{'='*60}")

                # 1. 更新账户状态
                self._update_account_status()

                # 2. 对每个交易对进行分析和交易
                for symbol in self.trading_symbols:
                    self._process_symbol(symbol)

                    # 短暂延迟避免 API 限流
                    time.sleep(2)

                # 3. 显示性能摘要 (已禁用 - 用户要求去掉)
                # self._display_performance()

                # 4. 等待下一轮
                self.logger.info(f"\n[WAIT] 等待 {self.trading_interval} 秒后开始下一轮...")
                time.sleep(self.trading_interval)

            except KeyboardInterrupt:
                self.logger.info("\n[WARNING]  检测到键盘中断，正在关闭...")
                break

            except Exception as e:
                self.logger.error(f"[ERROR] 主循环错误: {e}")
                self.logger.error(f"[WAIT] 60秒后重试...")
                time.sleep(60)

        self._shutdown()

    def _update_account_status(self):
        """更新账户状态"""
        try:
            # 测量API延迟
            import time as time_module
            start_time = time_module.time()

            # 获取余额
            balance = self.binance.get_futures_usdt_balance()

            # 获取持仓
            positions = self.binance.get_active_positions()

            # 计算API延迟
            api_latency_ms = int((time_module.time() - start_time) * 1000)

            # 计算总价值
            unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)
            total_value = balance + unrealized_pnl

            # 更新性能追踪
            self.performance.update_portfolio_value(total_value)

            # 计算并显示指标
            metrics = self.performance.calculate_metrics(balance, positions)

            # 计算保证金使用率
            total_margin_used = 0
            for pos in positions:
                pos_amt = abs(float(pos.get('positionAmt', 0)))
                entry_price = float(pos.get('entryPrice', 0))
                leverage = float(pos.get('leverage', 1))
                if pos_amt > 0 and entry_price > 0:
                    notional = pos_amt * entry_price
                    margin = notional / leverage
                    total_margin_used += margin

            margin_usage_pct = (total_margin_used / balance * 100) if balance > 0 else 0

            # 计算平均杠杆倍数
            avg_leverage = 0
            if positions:
                leverages = [float(pos.get('leverage', 1)) for pos in positions if float(pos.get('positionAmt', 0)) != 0]
                avg_leverage = sum(leverages) / len(leverages) if leverages else 0

            # 计算盈亏比（如果有交易历史）
            if hasattr(self.performance, 'trades') and len(self.performance.trades) > 0:
                winning_trades = [t for t in self.performance.trades if t.get('pnl', 0) > 0]
                losing_trades = [t for t in self.performance.trades if t.get('pnl', 0) < 0]

                avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
                avg_loss = abs(sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)) if losing_trades else 1

                profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            else:
                profit_factor = 0

            # 检查是否需要显示账户信息（每120秒显示一次）
            current_time = time.time()
            should_display = (current_time - self.last_account_display_time) >= self.account_display_interval

            if should_display:
                # 显示增强的账户信息
                self.logger.info(f"\n[ACCOUNT] 账户状态:")
                if avg_leverage > 0:
                    self.logger.info(f"  余额: ${balance:,.2f}  |  持仓数: {len(positions)}  |  杠杆: {avg_leverage:.0f}x  |  保证金使用: {margin_usage_pct:.1f}%")
                else:
                    self.logger.info(f"  余额: ${balance:,.2f}  |  持仓数: {len(positions)}  |  保证金使用: {margin_usage_pct:.1f}%")
                self.logger.info(f"  未实现盈亏: ${unrealized_pnl:,.2f}  |  总价值: ${total_value:,.2f}  |  总收益率: {metrics['total_return_pct']:+.2f}%")

                # 显示性能指标
                if profit_factor > 0:
                    self.logger.info(f"  [PERF] 盈亏比: {profit_factor:.2f}  |  最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%  |  胜率: {metrics.get('win_rate', 0):.1f}%")

                # [NEW] 清算价预警检查
                if positions:
                    liquidation_warnings = self.risk_manager.check_liquidation_risk(
                        positions,
                        liquidation_threshold=0.03  # 3% 预警阈值
                    )

                    if liquidation_warnings:
                        self.logger.warning(f"\n[WARNING]  检测到 {len(liquidation_warnings)} 个清算风险预警:")
                        for warning in liquidation_warnings:
                            self.logger.warning(f"  {warning['message']}")
                            self.logger.warning(
                                f"    当前价: ${warning['current_price']:,.2f} | "
                                f"清算价: ${warning['liquidation_price']:,.2f} | "
                                f"距离: {warning['distance_pct']:.2f}%"
                            )

                # 更新显示时间
                self.last_account_display_time = current_time

        except Exception as e:
            self.logger.error(f"更新账户状态失败: {e}")

    def _process_symbol(self, symbol: str):
        """
        处理单个交易对

        Args:
            symbol: 交易对
        """
        try:
            # 获取实时市场数据
            import time as time_module
            start_time = time_module.time()

            # 获取当前价格和24h数据
            try:
                ticker = self.binance.get_futures_24h_ticker(symbol=symbol)
                current_price = float(ticker.get('lastPrice', 0))
                price_change_24h = float(ticker.get('priceChangePercent', 0))
                volume_24h = float(ticker.get('volume', 0))
                quote_volume_24h = float(ticker.get('quoteVolume', 0)) / 1_000_000  # 转换为百万

                # 计算API延迟
                market_data_latency_ms = int((time_module.time() - start_time) * 1000)

                # 显示市场数据
                self.logger.info(f"\n[ANALYZE] {symbol} 市场数据:")
                self.logger.info(
                    f"  价格: ${current_price:,.4f}  {price_change_24h:+.2f}%  |  "
                    f"24h成交: ${quote_volume_24h:.1f}M"
                )
            except Exception as e:
                self.logger.warning(f"  [WARNING] 获取市场数据失败: {e}")
                # 继续执行，使用基本分析

            # 检查是否已有持仓
            positions = self.binance.get_active_positions()
            existing_position = None
            for pos in positions:
                if pos['symbol'] == symbol and float(pos.get('positionAmt', 0)) != 0:
                    existing_position = pos
                    break

            if existing_position:
                # [OK] 新功能: 让AI评估是否应该平仓
                self.logger.info(f"  [SEARCH] {symbol} 已有持仓，让AI评估是否平仓...")

                # [NEW] 获取运行统计并传递给AI引擎
                runtime_stats = self.get_runtime_stats()

                result = self.ai_engine.analyze_position_for_closing(
                    symbol=symbol,
                    position=existing_position,
                    runtime_stats=runtime_stats
                )

                # [NEW] 递增AI调用计数
                self.total_invocations += 1

                if result['success']:
                    ai_decision = result.get('decision', {})
                    action = ai_decision.get('action', 'HOLD')

                    # 保存AI的持仓评估决策
                    self._save_ai_decision(symbol, ai_decision, result)

                    # [OK] 完全信任AI决策，不设置信心阈值
                    if action in ['CLOSE', 'CLOSE_LONG', 'CLOSE_SHORT']:
                        self.logger.info(f"  ✂️  AI决定平仓 {symbol}")
                        self.logger.info(f"  [IDEA] 理由: {ai_decision.get('reasoning', '')}")
                        self.logger.info(f"  [TARGET] 信心度: {ai_decision.get('confidence', 0)}%")

                        # 获取当前市场价格（平仓价）
                        try:
                            close_price = self.market_analyzer.get_current_price(symbol)
                        except Exception:
                            close_price = float(existing_position.get('markPrice', 0))

                        # 执行平仓
                        close_result = self.binance.close_position(symbol)

                        # 记录平仓并计算盈亏
                        pnl = self.performance.record_trade_close(
                            symbol=symbol,
                            close_price=close_price,
                            position_info=existing_position
                        )

                        # 记录平仓交易（带盈亏信息）
                        self.performance.record_trade({
                            'symbol': symbol,
                            'action': 'CLOSE',
                            'entry_price': float(existing_position.get('entryPrice', 0)),
                            'price': close_price,
                            'quantity': abs(float(existing_position.get('positionAmt', 0))),
                            'leverage': int(existing_position.get('leverage', 1)),
                            'confidence': ai_decision.get('confidence', 0),
                            'reasoning': ai_decision.get('reasoning', ''),
                            'pnl': pnl
                        })

                        if pnl > 0:
                            self.logger.info(f"  [OK] 平仓成功 - 盈利 ${pnl:.2f}")
                        else:
                            self.logger.info(f"  [OK] 平仓成功 - 亏损 ${pnl:.2f}")

                    elif action == 'ROLL':
                        # [NEW] 执行浮盈滚仓策略
                        self.logger.info(f"  🔄 AI决定执行滚仓策略 {symbol}")
                        self.logger.info(f"  [IDEA] 理由: {ai_decision.get('reasoning', '')}")
                        self.logger.info(f"  [TARGET] 信心度: {ai_decision.get('confidence', 0)}%")

                        roll_result = self.execute_roll_strategy(
                            symbol=symbol,
                            position=existing_position,
                            decision=ai_decision
                        )

                        if roll_result['success']:
                            self.logger.info(f"  [SUCCESS] 滚仓策略执行成功")
                        else:
                            self.logger.warning(f"  [WARNING] 滚仓策略执行失败: {roll_result.get('reason', '未知原因')}")

                    else:
                        self.logger.info(f"  [OK] AI建议继续持有 {symbol} (信心度: {ai_decision.get('confidence', 0)}%)")
                        self.logger.info(f"  [IDEA] 理由: {ai_decision.get('reasoning', '')}")
                else:
                    self.logger.error(f"  [ERROR] 持仓评估失败: {result.get('error')}")

                return  # 处理完持仓后返回

            # AI 分析和交易（仅在无持仓时）
            # [NEW] 获取运行统计并传递给AI引擎
            runtime_stats = self.get_runtime_stats()

            result = self.ai_engine.analyze_and_trade(
                symbol=symbol,
                max_position_pct=self.max_position_pct,
                runtime_stats=runtime_stats
            )

            # [NEW] 递增AI调用计数
            self.total_invocations += 1

            if result['success']:
                action = result.get('trade_result', {}).get('action', 'HOLD')
                ai_decision = result.get('ai_decision', {})

                # 保存所有AI决策（包括HOLD）到文件供仪表板显示
                self._save_ai_decision(symbol, ai_decision, result.get('trade_result', {}))

                # 获取AI的叙述性决策说明（优先使用narrative，其次reasoning）
                narrative = ai_decision.get('narrative', ai_decision.get('reasoning', ''))

                if action in ['BUY', 'SELL', 'OPEN_LONG', 'OPEN_SHORT']:
                    # 记录交易
                    trade_info = result['trade_result']
                    trade_info['confidence'] = ai_decision.get('confidence', 0)
                    trade_info['reasoning'] = ai_decision.get('reasoning', '')

                    self.performance.record_trade(trade_info)

                    self.logger.info(f"\n[AI] DEEPSEEK CHAT V3.1 决策:")
                    self.logger.info(f"  {narrative}")
                else:
                    # HOLD决策 - 显示叙述性说明
                    self.logger.info(f"\n[AI] DEEPSEEK CHAT V3.1 决策:")
                    self.logger.info(f"  {narrative}")

            else:
                self.logger.error(f"  [ERROR] 交易失败: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"处理 {symbol} 失败: {e}")

    def _save_ai_decision(self, symbol: str, decision: dict, trade_result: dict):
        """保存增强的AI决策卡片到文件"""
        import json
        try:
            # 读取现有决策
            try:
                with open('ai_decisions.json', 'r') as f:
                    decisions = json.load(f)
            except FileNotFoundError:
                decisions = []

            # 获取当前账户状态
            try:
                balance = self.binance.get_futures_usdt_balance()
                positions = self.binance.get_active_positions()
                unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)
                total_value = balance + unrealized_pnl
                metrics = self.performance.calculate_metrics(balance, positions)
            except Exception:
                balance = 0
                total_value = 0
                metrics = {'total_return_pct': 0}
                positions = []

            # 获取交易时段信息
            from deepseek_client import DeepSeekClient
            temp_client = DeepSeekClient(self.deepseek_api_key)
            session_info = temp_client.get_trading_session()

            # 构建增强的决策记录
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'cycle': len(decisions) + 1,

                # [ANALYZE] 账户快照
                'account_snapshot': {
                    'total_value': round(total_value, 2),
                    'cash_balance': round(balance, 2),
                    'total_return_pct': round(metrics.get('total_return_pct', 0), 2),
                    'positions_count': len(positions),
                    'unrealized_pnl': round(unrealized_pnl, 2)
                },

                # [TARGET] 本次决策详情
                'decision': {
                    'symbol': symbol,
                    'action': decision.get('action', 'HOLD'),
                    'confidence': decision.get('confidence', 0),
                    'reasoning': decision.get('reasoning', ''),
                    'leverage': decision.get('leverage', 3),
                    'position_size': decision.get('position_size', 5),
                    'stop_loss_pct': decision.get('stop_loss_pct', 1.5),
                    'take_profit_pct': decision.get('take_profit_pct', 5),
                    'executed': trade_result.get('success', False),
                    'error': trade_result.get('error', None)
                },

                # [TIMER] 交易时段
                'session_info': {
                    'session': session_info['session'],
                    'volatility': session_info['volatility'],
                    'recommendation': session_info['recommendation'],
                    'aggressive_mode': session_info['aggressive_mode']
                },

                # [ACCOUNT] 持仓快照（如果是持仓决策）
                'position_snapshot': None
            }

            # 如果是持仓评估，添加持仓详情
            if decision.get('action') in ['HOLD', 'CLOSE']:
                for pos in positions:
                    if pos['symbol'] == symbol:
                        entry_price = float(pos.get('entryPrice', 0))
                        current_price = float(pos.get('markPrice', 0))
                        pnl_pct = ((current_price - entry_price) / entry_price * 100 *
                                  (-1 if float(pos.get('positionAmt', 0)) < 0 else 1))

                        decision_record['position_snapshot'] = {
                            'direction': 'SHORT' if float(pos.get('positionAmt', 0)) < 0 else 'LONG',
                            'quantity': abs(float(pos.get('positionAmt', 0))),
                            'leverage': int(pos.get('leverage', 1)),
                            'entry_price': entry_price,
                            'current_price': current_price,
                            'unrealized_pnl': float(pos.get('unRealizedProfit', 0)),
                            'unrealized_pnl_pct': round(pnl_pct, 2)
                        }
                        break

            decisions.append(decision_record)

            # 只保留最近200条决策
            decisions = decisions[-200:]

            # 保存
            with open('ai_decisions.json', 'w') as f:
                json.dump(decisions, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存AI决策失败: {e}")

    def _display_performance(self):
        """显示性能摘要"""
        try:
            summary = self.performance.get_performance_summary()
            print(summary)
        except Exception as e:
            self.logger.error(f"显示性能摘要失败: {e}")

    def get_runtime_stats(self) -> dict:
        """
        获取系统运行统计信息

        Returns:
            包含运行时长和AI调用次数的字典
        """
        runtime_delta = datetime.now() - self.start_time
        runtime_minutes = int(runtime_delta.total_seconds() / 60)

        return {
            'start_time': self.start_time.isoformat(),
            'current_time': datetime.now().isoformat(),
            'runtime_minutes': runtime_minutes,
            'total_invocations': self.total_invocations
        }

    def execute_roll_strategy(self, symbol: str, position: Dict, decision: Dict) -> Dict:
        """
        执行浮盈滚仓策略 V2.0（增强版：6次限制+手续费+自动止损）

        Args:
            symbol: 交易对
            position: 当前持仓信息
            decision: AI决策信息（包含leverage、reinvest_pct等）

        Returns:
            执行结果
        """
        try:
            self.logger.info(f"\n🔄 [ROLL V2.0] 开始执行浮盈直接加仓策略: {symbol}")

            # [NEW V2.0] 0. 检查ROLL次数限制（最多6次）
            can_roll, reason, current_count = self.roll_tracker.can_roll(symbol)
            if not can_roll:
                self.logger.error(f"  ❌ [LIMIT] {reason}")
                self.logger.info(f"  💡 建议: 已达到6次ROLL上限，应该止盈离场了")
                return {'success': False, 'reason': reason}

            self.logger.info(f"  ✅ [CHECK] ROLL次数检查通过（当前{current_count}次，还剩{6-current_count}次机会）")

            # 1. 验证当前浮盈是否达到阈值
            unrealized_pnl = float(position.get('unRealizedProfit', 0))
            account_balance = self.binance.get_futures_usdt_balance()
            account_value = account_balance + unrealized_pnl

            profit_ratio = (unrealized_pnl / account_value) * 100 if account_value > 0 else 0
            threshold_pct = decision.get('profit_threshold_pct', 6.0)

            self.logger.info(f"  [DATA] 账户总价值: ${account_value:.2f}")
            self.logger.info(f"  [DATA] 未实现盈亏: ${unrealized_pnl:.2f}")
            self.logger.info(f"  [DATA] 浮盈比例: {profit_ratio:.2f}% (阈值: {threshold_pct:.2f}%)")

            if profit_ratio < threshold_pct:
                self.logger.warning(f"  [WARNING] 浮盈未达到阈值，不执行滚仓")
                return {
                    'success': False,
                    'reason': f'浮盈比例{profit_ratio:.2f}%未达到阈值{threshold_pct:.2f}%'
                }

            if unrealized_pnl <= 0:
                self.logger.warning(f"  [WARNING] 浮盈为负或零，不执行滚仓")
                return {'success': False, 'reason': '浮盈为负或零'}

            # [NEW V2.0] 2. 扣除手续费后计算净浮盈
            BINANCE_TAKER_FEE = 0.0005  # Binance taker手续费0.05%
            fee_amount = unrealized_pnl * BINANCE_TAKER_FEE
            net_unrealized_pnl = unrealized_pnl - fee_amount

            self.logger.info(f"  [STEP 1] 保持原仓位继续盈利（不平仓）")
            self.logger.info(f"  [FEE] 扣除手续费: ${fee_amount:.2f} (0.05%)")
            self.logger.info(f"  [NET] 净浮盈: ${net_unrealized_pnl:.2f}")

            # 计算可用于加仓的浮盈金额
            reinvest_pct = decision.get('reinvest_pct', 60.0)
            reinvest_pct = max(50.0, min(70.0, reinvest_pct))

            reinvest_amount = net_unrealized_pnl * (reinvest_pct / 100.0)

            self.logger.info(f"  [STEP 2] 使用{reinvest_pct:.1f}%净浮盈加仓: ${reinvest_amount:.2f}")
            self.logger.info(f"  [DATA] 保留浮盈: ${net_unrealized_pnl - reinvest_amount:.2f}")

            # 3. 使用AI指定的杠杆开新仓位
            new_leverage = decision.get('leverage', 10)
            new_leverage = max(1, min(30, new_leverage))

            # 获取当前价格
            current_price = self.market_analyzer.get_current_price(symbol)

            # 计算开仓数量（考虑杠杆）
            position_quantity = (reinvest_amount * new_leverage) / current_price

            # 币安最小开仓量检查
            min_quantity = 0.001
            if position_quantity < min_quantity:
                self.logger.warning(f"  [WARNING] 开仓数量{position_quantity:.6f}小于最小量{min_quantity}，调整至最小量")
                position_quantity = min_quantity

            self.logger.info(f"  [STEP 3] 用浮盈开新仓位（原仓位保持）...")
            self.logger.info(f"  [DATA] 新仓杠杆: {new_leverage}x")
            self.logger.info(f"  [DATA] 新仓数量: {position_quantity:.6f}")
            self.logger.info(f"  [DATA] 当前价格: ${current_price:.2f}")

            # 设置杠杆
            self.binance.set_leverage(symbol, new_leverage)

            # 根据原持仓方向决定新仓位方向（保持同方向）
            position_side = float(position.get('positionAmt', 0))
            side = 'LONG' if position_side > 0 else 'SHORT'
            entry_price = float(position.get('entryPrice', current_price))

            # [NEW V2.0] 如果是第一次ROLL，初始化tracker
            if current_count == 0:
                self.roll_tracker.initialize_position(
                    symbol=symbol,
                    entry_price=entry_price,
                    position_amt=position_side,
                    side=side
                )

            # 开仓
            if side == 'LONG':
                open_result = self.binance.open_long(symbol, position_quantity, new_leverage)
            else:
                open_result = self.binance.open_short(symbol, position_quantity, new_leverage)

            if open_result:
                self.logger.info(f"  [OK] 新仓位加仓成功")

                # [NEW V2.0] 记录ROLL到tracker
                new_count = self.roll_tracker.increment_roll_count(symbol, {
                    'current_price': current_price,
                    'unrealized_pnl': unrealized_pnl,
                    'profit_pct': profit_ratio,
                    'reinvest_amount': reinvest_amount,
                    'new_position_qty': position_quantity,
                    'leverage': new_leverage
                })

                # [NEW V2.0] STEP 4: 自动移动止损到盈亏平衡
                self.logger.info(f"  [STEP 4] 自动移动止损保护利润...")
                original_entry = self.roll_tracker.get_original_entry_price(symbol)
                if original_entry:
                    move_result = self.position_manager.move_stop_to_breakeven(
                        symbol=symbol,
                        entry_price=original_entry,
                        profit_trigger_pct=0.0,  # 立即执行，不检查盈利触发
                        breakeven_offset_pct=0.2  # 成本价+0.2%（含手续费）
                    )
                    if move_result.get('success'):
                        self.logger.info(f"  ✅ [STOP] 止损已移至盈亏平衡点: ${move_result.get('new_stop_price'):.2f}")
                    else:
                        self.logger.warning(f"  ⚠️ [STOP] 止损移动跳过: {move_result.get('error')}")

                # 记录加仓交易
                self.performance.record_trade({
                    'symbol': symbol,
                    'action': f'ROLL_ADD_{side}',
                    'entry_price': current_price,
                    'price': current_price,
                    'quantity': position_quantity,
                    'leverage': new_leverage,
                    'confidence': decision.get('confidence', 0),
                    'reasoning': f"[ROLL #{new_count}] 浮盈{profit_ratio:.1f}%，用${reinvest_amount:.2f}加仓（扣费后净额）",
                    'pnl': None
                })

                self.logger.info(f"  🚀 [SUCCESS] 第{new_count}次ROLL完成！（还剩{6-new_count}次机会）")
                self.logger.info(f"  ✅ 原仓位: 继续持有，止损已保护")
                self.logger.info(f"  ✅ 新仓位: 投入${reinvest_amount:.2f} @ {new_leverage}x杠杆")
                self.logger.info(f"  ✅ 保留浮盈: ${net_unrealized_pnl - reinvest_amount:.2f}")
                self.logger.info(f"  💎 复利效应: 原仓+新仓双重盈利增长！")

                return {
                    'success': True,
                    'unrealized_profit': unrealized_pnl,
                    'net_profit_after_fee': net_unrealized_pnl,
                    'fee_amount': fee_amount,
                    'reinvest_amount': reinvest_amount,
                    'new_leverage': new_leverage,
                    'new_position_quantity': position_quantity,
                    'roll_count': new_count,
                    'roll_type': 'ADD'
                }
            else:
                self.logger.error(f"  [ERROR] 新仓位加仓失败")
                return {'success': False, 'reason': '新仓位加仓失败'}

        except Exception as e:
            self.logger.error(f"  [ERROR] 滚仓执行失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {'success': False, 'reason': str(e)}

    def _shutdown(self):
        """关闭机器人"""
        self.logger.info("\n🛑 DeepSeek Ai Trade Bot 正在关闭...")

        try:
            # 显示最终表现
            self._display_performance()

            # 保存数据
            self.logger.info("💾 保存数据...")

            self.logger.info("[OK] 关闭完成")

        except Exception as e:
            self.logger.error(f"关闭过程出错: {e}")


def main():
    """主函数"""
    # 创建并运行机器人
    bot = AlphaArenaBot()

    # DeepSeek 专属品牌色
    deepseek_blue = '\033[38;2;41;148;255m'
    reset = '\033[0m'
    bold = '\033[1m'

    print(f"""
{bold}{deepseek_blue}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ██████╗ ███████╗███████╗██████╗ ███████╗███████╗██╗  ██╗
║   ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██║ ██╔╝
║   ██║  ██║█████╗  █████╗  ██████╔╝███████╗█████╗  █████╔╝
║   ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ╚════██║██╔══╝  ██╔═██╗
║   ██████╔╝███████╗███████╗██║     ███████║███████╗██║  ██╗
║   ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝
║                                                          ║
║        ████████╗██████╗  █████╗ ██████╗ ███████╗
║        ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝
║           ██║   ██████╔╝███████║██║  ██║█████╗
║           ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝
║           ██║   ██║  ██║██║  ██║██████╔╝███████╗
║           ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝
║                                                          ║
║        █████╗  ██████╗ ███████╗███╗   ██╗████████╗
║       ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
║       ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
║       ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
║       ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
║       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
║                                                          ║
║            AI-Powered Trading System v3.1               ║
║        Inspired by nof1.ai Alpha Arena Experiment       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
{reset}
""")

    try:
        bot.run_forever()
    except Exception as e:
        logging.error(f"致命错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
