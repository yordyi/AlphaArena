"""
浮盈滚仓管理器 - 超短线策略
盈利时按比例加仓,放大收益
"""

import logging
from typing import Dict, Optional, List


class RollingPositionManager:
    """浮盈滚仓管理器"""

    def __init__(self,
                 profit_threshold_pct: float = 3.0,  # 盈利>3%时触发滚仓
                 roll_ratio: float = 0.5,  # 每次加仓比例(现有仓位的50%)
                 max_rolls: int = 2,  # 最多滚仓次数
                 min_roll_interval_minutes: int = 5):  # 最小滚仓间隔
        """
        初始化滚仓管理器

        Args:
            profit_threshold_pct: 触发滚仓的盈利阈值(%)
            roll_ratio: 每次加仓比例(0-1)
            max_rolls: 最大滚仓次数
            min_roll_interval_minutes: 最小滚仓间隔(分钟)
        """
        self.profit_threshold_pct = profit_threshold_pct
        self.roll_ratio = roll_ratio
        self.max_rolls = max_rolls
        self.min_roll_interval_minutes = min_roll_interval_minutes

        # 滚仓记录: {symbol: [roll1_time, roll2_time, ...]}
        self.roll_history: Dict[str, List[float]] = {}

        self.logger = logging.getLogger(__name__)

    def should_roll_position(self, position: Dict) -> tuple[bool, str, float]:
        """
        判断是否应该滚仓

        Args:
            position: 持仓信息,包含:
                - symbol: 交易对
                - pnl_pct: 盈亏百分比
                - quantity: 当前持仓数量
                - entry_price: 开仓价
                - side: LONG/SHORT

        Returns:
            (should_roll, reason, roll_quantity)
        """
        symbol = position['symbol']
        pnl_pct = position.get('pnl_pct', 0)
        quantity = position.get('quantity', 0)

        # 检查1: 是否盈利达到阈值
        if pnl_pct < self.profit_threshold_pct:
            return False, f"盈利未达到滚仓阈值({pnl_pct:.2f}% < {self.profit_threshold_pct}%)", 0

        # 检查2: 是否已达最大滚仓次数
        roll_count = len(self.roll_history.get(symbol, []))
        if roll_count >= self.max_rolls:
            return False, f"已达最大滚仓次数({roll_count}/{self.max_rolls})", 0

        # 检查3: 距离上次滚仓是否满足时间间隔
        import time
        if symbol in self.roll_history and self.roll_history[symbol]:
            last_roll_time = self.roll_history[symbol][-1]
            time_since_last_roll = (time.time() - last_roll_time) / 60  # 转换为分钟
            if time_since_last_roll < self.min_roll_interval_minutes:
                return False, f"距离上次滚仓时间过短({time_since_last_roll:.1f}分钟)", 0

        # 计算加仓数量
        roll_quantity = abs(quantity) * self.roll_ratio

        self.logger.info(f"✅ [{symbol}] 滚仓条件满足:")
        self.logger.info(f"   当前盈利: {pnl_pct:.2f}%")
        self.logger.info(f"   当前仓位: {quantity}")
        self.logger.info(f"   建议加仓: {roll_quantity:.4f}")
        self.logger.info(f"   已滚仓次数: {roll_count}/{self.max_rolls}")

        return True, f"盈利{pnl_pct:.2f}%,触发滚仓", roll_quantity

    def record_roll(self, symbol: str):
        """记录滚仓操作"""
        import time
        if symbol not in self.roll_history:
            self.roll_history[symbol] = []
        self.roll_history[symbol].append(time.time())
        self.logger.info(f"📝 记录滚仓: {symbol}, 第{len(self.roll_history[symbol])}次")

    def clear_roll_history(self, symbol: str):
        """清除滚仓历史(平仓时调用)"""
        if symbol in self.roll_history:
            del self.roll_history[symbol]
            self.logger.info(f"🧹 清除滚仓历史: {symbol}")

    def get_roll_info(self, symbol: str) -> Dict:
        """获取滚仓信息"""
        roll_count = len(self.roll_history.get(symbol, []))
        return {
            'symbol': symbol,
            'roll_count': roll_count,
            'max_rolls': self.max_rolls,
            'remaining_rolls': self.max_rolls - roll_count,
            'can_roll_more': roll_count < self.max_rolls
        }

    def calculate_dynamic_stop_loss(self,
                                    position: Dict,
                                    atr: float,
                                    base_stop_loss_pct: float = 2.0) -> float:
        """
        计算动态止损价格

        Args:
            position: 持仓信息
            atr: 平均真实波幅
            base_stop_loss_pct: 基础止损百分比

        Returns:
            止损价格
        """
        entry_price = position['entry_price']
        side = position['side']
        pnl_pct = position.get('pnl_pct', 0)

        # 如果已经盈利,使用移动止损
        if pnl_pct > 0:
            # 移动止损: 保护已有盈利的50%
            protected_profit_pct = pnl_pct * 0.5
            if side == 'LONG':
                stop_loss = entry_price * (1 + protected_profit_pct / 100)
            else:  # SHORT
                stop_loss = entry_price * (1 - protected_profit_pct / 100)

            self.logger.info(f"📊 移动止损: 保护{protected_profit_pct:.2f}%盈利")
        else:
            # 基于ATR的动态止损
            # ATR止损: 2倍ATR或基础止损百分比,取较宽者
            atr_based_pct = (atr / entry_price) * 200  # 2倍ATR
            final_stop_pct = max(atr_based_pct, base_stop_loss_pct)

            if side == 'LONG':
                stop_loss = entry_price * (1 - final_stop_pct / 100)
            else:  # SHORT
                stop_loss = entry_price * (1 + final_stop_pct / 100)

            self.logger.info(f"📊 动态止损: {final_stop_pct:.2f}% (ATR: {atr:.4f})")

        return stop_loss

    def calculate_dynamic_take_profit(self,
                                     position: Dict,
                                     atr: float,
                                     base_take_profit_pct: float = 5.0) -> float:
        """
        计算动态止盈价格

        Args:
            position: 持仓信息
            atr: 平均真实波幅
            base_take_profit_pct: 基础止盈百分比

        Returns:
            止盈价格
        """
        entry_price = position['entry_price']
        side = position['side']
        roll_count = len(self.roll_history.get(position['symbol'], []))

        # 如果已经滚仓,提高止盈目标
        # 滚仓1次: +2%, 滚仓2次: +4%
        adjusted_take_profit_pct = base_take_profit_pct + (roll_count * 2)

        # 基于ATR的动态止盈
        atr_based_pct = (atr / entry_price) * 300  # 3倍ATR
        final_take_profit_pct = max(atr_based_pct, adjusted_take_profit_pct)

        if side == 'LONG':
            take_profit = entry_price * (1 + final_take_profit_pct / 100)
        else:  # SHORT
            take_profit = entry_price * (1 - final_take_profit_pct / 100)

        self.logger.info(f"📊 动态止盈: {final_take_profit_pct:.2f}% (滚仓{roll_count}次)")

        return take_profit
