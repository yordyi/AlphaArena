"""
Alpha Arena 性能追踪系统
追踪所有交易指标，类似 nof1.ai 的 SharpeBench
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
import logging


class PerformanceTracker:
    """性能追踪器"""

    def __init__(self, initial_capital: float = 10000.0, data_file: str = 'performance_data.json'):
        """
        初始化性能追踪器

        Args:
            initial_capital: 初始资金
            data_file: 数据存储文件
        """
        self.initial_capital = initial_capital
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)

        # 加载或初始化数据
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载历史数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载数据失败: {e}")

        # 初始化数据结构
        return {
            'start_time': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'trades': [],
            'daily_snapshots': [],
            'portfolio_values': [],
            'metrics': {}
        }

    def _save_data(self):
        """保存数据"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    def record_trade(self, trade: Dict):
        """
        记录交易

        Args:
            trade: 交易信息
        """
        trade_record = {
            'time': datetime.now().isoformat(),
            'symbol': trade.get('symbol'),
            'action': trade.get('action'),
            'quantity': trade.get('quantity'),
            'price': trade.get('entry_price') or trade.get('price'),
            'leverage': trade.get('leverage', 1),
            'stop_loss': trade.get('stop_loss'),
            'take_profit': trade.get('take_profit'),
            'confidence': trade.get('confidence', 0),
            'reasoning': trade.get('reasoning', ''),
            'pnl': trade.get('pnl')  # 记录盈亏（如果有）
        }

        self.data['trades'].append(trade_record)
        self._save_data()

    def record_trade_close(self, symbol: str, close_price: float, position_info: Dict):
        """
        记录平仓并计算盈亏

        Args:
            symbol: 交易对
            close_price: 平仓价格
            position_info: 持仓信息（包含入场价、方向、数量、杠杆等）
        """
        # 查找对应的开仓记录
        trades = self.data['trades']
        entry_trade = None

        for trade in reversed(trades):
            if (trade['symbol'] == symbol and
                trade['action'] in ['OPEN_LONG', 'OPEN_SHORT'] and
                trade.get('pnl') is None):  # 找到未平仓的记录
                entry_trade = trade
                break

        if entry_trade:
            # 计算实际盈亏
            entry_price = entry_trade['price']
            quantity = entry_trade['quantity']
            leverage = entry_trade['leverage']

            if entry_trade['action'] in ['OPEN_LONG', 'BUY']:
                price_diff = close_price - entry_price
            else:  # OPEN_SHORT, SELL
                price_diff = entry_price - close_price

            # 计算盈亏（考虑杠杆）
            pnl = price_diff * quantity * leverage

            # 更新开仓记录的pnl
            entry_trade['pnl'] = round(pnl, 2)
            entry_trade['close_price'] = close_price
            entry_trade['close_time'] = datetime.now().isoformat()

            self._save_data()
            self.logger.info(f"记录平仓: {symbol}, 盈亏: ${pnl:.2f}")

            return pnl
        else:
            self.logger.warning(f"未找到{symbol}的开仓记录")
            return 0

    def update_portfolio_value(self, current_value: float):
        """
        更新组合价值

        Args:
            current_value: 当前总价值
        """
        snapshot = {
            'time': datetime.now().isoformat(),
            'value': current_value,
            'return_pct': ((current_value - self.initial_capital) / self.initial_capital) * 100
        }

        self.data['portfolio_values'].append(snapshot)

        # 只保留最近 10000 个数据点
        if len(self.data['portfolio_values']) > 10000:
            self.data['portfolio_values'] = self.data['portfolio_values'][-10000:]

        self._save_data()

    def calculate_metrics(self, current_balance: float, positions: List[Dict]) -> Dict:
        """
        计算性能指标

        Args:
            current_balance: 当前余额
            positions: 当前持仓

        Returns:
            性能指标
        """
        # 计算未实现盈亏
        unrealized_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in positions)
        total_value = current_balance + unrealized_pnl

        # 计算累计总收益率（从最初投入算起）
        cumulative_return = ((total_value - self.initial_capital) / self.initial_capital) * 100

        # 计算当前持仓收益率（基于当前钱包余额）
        current_position_return = (unrealized_pnl / current_balance * 100) if current_balance > 0 else 0

        # 计算已实现盈亏
        realized_pnl = current_balance - self.initial_capital

        # 计算交易统计
        trades = self.data['trades']
        total_trades = len(trades)

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio()

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown()

        # 计算胜率（需要从已平仓交易中统计）
        win_rate = self._calculate_win_rate()

        # 更新指标
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'account_value': round(total_value, 2),
            'wallet_balance': round(current_balance, 2),

            # 累计总收益（包含已实现和未实现）
            'cumulative_return_pct': round(cumulative_return, 2),
            'cumulative_return_usd': round(total_value - self.initial_capital, 2),

            # 当前持仓收益（仅未实现盈亏）
            'current_position_return_pct': round(current_position_return, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),

            # 已实现盈亏
            'realized_pnl': round(realized_pnl, 2),
            'realized_return_pct': round((realized_pnl / self.initial_capital * 100), 2) if self.initial_capital > 0 else 0,

            # 保留旧字段以兼容
            'total_return_pct': round(current_position_return, 2),  # 改为显示当前持仓收益率
            'total_return_usd': round(unrealized_pnl, 2),  # 改为显示未实现盈亏

            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'win_rate_pct': round(win_rate, 2),
            'total_trades': total_trades,
            'open_positions': len(positions),
            'fees_paid': round(self._calculate_total_fees(), 2),
            'avg_trade_return': round(self._calculate_avg_trade_return(), 2),
            'daily_return': round(self._calculate_daily_return(), 2)
        }

        self.data['metrics'] = metrics
        self._save_data()

        return metrics

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """计算夏普比率"""
        try:
            values = [v['value'] for v in self.data['portfolio_values']]

            if len(values) < 2:
                return 0.0

            # 计算每日收益率
            returns = []
            for i in range(1, len(values)):
                daily_return = (values[i] - values[i-1]) / values[i-1]
                returns.append(daily_return)

            if len(returns) == 0:
                return 0.0

            # 计算年化夏普比率
            mean_return = np.mean(returns)
            std_return = np.std(returns)

            if std_return == 0:
                return 0.0

            # 假设每天都有数据，年化因子为 sqrt(365)
            sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(365)

            return sharpe

        except Exception as e:
            self.logger.error(f"计算夏普比率失败: {e}")
            return 0.0

    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        try:
            values = [v['value'] for v in self.data['portfolio_values']]

            if len(values) < 2:
                return 0.0

            peak = values[0]
            max_dd = 0.0

            for value in values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak * 100
                if dd > max_dd:
                    max_dd = dd

            return max_dd

        except Exception as e:
            self.logger.error(f"计算最大回撤失败: {e}")
            return 0.0

    def _calculate_win_rate(self) -> float:
        """
        计算胜率（基于已平仓交易的实际盈亏）
        使用记录的 pnl 字段，更准确地计算胜率
        """
        try:
            trades = self.data['trades']

            if len(trades) == 0:
                return 0.0

            # 统计所有有pnl记录的已平仓交易
            trades_with_pnl = [t for t in trades if t.get('pnl') is not None]

            if len(trades_with_pnl) == 0:
                return 0.0

            # 计算盈利和亏损交易数量
            wins = sum(1 for t in trades_with_pnl if t['pnl'] > 0)
            losses = sum(1 for t in trades_with_pnl if t['pnl'] <= 0)

            total = wins + losses
            if total == 0:
                return 0.0

            win_rate = (wins / total) * 100

            self.logger.info(f"胜率计算: {wins}胜/{losses}负, 总计{total}笔, 胜率{win_rate:.1f}%")

            return win_rate

        except Exception as e:
            self.logger.error(f"计算胜率失败: {e}")
            return 0.0

    def _calculate_total_fees(self) -> float:
        """
        计算总手续费（估算）
        币安期货手续费：Taker 0.04%, Maker 0.02%
        市价单按 Taker 计算
        """
        try:
            trades = self.data['trades']
            total_fees = 0.0

            # 市价单手续费率：0.04% (Taker)
            fee_rate = 0.0004

            for trade in trades:
                if trade.get('action') in ['BUY', 'SELL', 'OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'CLOSE_LONG', 'CLOSE_SHORT']:
                    price = trade.get('price', 0)
                    quantity = trade.get('quantity', 0)

                    # 计算名义价值（不考虑杠杆，因为手续费基于名义价值）
                    notional = price * quantity
                    total_fees += notional * fee_rate

            return total_fees

        except Exception as e:
            self.logger.error(f"计算手续费失败: {e}")
            return 0.0

    def _calculate_avg_trade_return(self) -> float:
        """
        计算平均每笔交易收益率
        基于已平仓交易的实际盈亏
        """
        try:
            trades = self.data['trades']

            # 只统计有盈亏记录的已平仓交易
            closed_trades = [t for t in trades if t.get('pnl') is not None]

            if len(closed_trades) == 0:
                return 0.0

            # 计算平均盈亏
            total_pnl = sum(t['pnl'] for t in closed_trades)
            avg_pnl = total_pnl / len(closed_trades)

            # 转换为百分比（相对于初始资金）
            avg_return_pct = (avg_pnl / self.initial_capital) * 100

            return avg_return_pct

        except Exception as e:
            self.logger.error(f"计算平均交易收益失败: {e}")
            return 0.0

    def _calculate_daily_return(self) -> float:
        """计算今日收益率"""
        try:
            values = self.data['portfolio_values']

            if len(values) < 2:
                return 0.0

            # 找到今天开始时的值
            now = datetime.now()
            today_start = datetime(now.year, now.month, now.day)

            today_values = [v for v in values if datetime.fromisoformat(v['time']) >= today_start]

            if len(today_values) < 2:
                return 0.0

            start_value = today_values[0]['value']
            current_value = today_values[-1]['value']

            return ((current_value - start_value) / start_value) * 100

        except Exception as e:
            self.logger.error(f"计算今日收益失败: {e}")
            return 0.0

    def get_leaderboard_stats(self) -> Dict:
        """获取排行榜统计数据（类似 Alpha Arena）"""
        metrics = self.data.get('metrics', {})

        return {
            'model': 'DeepSeek-V3',
            'account_value': metrics.get('account_value', self.initial_capital),
            'total_return_pct': metrics.get('total_return_pct', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
            'win_rate_pct': metrics.get('win_rate_pct', 0),
            'total_trades': metrics.get('total_trades', 0),
            'fees_paid': metrics.get('fees_paid', 0),
            'days_running': self._calculate_days_running()
        }

    def _calculate_days_running(self) -> int:
        """计算运行天数"""
        try:
            start_time = datetime.fromisoformat(self.data['start_time'])
            return (datetime.now() - start_time).days
        except Exception:
            return 0

    def get_performance_summary(self) -> str:
        """获取性能摘要（格式化字符串）"""
        stats = self.get_leaderboard_stats()

        return f"""
╔══════════════════════════════════════════════════════════╗
║         🏆 Alpha Arena - DeepSeek-V3 Performance         ║
╠══════════════════════════════════════════════════════════╣
║ Account Value:     ${stats['account_value']:,.2f}
║ Total Return:      {stats['total_return_pct']:+.2f}%
║ Sharpe Ratio:      {stats['sharpe_ratio']:.2f}
║ Max Drawdown:      {stats['max_drawdown_pct']:.2f}%
║ Win Rate:          {stats['win_rate_pct']:.2f}%
╠══════════════════════════════════════════════════════════╣
║ Total Trades:      {stats['total_trades']}
║ Fees Paid:         ${stats['fees_paid']:,.2f}
║ Days Running:      {stats['days_running']}
╚══════════════════════════════════════════════════════════╝
"""
