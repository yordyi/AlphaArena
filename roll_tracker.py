"""
ROLL状态追踪器 (V2.0新增)

追踪每个symbol的滚仓状态，包括:
- ROLL次数计数（最多6次）
- 原始入场价格
- ROLL历史记录
- 自动状态管理

用途：
1. 限制ROLL次数到6次，防止过度杠杆
2. 追踪原始入场价，用于移动止损到盈亏平衡
3. 记录ROLL历史，用于分析和优化
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class RollTracker:
    """ROLL状态追踪器 - 管理滚仓状态和历史"""

    def __init__(self, data_file: str = 'roll_state.json'):
        """
        初始化ROLL追踪器

        Args:
            data_file: 数据存储文件路径
        """
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        self.data = self._load()

    def _load(self) -> Dict:
        """从文件加载ROLL状态数据"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"📂 加载ROLL状态: {len(data)}个symbol")
                    return data
            else:
                self.logger.info(f"📂 创建新的ROLL状态文件: {self.data_file}")
                return {}
        except Exception as e:
            self.logger.error(f"加载ROLL状态失败: {e}，使用空数据")
            return {}

    def _save(self):
        """保存ROLL状态数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存ROLL状态失败: {e}")

    def get_roll_count(self, symbol: str) -> int:
        """
        获取symbol的当前ROLL次数

        Args:
            symbol: 交易对

        Returns:
            ROLL次数（0-6）
        """
        if symbol not in self.data:
            return 0
        return self.data[symbol].get('roll_count', 0)

    def get_original_entry_price(self, symbol: str) -> Optional[float]:
        """
        获取symbol的原始入场价格

        Args:
            symbol: 交易对

        Returns:
            原始入场价格，如果无记录返回None
        """
        if symbol not in self.data:
            return None
        return self.data[symbol].get('original_entry_price')

    def get_roll_history(self, symbol: str) -> List[Dict]:
        """
        获取symbol的ROLL历史记录

        Args:
            symbol: 交易对

        Returns:
            ROLL历史列表，每条记录包含时间、价格、盈利等信息
        """
        if symbol not in self.data:
            return []
        return self.data[symbol].get('roll_history', [])

    def initialize_position(self, symbol: str, entry_price: float,
                           position_amt: float, side: str):
        """
        初始化新仓位（首次开仓时调用）

        Args:
            symbol: 交易对
            entry_price: 入场价格
            position_amt: 仓位数量
            side: 仓位方向 ('LONG' 或 'SHORT')
        """
        self.data[symbol] = {
            'symbol': symbol,
            'original_entry_price': entry_price,
            'original_position_amt': abs(position_amt),
            'side': side,
            'roll_count': 0,
            'roll_history': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        self._save()
        self.logger.info(
            f"🆕 [ROLL追踪] 初始化 {symbol}: 入场价${entry_price:.2f}, "
            f"{side} {abs(position_amt):.3f}"
        )

    def increment_roll_count(self, symbol: str, roll_details: Dict) -> int:
        """
        增加ROLL次数并记录历史

        Args:
            symbol: 交易对
            roll_details: ROLL详情
                {
                    'current_price': 当前价格,
                    'unrealized_pnl': 未实现盈亏,
                    'profit_pct': 盈利百分比,
                    'reinvest_amount': 加仓金额,
                    'new_position_qty': 新加仓位数量,
                    'leverage': 杠杆
                }

        Returns:
            新的ROLL次数
        """
        if symbol not in self.data:
            self.logger.warning(f"⚠️  Symbol {symbol} 未初始化，无法ROLL")
            return 0

        # 增加计数
        new_count = self.data[symbol]['roll_count'] + 1

        # 检查是否超过最大次数
        if new_count > 6:
            self.logger.error(f"❌ {symbol} ROLL次数已达上限6次，拒绝继续ROLL")
            return 6  # 返回6，不增加

        # 更新数据
        self.data[symbol]['roll_count'] = new_count
        self.data[symbol]['last_updated'] = datetime.now().isoformat()

        # 记录历史
        history_entry = {
            'roll_number': new_count,
            'timestamp': datetime.now().isoformat(),
            'current_price': roll_details.get('current_price'),
            'unrealized_pnl': roll_details.get('unrealized_pnl'),
            'profit_pct': roll_details.get('profit_pct'),
            'reinvest_amount': roll_details.get('reinvest_amount'),
            'new_position_qty': roll_details.get('new_position_qty'),
            'leverage': roll_details.get('leverage')
        }
        self.data[symbol]['roll_history'].append(history_entry)

        self._save()

        self.logger.info(
            f"🔄 [ROLL追踪] {symbol} 第{new_count}次ROLL完成 "
            f"(盈利{roll_details.get('profit_pct', 0):.1f}%, "
            f"加仓${roll_details.get('reinvest_amount', 0):.2f})"
        )

        return new_count

    def can_roll(self, symbol: str) -> tuple[bool, str, int]:
        """
        检查是否可以继续ROLL

        Args:
            symbol: 交易对

        Returns:
            (是否可以ROLL, 原因, 当前ROLL次数)
        """
        if symbol not in self.data:
            return True, "新仓位，可以开始ROLL", 0

        current_count = self.data[symbol]['roll_count']

        if current_count >= 6:
            return False, f"已达到最大ROLL次数限制(6次)", current_count

        remaining = 6 - current_count
        return True, f"可以继续ROLL（已{current_count}次，还剩{remaining}次机会）", current_count

    def clear_symbol(self, symbol: str):
        """
        清除symbol的所有记录（平仓后调用）

        Args:
            symbol: 交易对
        """
        if symbol in self.data:
            roll_count = self.data[symbol].get('roll_count', 0)
            del self.data[symbol]
            self._save()
            self.logger.info(
                f"🧹 [ROLL追踪] 清除 {symbol} 记录 "
                f"(共执行了{roll_count}次ROLL)"
            )
        else:
            self.logger.debug(f"Symbol {symbol} 无ROLL记录，无需清除")

    def get_status(self, symbol: str) -> Optional[Dict]:
        """
        获取symbol的完整状态

        Args:
            symbol: 交易对

        Returns:
            完整状态字典，包含所有信息
        """
        if symbol not in self.data:
            return None
        return self.data[symbol].copy()

    def get_all_active_rolls(self) -> Dict[str, Dict]:
        """
        获取所有活跃的ROLL状态

        Returns:
            所有symbol的ROLL状态字典
        """
        return self.data.copy()

    def update_original_entry_price(self, symbol: str, new_price: float):
        """
        更新原始入场价格（用于移动止损到盈亏平衡后）

        Args:
            symbol: 交易对
            new_price: 新的"原始"入场价（通常是盈亏平衡点）
        """
        if symbol in self.data:
            old_price = self.data[symbol]['original_entry_price']
            self.data[symbol]['original_entry_price'] = new_price
            self.data[symbol]['last_updated'] = datetime.now().isoformat()
            self._save()
            self.logger.info(
                f"📝 [ROLL追踪] 更新 {symbol} 原始入场价: "
                f"${old_price:.2f} → ${new_price:.2f}"
            )

    def get_statistics(self) -> Dict:
        """
        获取ROLL统计信息

        Returns:
            {
                'total_symbols': 活跃symbol数量,
                'total_rolls': 总ROLL次数,
                'avg_rolls_per_symbol': 平均每symbol的ROLL次数,
                'symbols_at_max': 达到6次限制的symbol数量
            }
        """
        total_symbols = len(self.data)
        total_rolls = sum(s.get('roll_count', 0) for s in self.data.values())
        symbols_at_max = sum(1 for s in self.data.values() if s.get('roll_count', 0) >= 6)

        avg_rolls = total_rolls / total_symbols if total_symbols > 0 else 0

        return {
            'total_symbols': total_symbols,
            'total_rolls': total_rolls,
            'avg_rolls_per_symbol': round(avg_rolls, 2),
            'symbols_at_max': symbols_at_max,
            'data_file': self.data_file
        }


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建追踪器
    tracker = RollTracker()

    # 示例：初始化新仓位
    tracker.initialize_position(
        symbol='BTCUSDT',
        entry_price=44000.0,
        position_amt=0.01,
        side='LONG'
    )

    # 检查是否可以ROLL
    can_roll, reason, count = tracker.can_roll('BTCUSDT')
    print(f"Can roll: {can_roll}, Reason: {reason}, Count: {count}")

    # 执行第1次ROLL
    tracker.increment_roll_count('BTCUSDT', {
        'current_price': 45320,
        'unrealized_pnl': 132,
        'profit_pct': 6.5,
        'reinvest_amount': 85,
        'new_position_qty': 0.03,
        'leverage': 15
    })

    # 获取状态
    status = tracker.get_status('BTCUSDT')
    print(f"Status: {status}")

    # 获取统计
    stats = tracker.get_statistics()
    print(f"Statistics: {stats}")

    # 平仓后清除
    # tracker.clear_symbol('BTCUSDT')
