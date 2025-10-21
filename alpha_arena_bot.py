#!/usr/bin/env python3
"""
Alpha Arena 交易机器人
永不停机的 AI 驱动量化交易系统
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List
import signal

# 导入模块
from binance_client import BinanceClient
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager
from ai_trading_engine import AITradingEngine
from performance_tracker import PerformanceTracker


class AlphaArenaBot:
    """Alpha Arena 交易机器人"""

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

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("🚀 Alpha Arena Bot 初始化完成")

    def _setup_logging(self):
        """设置日志"""
        # 创建 logs 目录
        os.makedirs('logs', exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/alpha_arena_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

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

        # 市场分析器
        self.market_analyzer = MarketAnalyzer(self.binance)

        # 风险管理器
        risk_config = {
            'max_portfolio_risk': 0.02,
            'max_position_size': self.max_position_pct / 100,
            'max_leverage': 15,  # 降低到15倍（从原来的default_leverage）
            'default_stop_loss_pct': 0.03,  # 提高到3%（从2%），给予更大容忍空间
            'default_take_profit_pct': 0.09,  # 提高到9%（从4%），1:3盈亏比
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_open_positions': 10,
            'max_daily_trades': 100
        }
        self.risk_manager = RiskManager(risk_config)

        # AI 交易引擎
        self.ai_engine = AITradingEngine(
            deepseek_api_key=self.deepseek_api_key,
            binance_client=self.binance,
            market_analyzer=self.market_analyzer,
            risk_manager=self.risk_manager
        )

        # 性能追踪器
        self.performance = PerformanceTracker(
            initial_capital=self.initial_capital,
            data_file='performance_data.json'
        )

    def _signal_handler(self, signum, frame):
        """信号处理器（优雅关闭）"""
        self.logger.info(f"\n收到信号 {signum}, 正在优雅关闭...")
        self.running = False

    def run_forever(self):
        """永久运行主循环"""
        self.logger.info("=" * 60)
        self.logger.info("🏆 Alpha Arena Trading Bot 启动")
        self.logger.info(f"💰 初始资金: ${self.initial_capital:,.2f}")
        self.logger.info(f"📊 交易对: {', '.join(self.trading_symbols)}")
        self.logger.info(f"⏱️  交易间隔: {self.trading_interval}秒")
        self.logger.info(f"🤖 AI 模型: DeepSeek-V3")
        self.logger.info("=" * 60)

        cycle_count = 0

        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🔄 开始第 {cycle_count} 轮交易循环")
                self.logger.info(f"🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info(f"{'='*60}")

                # 1. 更新账户状态
                self._update_account_status()

                # 2. 对每个交易对进行分析和交易
                for symbol in self.trading_symbols:
                    self._process_symbol(symbol)

                    # 短暂延迟避免 API 限流
                    time.sleep(2)

                # 3. 显示性能摘要
                self._display_performance()

                # 4. 等待下一轮
                self.logger.info(f"\n⏳ 等待 {self.trading_interval} 秒后开始下一轮...")
                time.sleep(self.trading_interval)

            except KeyboardInterrupt:
                self.logger.info("\n⚠️  检测到键盘中断，正在关闭...")
                break

            except Exception as e:
                self.logger.error(f"❌ 主循环错误: {e}")
                self.logger.error(f"⏳ 60秒后重试...")
                time.sleep(60)

        self._shutdown()

    def _update_account_status(self):
        """更新账户状态"""
        try:
            # 获取余额
            balance = self.binance.get_futures_usdt_balance()

            # 获取持仓
            positions = self.binance.get_active_positions()

            # 计算总价值
            unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)
            total_value = balance + unrealized_pnl

            # 更新性能追踪
            self.performance.update_portfolio_value(total_value)

            # 计算并显示指标
            metrics = self.performance.calculate_metrics(balance, positions)

            self.logger.info(f"\n💼 账户状态:")
            self.logger.info(f"  余额: ${balance:,.2f}")
            self.logger.info(f"  持仓数: {len(positions)}")
            self.logger.info(f"  未实现盈亏: ${unrealized_pnl:,.2f}")
            self.logger.info(f"  总价值: ${total_value:,.2f}")
            self.logger.info(f"  总收益率: {metrics['total_return_pct']:+.2f}%")

        except Exception as e:
            self.logger.error(f"更新账户状态失败: {e}")

    def _process_symbol(self, symbol: str):
        """
        处理单个交易对

        Args:
            symbol: 交易对
        """
        try:
            self.logger.info(f"\n📊 分析 {symbol}...")

            # 检查是否已有持仓
            positions = self.binance.get_active_positions()
            existing_position = None
            for pos in positions:
                if pos['symbol'] == symbol and float(pos.get('positionAmt', 0)) != 0:
                    existing_position = pos
                    break

            if existing_position:
                # ✅ 新功能: 让AI评估是否应该平仓
                self.logger.info(f"  🔍 {symbol} 已有持仓，让AI评估是否平仓...")

                result = self.ai_engine.analyze_position_for_closing(
                    symbol=symbol,
                    position=existing_position
                )

                if result['success']:
                    ai_decision = result.get('decision', {})
                    action = ai_decision.get('action', 'HOLD')

                    # 保存AI的持仓评估决策
                    self._save_ai_decision(symbol, ai_decision, result)

                    # ✅ 完全信任AI决策，不设置信心阈值
                    if action == 'CLOSE':
                        self.logger.info(f"  ✂️  AI决定平仓 {symbol}")
                        self.logger.info(f"  💡 理由: {ai_decision.get('reasoning', '')}")
                        self.logger.info(f"  🎯 信心度: {ai_decision.get('confidence', 0)}%")

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
                            self.logger.info(f"  ✅ 平仓成功 - 盈利 ${pnl:.2f}")
                        else:
                            self.logger.info(f"  ✅ 平仓成功 - 亏损 ${pnl:.2f}")
                    else:
                        self.logger.info(f"  ✅ AI建议继续持有 {symbol} (信心度: {ai_decision.get('confidence', 0)}%)")
                        self.logger.info(f"  💡 理由: {ai_decision.get('reasoning', '')}")
                else:
                    self.logger.error(f"  ❌ 持仓评估失败: {result.get('error')}")

                return  # 处理完持仓后返回

            # AI 分析和交易（仅在无持仓时）
            result = self.ai_engine.analyze_and_trade(
                symbol=symbol,
                max_position_pct=self.max_position_pct
            )

            if result['success']:
                action = result.get('trade_result', {}).get('action', 'HOLD')
                ai_decision = result.get('ai_decision', {})

                # 保存所有AI决策（包括HOLD）到文件供仪表板显示
                self._save_ai_decision(symbol, ai_decision, result.get('trade_result', {}))

                if action in ['OPEN_LONG', 'OPEN_SHORT']:
                    # 记录交易
                    trade_info = result['trade_result']
                    trade_info['confidence'] = ai_decision.get('confidence', 0)
                    trade_info['reasoning'] = ai_decision.get('reasoning', '')

                    self.performance.record_trade(trade_info)

                    self.logger.info(f"  ✅ {action}: {symbol}")
                    self.logger.info(f"  💡 理由: {trade_info['reasoning']}")
                else:
                    self.logger.info(f"  ⏸️  {action}")

            else:
                self.logger.error(f"  ❌ 交易失败: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"处理 {symbol} 失败: {e}")

    def _save_ai_decision(self, symbol: str, decision: dict, trade_result: dict):
        """保存AI决策到文件"""
        import json
        try:
            # 读取现有决策
            try:
                with open('ai_decisions.json', 'r') as f:
                    decisions = json.load(f)
            except FileNotFoundError:
                decisions = []

            # 添加新决策（包含所有DeepSeek参数）
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': decision.get('action', 'HOLD'),
                'confidence': decision.get('confidence', 0),
                'reasoning': decision.get('reasoning', ''),
                'leverage': decision.get('leverage', 3),
                'position_size': decision.get('position_size', 5),
                'stop_loss_pct': decision.get('stop_loss_pct', 2),
                'take_profit_pct': decision.get('take_profit_pct', 4),
                'executed': trade_result.get('success', False),
                'error': trade_result.get('error', None)
            }

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

    def _shutdown(self):
        """关闭机器人"""
        self.logger.info("\n🛑 Alpha Arena Bot 正在关闭...")

        try:
            # 显示最终表现
            self._display_performance()

            # 保存数据
            self.logger.info("💾 保存数据...")

            self.logger.info("✅ 关闭完成")

        except Exception as e:
            self.logger.error(f"关闭过程出错: {e}")


def main():
    """主函数"""
    # 创建并运行机器人
    bot = AlphaArenaBot()

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         🏆 ALPHA ARENA - DeepSeek-V3 Trading Bot        ║
    ║                                                          ║
    ║      Inspired by nof1.ai's Alpha Arena Experiment       ║
    ║                                                          ║
    ║         永不停机的 AI 量化交易系统                         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    try:
        bot.run_forever()
    except Exception as e:
        logging.error(f"致命错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
