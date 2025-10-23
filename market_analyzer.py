"""
市场分析工具
提供技术指标、价格分析和交易信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class MarketAnalyzer:
    """市场数据分析器"""

    def __init__(self, client):
        """
        初始化市场分析器

        Args:
            client: BinanceClient实例
        """
        self.client = client

    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        ticker = self.client.get_ticker_price(symbol)
        return float(ticker['price'])

    def get_price_change_24h(self, symbol: str) -> Dict:
        """获取24小时价格变化"""
        ticker = self.client.get_24h_ticker(symbol)
        return {
            'symbol': symbol,
            'price': float(ticker['lastPrice']),
            'change_percent': float(ticker['priceChangePercent']),
            'high_24h': float(ticker['highPrice']),
            'low_24h': float(ticker['lowPrice']),
            'volume_24h': float(ticker['volume']),
            'quote_volume_24h': float(ticker['quoteVolume'])
        }

    def get_kline_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        获取K线数据并转换为DataFrame

        Args:
            symbol: 交易对
            interval: 时间间隔 ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: 数据数量

        Returns:
            包含OHLCV数据的DataFrame
        """
        klines = self.client.get_klines(symbol, interval, limit)

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    # ========== 技术指标 ==========

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """计算简单移动平均线"""
        return df['close'].rolling(window=period).mean()

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算RSI指标

        Args:
            df: K线数据
            period: 周期（默认14）

        Returns:
            RSI值序列
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, df: pd.DataFrame,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标

        Returns:
            (MACD线, 信号线, 柱状图)
        """
        ema_fast = self.calculate_ema(df, fast_period)
        ema_slow = self.calculate_ema(df, slow_period)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, df: pd.DataFrame,
                                  period: int = 20,
                                  std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算布林带

        Returns:
            (上轨, 中轨, 下轨)
        """
        sma = self.calculate_sma(df, period)
        std = df['close'].rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, sma, lower_band

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算平均真实波幅（ATR）"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    # ========== 交易信号 ==========

    def get_trend_signal(self, symbol: str, interval: str = '1h') -> Dict:
        """
        获取趋势信号

        Returns:
            包含趋势分析的字典
        """
        df = self.get_kline_data(symbol, interval, 100)

        # 计算移动平均线
        df['sma_20'] = self.calculate_sma(df, 20)
        df['sma_50'] = self.calculate_sma(df, 50)
        df['ema_12'] = self.calculate_ema(df, 12)
        df['ema_26'] = self.calculate_ema(df, 26)

        current_price = df['close'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        sma_50 = df['sma_50'].iloc[-1]

        # 判断趋势
        if current_price > sma_20 > sma_50:
            trend = 'UPTREND'
            signal = 'BULLISH'
        elif current_price < sma_20 < sma_50:
            trend = 'DOWNTREND'
            signal = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
            signal = 'NEUTRAL'

        return {
            'symbol': symbol,
            'interval': interval,
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'trend': trend,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        }

    def get_rsi_signal(self, symbol: str, interval: str = '1h') -> Dict:
        """
        获取RSI信号

        Returns:
            包含RSI分析的字典
        """
        df = self.get_kline_data(symbol, interval, 100)
        df['rsi'] = self.calculate_rsi(df, 14)

        current_rsi = df['rsi'].iloc[-1]

        # 判断超买超卖
        if current_rsi > 70:
            signal = 'OVERBOUGHT'
            action = 'SELL'
        elif current_rsi < 30:
            signal = 'OVERSOLD'
            action = 'BUY'
        else:
            signal = 'NEUTRAL'
            action = 'HOLD'

        return {
            'symbol': symbol,
            'interval': interval,
            'rsi': current_rsi,
            'signal': signal,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }

    def get_macd_signal(self, symbol: str, interval: str = '1h') -> Dict:
        """
        获取MACD信号

        Returns:
            包含MACD分析的字典
        """
        df = self.get_kline_data(symbol, interval, 100)
        macd_line, signal_line, histogram = self.calculate_macd(df)

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2]

        # 判断信号
        if current_macd > current_signal and prev_histogram < 0 < current_histogram:
            signal = 'BULLISH_CROSSOVER'
            action = 'BUY'
        elif current_macd < current_signal and prev_histogram > 0 > current_histogram:
            signal = 'BEARISH_CROSSOVER'
            action = 'SELL'
        else:
            signal = 'NEUTRAL'
            action = 'HOLD'

        return {
            'symbol': symbol,
            'interval': interval,
            'macd': current_macd,
            'signal_line': current_signal,
            'histogram': current_histogram,
            'signal': signal,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }

    def get_combined_signal(self, symbol: str, interval: str = '1h') -> Dict:
        """
        获取综合信号（结合多个指标）

        Returns:
            包含综合分析的字典
        """
        trend_signal = self.get_trend_signal(symbol, interval)
        rsi_signal = self.get_rsi_signal(symbol, interval)
        macd_signal = self.get_macd_signal(symbol, interval)

        # 信号评分
        buy_score = 0
        sell_score = 0

        if trend_signal['signal'] == 'BULLISH':
            buy_score += 1
        elif trend_signal['signal'] == 'BEARISH':
            sell_score += 1

        if rsi_signal['action'] == 'BUY':
            buy_score += 1
        elif rsi_signal['action'] == 'SELL':
            sell_score += 1

        if macd_signal['action'] == 'BUY':
            buy_score += 1
        elif macd_signal['action'] == 'SELL':
            sell_score += 1

        # 综合判断
        if buy_score >= 2:
            final_signal = 'STRONG_BUY'
        elif sell_score >= 2:
            final_signal = 'STRONG_SELL'
        elif buy_score > sell_score:
            final_signal = 'BUY'
        elif sell_score > buy_score:
            final_signal = 'SELL'
        else:
            final_signal = 'HOLD'

        return {
            'symbol': symbol,
            'interval': interval,
            'current_price': trend_signal['current_price'],
            'trend': trend_signal['trend'],
            'rsi': rsi_signal['rsi'],
            'macd_signal': macd_signal['signal'],
            'buy_score': buy_score,
            'sell_score': sell_score,
            'final_signal': final_signal,
            'timestamp': datetime.now().isoformat()
        }

    # ========== 支撑阻力 ==========

    def find_support_resistance(self, symbol: str, interval: str = '1h',
                                lookback: int = 50) -> Dict:
        """
        寻找支撑位和阻力位

        Returns:
            包含支撑阻力位的字典
        """
        df = self.get_kline_data(symbol, interval, lookback)

        # 找局部高点和低点
        df['local_max'] = df['high'].rolling(window=5, center=True).max()
        df['local_min'] = df['low'].rolling(window=5, center=True).min()

        resistance_levels = df[df['high'] == df['local_max']]['high'].unique()
        support_levels = df[df['low'] == df['local_min']]['low'].unique()

        # 排序并取最近的几个
        resistance_levels = sorted(resistance_levels, reverse=True)[:3]
        support_levels = sorted(support_levels, reverse=True)[:3]

        current_price = df['close'].iloc[-1]

        return {
            'symbol': symbol,
            'current_price': current_price,
            'resistance_levels': [float(r) for r in resistance_levels],
            'support_levels': [float(s) for s in support_levels],
            'timestamp': datetime.now().isoformat()
        }

    # ========== 波动率分析 ==========

    def calculate_volatility(self, symbol: str, interval: str = '1h',
                            period: int = 20) -> Dict:
        """
        计算价格波动率

        Returns:
            波动率分析字典
        """
        df = self.get_kline_data(symbol, interval, period + 10)

        # 计算收益率
        df['returns'] = df['close'].pct_change()

        # 计算波动率（标准差）
        volatility = df['returns'].std() * np.sqrt(period)

        # 计算ATR
        atr = self.calculate_atr(df, 14).iloc[-1]
        current_price = df['close'].iloc[-1]
        atr_percent = (atr / current_price) * 100

        return {
            'symbol': symbol,
            'volatility': float(volatility),
            'atr': float(atr),
            'atr_percent': float(atr_percent),
            'is_high_volatility': atr_percent > 3,
            'timestamp': datetime.now().isoformat()
        }

    # ========== 订单簿分析 ==========

    def analyze_order_book(self, symbol: str, depth: int = 20) -> Dict:
        """
        分析订单簿，找出买卖压力

        Returns:
            订单簿分析字典
        """
        order_book = self.client.get_order_book(symbol, depth)

        bids = order_book['bids'][:depth]  # 买单
        asks = order_book['asks'][:depth]  # 卖单

        # 计算买卖量
        total_bid_volume = sum(float(bid[1]) for bid in bids)
        total_ask_volume = sum(float(ask[1]) for ask in asks)

        # 买卖压力比
        buy_pressure = total_bid_volume / (total_bid_volume + total_ask_volume)
        sell_pressure = total_ask_volume / (total_bid_volume + total_ask_volume)

        # 最优买卖价
        best_bid = float(bids[0][0]) if bids else 0
        best_ask = float(asks[0][0]) if asks else 0
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid * 100) if best_bid > 0 else 0

        return {
            'symbol': symbol,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'spread_percent': spread_percent,
            'total_bid_volume': total_bid_volume,
            'total_ask_volume': total_ask_volume,
            'buy_pressure': buy_pressure,
            'sell_pressure': sell_pressure,
            'market_sentiment': 'BULLISH' if buy_pressure > 0.55 else 'BEARISH' if sell_pressure > 0.55 else 'NEUTRAL',
            'timestamp': datetime.now().isoformat()
        }

    # ========== 市场概览 ==========

    def get_market_overview(self, symbol: str) -> Dict:
        """
        获取完整的市场概览

        Returns:
            综合市场分析
        """
        price_info = self.get_price_change_24h(symbol)
        combined_signal = self.get_combined_signal(symbol)
        volatility = self.calculate_volatility(symbol)
        order_book = self.analyze_order_book(symbol)

        return {
            'symbol': symbol,
            'price_info': price_info,
            'technical_signal': combined_signal,
            'volatility': volatility,
            'order_book': order_book,
            'timestamp': datetime.now().isoformat()
        }

    # ========== 增强数据获取（用于AI决策）==========

    def get_intraday_series(self, symbol: str, interval: str = '3m', limit: int = 10) -> Dict:
        """
        获取日内时间序列数据（用于AI分析）

        Args:
            symbol: 交易对
            interval: 时间间隔（默认3分钟）
            limit: 数据点数量（默认10）

        Returns:
            包含价格和指标序列的字典
        """
        df = self.get_kline_data(symbol, interval, limit)

        # 计算各种指标
        df['ema20'] = self.calculate_ema(df, 20 if len(df) >= 20 else len(df) // 2)
        df['rsi7'] = self.calculate_rsi(df, min(7, len(df) - 1))
        df['rsi14'] = self.calculate_rsi(df, min(14, len(df) - 1))

        macd_line, signal_line, _ = self.calculate_macd(df)
        df['macd'] = macd_line

        # 转换为列表（从旧到新）
        return {
            'mid_prices': df['close'].tolist(),
            'ema20_values': df['ema20'].fillna(df['close']).tolist(),
            'macd_values': df['macd'].fillna(0).tolist(),
            'rsi7_values': df['rsi7'].fillna(50).tolist(),
            'rsi14_values': df['rsi14'].fillna(50).tolist(),
            'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        }

    def get_4h_context(self, symbol: str, limit: int = 10) -> Dict:
        """
        获取4小时级别上下文数据

        Args:
            symbol: 交易对
            limit: K线数量

        Returns:
            4小时级别的市场上下文
        """
        df = self.get_kline_data(symbol, '4h', limit)

        # 计算长期指标
        df['ema20'] = self.calculate_ema(df, min(20, len(df)))
        df['ema50'] = self.calculate_ema(df, min(50, len(df)))
        df['atr3'] = self.calculate_atr(df, min(3, len(df) - 1))
        df['atr14'] = self.calculate_atr(df, min(14, len(df) - 1))
        df['rsi14'] = self.calculate_rsi(df, min(14, len(df) - 1))

        macd_line, signal_line, _ = self.calculate_macd(df)
        df['macd'] = macd_line

        # 最新值
        latest = df.iloc[-1]

        # 平均成交量
        avg_volume = df['volume'].mean()

        return {
            'ema20': float(latest['ema20']) if not pd.isna(latest['ema20']) else None,
            'ema50': float(latest['ema50']) if not pd.isna(latest['ema50']) else None,
            'atr3': float(latest['atr3']) if not pd.isna(latest['atr3']) else None,
            'atr14': float(latest['atr14']) if not pd.isna(latest['atr14']) else None,
            'current_volume': float(latest['volume']),
            'average_volume': float(avg_volume),
            'macd_series': df['macd'].fillna(0).tolist()[-10:],
            'rsi14_series': df['rsi14'].fillna(50).tolist()[-10:]
        }

    def get_futures_market_data(self, symbol: str) -> Dict:
        """
        获取合约市场数据（资金费率、持仓量）

        Args:
            symbol: 交易对

        Returns:
            合约市场数据
        """
        try:
            # 获取当前资金费率
            funding_rate_data = self.client.get_current_funding_rate(symbol)
            current_funding_rate = float(funding_rate_data.get('fundingRate', 0))

            # 获取持仓量
            open_interest_data = self.client.get_open_interest(symbol)
            current_open_interest = float(open_interest_data.get('openInterest', 0))

            # 获取持仓量历史（用于计算平均）
            oi_history = self.client.get_open_interest_statistics(symbol, period='5m', limit=10)
            if oi_history:
                avg_open_interest = sum(float(item['sumOpenInterest']) for item in oi_history) / len(oi_history)
            else:
                avg_open_interest = current_open_interest

            return {
                'funding_rate': current_funding_rate,
                'open_interest': {
                    'current': current_open_interest,
                    'average': avg_open_interest
                }
            }
        except Exception as e:
            return {
                'funding_rate': 0,
                'open_interest': {
                    'current': 0,
                    'average': 0
                },
                'error': str(e)
            }

    def get_comprehensive_market_context(self, symbol: str) -> Dict:
        """
        获取完整的市场上下文（供AI决策使用）

        包含：
        - 当前价格和基础指标
        - 日内时间序列（3分钟，10个点）
        - 4小时级别上下文
        - 合约市场数据（资金费率、持仓量）

        Args:
            symbol: 交易对

        Returns:
            完整的市场上下文数据
        """
        # 获取当前快照
        df = self.get_kline_data(symbol, '1m', 1)
        current_price = float(df['close'].iloc[-1])

        # 获取短期技术指标
        df_short = self.get_kline_data(symbol, '3m', 30)
        current_ema20 = float(self.calculate_ema(df_short, 20).iloc[-1])
        current_rsi7 = float(self.calculate_rsi(df_short, 7).iloc[-1])

        macd_line, _, _ = self.calculate_macd(df_short)
        current_macd = float(macd_line.iloc[-1])

        # 获取日内序列
        intraday_series = self.get_intraday_series(symbol, '3m', 10)

        # 获取4小时上下文
        context_4h = self.get_4h_context(symbol, 10)

        # 获取合约数据
        futures_data = self.get_futures_market_data(symbol)

        # 获取市场概览（用于向后兼容）
        overview = self.get_market_overview(symbol)
        price_info = overview.get('price_info', {})

        # 计算完整的技术指标（向后兼容）
        df_1h = self.get_kline_data(symbol, '1h', 100)
        rsi14 = self.calculate_rsi(df_1h, period=14)
        macd_line, signal_line, histogram = self.calculate_macd(df_1h)
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df_1h, period=20)
        sma_20 = self.calculate_sma(df_1h, 20)
        sma_50 = self.calculate_sma(df_1h, 50)

        return {
            'symbol': symbol,
            # 新格式：增强数据
            'current_snapshot': {
                'price': current_price,
                'ema20': current_ema20,
                'macd': current_macd,
                'rsi7': current_rsi7
            },
            'intraday_series': intraday_series,
            'long_term_context_4h': context_4h,
            'futures_market': futures_data,
            'timestamp': datetime.now().isoformat(),

            # 旧格式：向后兼容字段
            'current_price': current_price,
            'price_change_24h': price_info.get('change_percent', 0),
            'rsi': float(rsi14.iloc[-1]),
            'macd': float(macd_line.iloc[-1]),
            'macd_signal': float(signal_line.iloc[-1]),
            'macd_histogram': float(histogram.iloc[-1]),
            'bollinger_upper': float(upper_band.iloc[-1]),
            'bollinger_middle': float(middle_band.iloc[-1]),
            'bollinger_lower': float(lower_band.iloc[-1]),
            'sma_20': float(sma_20.iloc[-1]),
            'sma_50': float(sma_50.iloc[-1]),
            'volume_24h': price_info.get('volume', 0),
            'high_24h': price_info.get('high', current_price),
            'low_24h': price_info.get('low', current_price),
            'support_levels': [current_price * 0.98, current_price * 0.95],  # 简化
            'resistance_levels': [current_price * 1.02, current_price * 1.05],  # 简化
            'trend': 'uptrend' if current_price > float(sma_50.iloc[-1]) else 'downtrend',
            'atr': context_4h.get('atr14', 0) if context_4h else 0
        }

    @staticmethod
    def calculate_liquidation_price(entry_price: float, leverage: int, side: str) -> float:
        """
        计算清算价格

        Args:
            entry_price: 入场价格
            leverage: 杠杆倍数
            side: 持仓方向 ('LONG' 或 'SHORT')

        Returns:
            清算价格

        Formula:
            币安期货维持保证金率约为5%（不同杠杆档位略有差异）
            清算价 = 入场价 × (1 - (1 - 维持保证金率) / 杠杆)  # LONG
            清算价 = 入场价 × (1 + (1 - 维持保证金率) / 杠杆)  # SHORT
        """
        # 币安期货维持保证金率（简化处理，实际根据杠杆档位有所不同）
        maintenance_margin_rate = 0.05

        if side.upper() in ['LONG', 'BUY']:
            # 多头清算价：入场价 × (1 - (1 - MMR) / leverage)
            liquidation_price = entry_price * (1 - (1 - maintenance_margin_rate) / leverage)
        elif side.upper() in ['SHORT', 'SELL']:
            # 空头清算价：入场价 × (1 + (1 - MMR) / leverage)
            liquidation_price = entry_price * (1 + (1 - maintenance_margin_rate) / leverage)
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'LONG' or 'SHORT'")

        return round(liquidation_price, 2)
