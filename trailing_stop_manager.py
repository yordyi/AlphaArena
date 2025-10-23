#!/usr/bin/env python3
"""
ATR动态追踪止损管理器
基于Average True Range (ATR)实现动态止损调整
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging


class TrailingStopManager:
    """ATR动态追踪止损管理器"""

    def __init__(self, atr_multiplier: float = 2.0):
        """
        初始化追踪止损管理器

        Args:
            atr_multiplier: ATR倍数，默认2.0倍（止损距离 = ATR * multiplier）
        """
        self.atr_multiplier = atr_multiplier
        self.trailing_stops = {}  # {symbol: stop_data}
        self.logger = logging.getLogger(__name__)

    def initialize_stop(self, symbol: str, side: str, entry_price: float,
                       atr: float, position_size: float) -> Dict:
        """
        为新持仓初始化追踪止损

        Args:
            symbol: 交易对
            side: 持仓方向 (LONG/SHORT)
            entry_price: 入场价格
            atr: 当前ATR值
            position_size: 持仓数量

        Returns:
            止损数据字典
        """
        # 计算初始止损价格
        stop_distance = atr * self.atr_multiplier

        if side == 'LONG':
            initial_stop = entry_price - stop_distance
            highest_price = entry_price  # 追踪最高价
        else:  # SHORT
            initial_stop = entry_price + stop_distance
            lowest_price = entry_price  # 追踪最低价

        stop_data = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'current_stop': initial_stop,
            'initial_stop': initial_stop,
            'atr': atr,
            'atr_multiplier': self.atr_multiplier,
            'position_size': position_size,
            'highest_price': highest_price if side == 'LONG' else None,
            'lowest_price': lowest_price if side == 'SHORT' else None,
            'last_update': datetime.now().isoformat(),
            'triggered': False
        }

        self.trailing_stops[symbol] = stop_data

        self.logger.info(
            f"初始化 {symbol} {side} 追踪止损: "
            f"入场=${entry_price:.2f}, 止损=${initial_stop:.2f}, "
            f"ATR={atr:.2f} (x{self.atr_multiplier})"
        )

        return stop_data

    def update_stop(self, symbol: str, current_price: float, atr: float) -> Optional[Dict]:
        """
        更新追踪止损位置

        Args:
            symbol: 交易对
            current_price: 当前价格
            atr: 当前ATR值

        Returns:
            更新后的止损数据，如果未初始化则返回None
        """
        if symbol not in self.trailing_stops:
            return None

        stop_data = self.trailing_stops[symbol]
        side = stop_data['side']
        old_stop = stop_data['current_stop']

        # 计算新的止损距离
        stop_distance = atr * self.atr_multiplier

        if side == 'LONG':
            # 多仓：价格上涨时提升止损
            if current_price > stop_data['highest_price']:
                stop_data['highest_price'] = current_price
                new_stop = current_price - stop_distance

                # 止损只能上移，不能下移
                if new_stop > old_stop:
                    stop_data['current_stop'] = new_stop
                    self.logger.info(
                        f"[TREND-UP] {symbol} LONG 止损上移: "
                        f"${old_stop:.2f} → ${new_stop:.2f} "
                        f"(当前价: ${current_price:.2f}, 盈利: {((current_price - stop_data['entry_price']) / stop_data['entry_price'] * 100):.2f}%)"
                    )
        else:  # SHORT
            # 空仓：价格下跌时下移止损
            if current_price < stop_data['lowest_price']:
                stop_data['lowest_price'] = current_price
                new_stop = current_price + stop_distance

                # 止损只能下移，不能上移
                if new_stop < old_stop:
                    stop_data['current_stop'] = new_stop
                    self.logger.info(
                        f"[TREND-DOWN] {symbol} SHORT 止损下移: "
                        f"${old_stop:.2f} → ${new_stop:.2f} "
                        f"(当前价: ${current_price:.2f}, 盈利: {((stop_data['entry_price'] - current_price) / stop_data['entry_price'] * 100):.2f}%)"
                    )

        # 更新ATR和时间戳
        stop_data['atr'] = atr
        stop_data['last_update'] = datetime.now().isoformat()

        return stop_data

    def check_stop_triggered(self, symbol: str, current_price: float) -> bool:
        """
        检查止损是否被触发

        Args:
            symbol: 交易对
            current_price: 当前价格

        Returns:
            是否触发止损
        """
        if symbol not in self.trailing_stops:
            return False

        stop_data = self.trailing_stops[symbol]
        side = stop_data['side']
        stop_price = stop_data['current_stop']

        triggered = False

        if side == 'LONG':
            # 多仓：价格跌破止损价
            if current_price <= stop_price:
                triggered = True
        else:  # SHORT
            # 空仓：价格突破止损价
            if current_price >= stop_price:
                triggered = True

        if triggered:
            stop_data['triggered'] = True
            pnl_pct = self._calculate_pnl_pct(stop_data, current_price)

            self.logger.warning(
                f"🛑 {symbol} {side} 止损触发! "
                f"当前价=${current_price:.2f}, 止损价=${stop_price:.2f}, "
                f"盈亏: {pnl_pct:+.2f}%"
            )

        return triggered

    def get_stop_data(self, symbol: str) -> Optional[Dict]:
        """
        获取指定交易对的止损数据

        Args:
            symbol: 交易对

        Returns:
            止损数据字典，如果不存在则返回None
        """
        return self.trailing_stops.get(symbol)

    def remove_stop(self, symbol: str) -> Optional[Dict]:
        """
        移除追踪止损（平仓时调用）

        Args:
            symbol: 交易对

        Returns:
            被移除的止损数据
        """
        if symbol in self.trailing_stops:
            stop_data = self.trailing_stops.pop(symbol)
            self.logger.info(f"移除 {symbol} 追踪止损")
            return stop_data
        return None

    def get_all_stops(self) -> Dict[str, Dict]:
        """
        获取所有追踪止损数据

        Returns:
            所有止损数据字典
        """
        return self.trailing_stops.copy()

    def _calculate_pnl_pct(self, stop_data: Dict, current_price: float) -> float:
        """
        计算盈亏百分比

        Args:
            stop_data: 止损数据
            current_price: 当前价格

        Returns:
            盈亏百分比
        """
        entry_price = stop_data['entry_price']
        side = stop_data['side']

        if side == 'LONG':
            return ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            return ((entry_price - current_price) / entry_price) * 100

    def get_stop_summary(self, symbol: str) -> Optional[str]:
        """
        获取止损状态摘要

        Args:
            symbol: 交易对

        Returns:
            状态摘要字符串
        """
        stop_data = self.get_stop_data(symbol)
        if not stop_data:
            return None

        side = stop_data['side']
        entry = stop_data['entry_price']
        current_stop = stop_data['current_stop']
        initial_stop = stop_data['initial_stop']

        stop_moved = current_stop != initial_stop

        if side == 'LONG':
            highest = stop_data['highest_price']
            summary = (
                f"{symbol} LONG追踪止损: 入场${entry:.2f}, "
                f"最高${highest:.2f}, 止损${current_stop:.2f} "
                f"{'(已上移)' if stop_moved else '(初始)'}"
            )
        else:
            lowest = stop_data['lowest_price']
            summary = (
                f"{symbol} SHORT追踪止损: 入场${entry:.2f}, "
                f"最低${lowest:.2f}, 止损${current_stop:.2f} "
                f"{'(已下移)' if stop_moved else '(初始)'}"
            )

        return summary
