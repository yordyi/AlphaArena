"""
风险管理系统
管理仓位大小、止损止盈、资金风控
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PositionRisk:
    """持仓风险指标"""
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    side: str  # LONG/SHORT
    unrealized_pnl: float
    unrealized_pnl_percent: float
    liquidation_price: Optional[float] = None
    margin_ratio: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.LOW


class RiskManager:
    """交易风险管理器"""

    def __init__(self, config: Dict):
        """
        初始化风险管理器

        Args:
            config: 风险管理配置
        """
        # 资金风控限制
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.02)  # 单次最大风险2%
        self.max_position_size = config.get('max_position_size', 0.1)  # 单仓位最大10%
        self.max_leverage = config.get('max_leverage', 10)  # 最大杠杆10倍

        # 止损止盈设置
        self.default_stop_loss_pct = config.get('default_stop_loss_pct', 0.02)  # 默认止损2%
        self.default_take_profit_pct = config.get('default_take_profit_pct', 0.04)  # 默认止盈4%
        self.trailing_stop_pct = config.get('trailing_stop_pct', 0.01)  # 移动止损1%

        # 风险阈值
        self.margin_call_threshold = config.get('margin_call_threshold', 0.8)  # 保证金率80%警戒
        self.max_drawdown = config.get('max_drawdown', 0.15)  # 最大回撤15%
        self.max_daily_loss = config.get('max_daily_loss', 0.05)  # 每日最大亏损5%

        # 仓位限制
        self.max_open_positions = config.get('max_open_positions', 10)  # 最多10个持仓
        self.max_correlation = config.get('max_correlation', 0.7)  # 最大相关性0.7

        # 追踪数据
        self.daily_pnl = 0.0
        self.initial_balance = 0.0
        self.peak_balance = 0.0
        self.daily_trades = 0
        self.max_daily_trades = config.get('max_daily_trades', 50)

    def calculate_position_size(self, account_balance: float, entry_price: float,
                                stop_loss_price: float, risk_per_trade: float = None) -> float:
        """
        根据风险管理规则计算仓位大小

        Args:
            account_balance: 账户总余额
            entry_price: 入场价格
            stop_loss_price: 止损价格
            risk_per_trade: 单次交易风险比例

        Returns:
            建议的仓位大小（以合约张数计）
        """
        if risk_per_trade is None:
            risk_per_trade = self.max_portfolio_risk

        # 计算风险金额
        risk_amount = account_balance * risk_per_trade

        # 计算每单位价格风险
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk == 0:
            return 0

        # 计算仓位大小
        position_size = risk_amount / price_risk

        # 应用最大仓位限制
        max_position_value = account_balance * self.max_position_size
        position_value = position_size * entry_price

        if position_value > max_position_value:
            position_size = max_position_value / entry_price

        return round(position_size, 3)

    def calculate_stop_loss(self, entry_price: float, side: str,
                           stop_loss_pct: float = None) -> float:
        """
        计算止损价格

        Args:
            entry_price: 入场价格
            side: 方向 (BUY/SELL 或 LONG/SHORT)
            stop_loss_pct: 止损百分比

        Returns:
            止损价格
        """
        if stop_loss_pct is None:
            stop_loss_pct = self.default_stop_loss_pct

        if side in ['BUY', 'LONG']:
            return round(entry_price * (1 - stop_loss_pct), 2)
        else:  # SELL/SHORT
            return round(entry_price * (1 + stop_loss_pct), 2)

    def calculate_take_profit(self, entry_price: float, side: str,
                             take_profit_pct: float = None) -> float:
        """
        计算止盈价格

        Args:
            entry_price: 入场价格
            side: 方向 (BUY/SELL 或 LONG/SHORT)
            take_profit_pct: 止盈百分比

        Returns:
            止盈价格
        """
        if take_profit_pct is None:
            take_profit_pct = self.default_take_profit_pct

        if side in ['BUY', 'LONG']:
            return round(entry_price * (1 + take_profit_pct), 2)
        else:  # SELL/SHORT
            return round(entry_price * (1 - take_profit_pct), 2)

    def assess_position_risk(self, position: Dict, current_price: float) -> PositionRisk:
        """
        评估单个持仓的风险

        Args:
            position: Binance持仓数据
            current_price: 当前市场价格

        Returns:
            PositionRisk对象
        """
        entry_price = float(position.get('entryPrice', 0))
        quantity = float(position.get('positionAmt', 0))
        unrealized_pnl = float(position.get('unRealizedProfit', 0))
        liquidation_price = float(position.get('liquidationPrice', 0))

        # 判断多空方向
        side = 'LONG' if quantity > 0 else 'SHORT'

        # 计算收益率
        if entry_price == 0:
            unrealized_pnl_percent = 0
        else:
            if quantity > 0:  # 多仓
                unrealized_pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:  # 空仓
                unrealized_pnl_percent = ((entry_price - current_price) / entry_price) * 100

        # 保证金率
        margin_ratio = None
        if 'marginRatio' in position:
            margin_ratio = float(position['marginRatio'])

        # 确定风险等级
        risk_level = self._determine_risk_level(unrealized_pnl_percent, margin_ratio)

        return PositionRisk(
            symbol=position['symbol'],
            entry_price=entry_price,
            current_price=current_price,
            quantity=abs(quantity),
            side=side,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            liquidation_price=liquidation_price if liquidation_price != 0 else None,
            margin_ratio=margin_ratio,
            risk_level=risk_level
        )

    def _determine_risk_level(self, pnl_percent: float,
                             margin_ratio: Optional[float]) -> RiskLevel:
        """根据PnL和保证金率确定风险等级"""
        # 优先检查保证金率（最关键）
        if margin_ratio is not None and margin_ratio > self.margin_call_threshold:
            return RiskLevel.CRITICAL

        # 检查未实现盈亏
        if pnl_percent < -10:
            return RiskLevel.CRITICAL
        elif pnl_percent < -5:
            return RiskLevel.HIGH
        elif pnl_percent < -2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def check_trading_allowed(self, account_balance: float) -> Tuple[bool, str]:
        """
        检查是否允许交易

        Returns:
            (是否允许, 原因说明)
        """
        # 初始化追踪
        if self.initial_balance == 0:
            self.initial_balance = account_balance
            self.peak_balance = account_balance

        # 更新峰值余额
        if account_balance > self.peak_balance:
            self.peak_balance = account_balance

        # 检查每日亏损限制
        if self.daily_pnl < 0:
            daily_loss_pct = abs(self.daily_pnl) / self.initial_balance
            if daily_loss_pct > self.max_daily_loss:
                return False, f"达到每日亏损限制: {daily_loss_pct:.2%}"

        # 检查最大回撤
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - account_balance) / self.peak_balance
            if drawdown > self.max_drawdown:
                return False, f"达到最大回撤限制: {drawdown:.2%}"

        # 检查每日交易次数
        if self.daily_trades >= self.max_daily_trades:
            return False, f"达到每日交易次数限制: {self.daily_trades}/{self.max_daily_trades}"

        return True, "允许交易"

    def update_daily_pnl(self, pnl: float):
        """更新每日盈亏"""
        self.daily_pnl += pnl

    def increment_trade_count(self):
        """增加交易计数"""
        self.daily_trades += 1

    def reset_daily_metrics(self):
        """重置每日指标（每天开始时调用）"""
        self.daily_pnl = 0.0
        self.daily_trades = 0

    def validate_order(self, symbol: str, quantity: float, price: float,
                      account_balance: float, open_positions: int,
                      leverage: int = 1) -> Tuple[bool, str]:
        """
        验证订单是否符合风险管理规则

        Returns:
            (是否有效, 原因说明)
        """
        # 检查是否允许交易
        allowed, reason = self.check_trading_allowed(account_balance)
        if not allowed:
            return False, reason

        # 检查最大持仓数
        if open_positions >= self.max_open_positions:
            return False, f"达到最大持仓数限制: {self.max_open_positions}"

        # 检查杠杆倍数
        if leverage > self.max_leverage:
            return False, f"杠杆倍数过高: {leverage}x > {self.max_leverage}x"

        # 检查仓位大小
        position_value = quantity * price
        position_size_pct = position_value / account_balance

        if position_size_pct > self.max_position_size:
            return False, f"仓位过大: {position_size_pct:.2%} > {self.max_position_size:.2%}"

        return True, "订单验证通过"

    def get_portfolio_risk_summary(self, positions: List[Dict],
                                   account_balance: float) -> Dict:
        """
        获取投资组合风险摘要

        Returns:
            风险指标字典
        """
        total_unrealized_pnl = sum(float(p.get('unRealizedProfit', 0)) for p in positions)
        total_position_value = sum(
            abs(float(p.get('positionAmt', 0))) * float(p.get('entryPrice', 0))
            for p in positions
        )

        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

        # 计算风险指标
        portfolio_risk_pct = (total_position_value / account_balance * 100) if account_balance > 0 else 0
        unrealized_pnl_pct = (total_unrealized_pnl / account_balance * 100) if account_balance > 0 else 0

        # 按风险等级统计持仓
        risk_counts = {level.value: 0 for level in RiskLevel}
        critical_positions = []

        for pos in active_positions:
            current_price = float(pos.get('markPrice', pos.get('entryPrice', 0)))
            risk = self.assess_position_risk(pos, current_price)
            risk_counts[risk.risk_level.value] += 1

            if risk.risk_level == RiskLevel.CRITICAL:
                critical_positions.append({
                    'symbol': pos['symbol'],
                    'pnl_percent': risk.unrealized_pnl_percent,
                    'margin_ratio': risk.margin_ratio
                })

        return {
            'total_positions': len(active_positions),
            'total_unrealized_pnl': round(total_unrealized_pnl, 2),
            'unrealized_pnl_percent': round(unrealized_pnl_pct, 2),
            'portfolio_risk_percent': round(portfolio_risk_pct, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_trades': self.daily_trades,
            'risk_level_counts': risk_counts,
            'critical_positions': critical_positions,
            'trading_allowed': self.check_trading_allowed(account_balance)[0],
            'account_balance': round(account_balance, 2),
            'peak_balance': round(self.peak_balance, 2)
        }

    def suggest_position_adjustment(self, position: Dict, current_price: float) -> Optional[str]:
        """
        建议仓位调整

        Returns:
            调整建议字符串，无需调整则返回None
        """
        risk = self.assess_position_risk(position, current_price)

        if risk.risk_level == RiskLevel.CRITICAL:
            return f"[WARNING] 紧急：建议立即平仓 {risk.symbol}，当前亏损 {risk.unrealized_pnl_percent:.2f}%"

        if risk.risk_level == RiskLevel.HIGH:
            return f"[WARNING] 警告：{risk.symbol} 风险偏高，考虑减仓或设置止损"

        if risk.risk_level == RiskLevel.MEDIUM:
            return f"ℹ️ 注意：{risk.symbol} 需要关注，建议设置移动止损"

        # 盈利建议
        if risk.unrealized_pnl_percent > 20:
            return f"[OK] {risk.symbol} 盈利丰厚 ({risk.unrealized_pnl_percent:.2f}%)，建议部分止盈"

        return None

    def check_liquidation_risk(self, positions: List[Dict],
                               liquidation_threshold: float = 0.03) -> List[Dict]:
        """
        检查清算风险预警

        Args:
            positions: 持仓列表（来自Binance API）
            liquidation_threshold: 清算价预警阈值（默认3% = 0.03）

        Returns:
            预警列表，包含：
            - symbol: 交易对
            - side: 持仓方向 (LONG/SHORT)
            - current_price: 当前价格
            - liquidation_price: 清算价
            - distance_pct: 距离清算价百分比
            - risk_level: 风险等级 (CRITICAL/HIGH)
            - message: 预警消息
        """
        warnings = []

        for position in positions:
            # 只检查有持仓的合约
            position_amt = float(position.get('positionAmt', 0))
            if position_amt == 0:
                continue

            current_price = float(position.get('markPrice', 0))
            liquidation_price = float(position.get('liquidationPrice', 0))

            # 如果没有清算价数据，跳过
            if liquidation_price == 0 or current_price == 0:
                continue

            # 判断持仓方向
            side = 'LONG' if position_amt > 0 else 'SHORT'

            # 计算距离清算价的百分比
            if side == 'LONG':
                # 多仓：当前价 > 清算价，距离 = (当前价 - 清算价) / 当前价
                distance_pct = (current_price - liquidation_price) / current_price
            else:  # SHORT
                # 空仓：当前价 < 清算价，距离 = (清算价 - 当前价) / 当前价
                distance_pct = (liquidation_price - current_price) / current_price

            # 只有在接近清算价时才预警（距离为正且小于等于阈值）
            if 0 < distance_pct <= liquidation_threshold:
                # 风险等级分类
                if distance_pct <= 0.01:  # 1%以内：危急
                    risk_level = 'CRITICAL'
                    emoji = '🚨'
                elif distance_pct <= 0.02:  # 2%以内：非常高
                    risk_level = 'HIGH'
                    emoji = '[WARNING]'
                else:  # 3%以内：高
                    risk_level = 'MEDIUM'
                    emoji = '⚡'

                warning = {
                    'symbol': position['symbol'],
                    'side': side,
                    'current_price': round(current_price, 2),
                    'liquidation_price': round(liquidation_price, 2),
                    'distance_pct': round(distance_pct * 100, 2),
                    'risk_level': risk_level,
                    'message': f"{emoji} {position['symbol']} {side}仓距离清算价仅剩 {distance_pct*100:.2f}%",
                    'timestamp': datetime.now().isoformat()
                }

                warnings.append(warning)

        # 按风险等级和距离排序（最危险的在前）
        warnings.sort(key=lambda x: (
            0 if x['risk_level'] == 'CRITICAL' else (1 if x['risk_level'] == 'HIGH' else 2),
            x['distance_pct']
        ))

        return warnings
