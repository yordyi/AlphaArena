"""
Binance API客户端 - 用于AI代理操控交易账户
支持现货和合约交易的完整API封装
"""

import hmac
import hashlib
import time
import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BinanceClient:
    """Binance API客户端，供AI代理使用"""

    BASE_URL = "https://api.binance.com"
    FUTURES_URL = "https://fapi.binance.com"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化Binance客户端

        Args:
            api_key: Binance API密钥
            api_secret: Binance API密钥对应的Secret
            testnet: 是否使用测试网（默认：否）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)

        if testnet:
            self.BASE_URL = "https://testnet.binance.vision"
            self.FUTURES_URL = "https://testnet.binancefuture.com"

        # 创建带重试机制的session
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        创建带重试机制的requests session

        自动重试策略:
        - SSL错误: 重试3次
        - 连接错误: 重试3次
        - 指数退避: 0.5s, 1s, 2s
        """
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总共重试3次
            backoff_factor=0.5,  # 指数退避因子: 0.5s, 1s, 2s
            status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码触发重试
            allowed_methods=["GET", "POST", "DELETE"],  # 允许重试的HTTP方法
            raise_on_status=False  # 不自动抛出HTTPError
        )

        # 创建HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # 连接池大小
            pool_maxsize=10  # 最大连接数
        )

        # 挂载到session
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成HMAC SHA256签名"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, params: Dict = None,
                 signed: bool = False, futures: bool = False) -> Dict:
        """
        向Binance API发送HTTP请求（增强版：自动重试+详细日志）

        Args:
            method: HTTP方法 (GET, POST, DELETE)
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
            futures: 是否使用合约API

        Returns:
            API响应字典
        """
        if params is None:
            params = {}

        base_url = self.FUTURES_URL if futures else self.BASE_URL
        url = f"{base_url}{endpoint}"

        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        # 尝试发送请求（自动重试机制由session处理）
        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                # 使用带重试机制的session
                if method == 'GET':
                    response = self.session.get(url, params=params, headers=headers, timeout=30)
                elif method == 'POST':
                    response = self.session.post(url, params=params, headers=headers, timeout=30)
                elif method == 'DELETE':
                    response = self.session.delete(url, params=params, headers=headers, timeout=30)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.SSLError as e:
                last_error = e
                error_type = type(e).__name__
                self.logger.warning(
                    f"[RETRY {attempt}/{max_attempts}] SSL错误: {error_type} - {str(e)[:100]}"
                )
                if attempt < max_attempts:
                    time.sleep(1 * attempt)  # 指数退避
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = e
                self.logger.warning(
                    f"[RETRY {attempt}/{max_attempts}] 连接错误: {str(e)[:100]}"
                )
                if attempt < max_attempts:
                    time.sleep(1 * attempt)
                continue

            except requests.exceptions.Timeout as e:
                last_error = e
                self.logger.warning(
                    f"[RETRY {attempt}/{max_attempts}] 超时错误: {str(e)[:100]}"
                )
                if attempt < max_attempts:
                    time.sleep(1 * attempt)
                continue

            except requests.exceptions.HTTPError as e:
                # HTTP错误不重试（4xx, 5xx已经由session处理）
                error_msg = f"API请求失败: {str(e)}"
                try:
                    error_detail = response.json()
                    error_msg += f" | 详细信息: {error_detail}"
                except:
                    pass
                raise Exception(error_msg)

            except Exception as e:
                # 其他未知错误
                last_error = e
                self.logger.error(f"未知错误: {type(e).__name__} - {str(e)}")
                raise Exception(f"API请求失败: {str(e)}")

        # 所有重试都失败
        error_msg = f"API请求失败（{max_attempts}次重试后）: {type(last_error).__name__} - {str(last_error)}"
        self.logger.error(error_msg)
        raise Exception(error_msg)

    # ========== 账户信息接口 ==========

    def get_account_info(self) -> Dict:
        """获取现货账户信息"""
        return self._request('GET', '/api/v3/account', signed=True)

    def get_account_balance(self) -> List[Dict]:
        """获取账户余额列表"""
        account = self.get_account_info()
        return account.get('balances', [])

    def get_asset_balance(self, asset: str) -> Dict:
        """获取特定资产余额"""
        balances = self.get_account_balance()
        for balance in balances:
            if balance['asset'] == asset:
                return balance
        return {'asset': asset, 'free': '0', 'locked': '0'}

    def get_futures_account_info(self) -> Dict:
        """获取合约账户信息"""
        return self._request('GET', '/fapi/v2/account', signed=True, futures=True)

    def get_futures_balance(self) -> List[Dict]:
        """获取合约账户余额"""
        account = self.get_futures_account_info()
        return account.get('assets', [])

    def get_futures_positions(self) -> List[Dict]:
        """获取所有合约持仓"""
        return self._request('GET', '/fapi/v2/positionRisk', signed=True, futures=True)

    def get_active_positions(self) -> List[Dict]:
        """获取活跃持仓（非零仓位）"""
        positions = self.get_futures_positions()
        return [p for p in positions if float(p.get('positionAmt', 0)) != 0]

    # ========== 市场数据接口 ==========

    def get_ticker_price(self, symbol: str = None) -> Dict:
        """获取当前价格"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/ticker/price', params=params)

    def get_24h_ticker(self, symbol: str) -> Dict:
        """获取24小时价格统计"""
        params = {'symbol': symbol}
        return self._request('GET', '/api/v3/ticker/24hr', params=params)

    def get_klines(self, symbol: str, interval: str, limit: int = 100,
                   startTime: int = None, endTime: int = None) -> List:
        """
        获取K线数据

        Args:
            symbol: 交易对 (如 'BTCUSDT')
            interval: K线间隔 ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: 获取数量 (最大1000)
            startTime: 开始时间戳(毫秒)
            endTime: 结束时间戳(毫秒)
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        return self._request('GET', '/api/v3/klines', params=params)

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """获取订单簿深度"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/api/v3/depth', params=params)

    def get_recent_trades(self, symbol: str, limit: int = 100) -> List:
        """获取最近成交"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/api/v3/trades', params=params)

    # ========== 现货交易接口 ==========

    def create_spot_order(self, symbol: str, side: str, order_type: str,
                         quantity: float = None, price: float = None,
                         quote_order_qty: float = None,
                         time_in_force: str = 'GTC', **kwargs) -> Dict:
        """
        创建现货订单

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET)
            quantity: 数量
            price: 价格 (LIMIT单必填)
            quote_order_qty: 以计价币种计算的数量 (仅MARKET单)
            time_in_force: 有效期 (GTC/IOC/FOK)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
        }

        if quantity:
            params['quantity'] = quantity
        if price:
            params['price'] = price
        if quote_order_qty:
            params['quoteOrderQty'] = quote_order_qty
        if order_type == 'LIMIT':
            params['timeInForce'] = time_in_force

        params.update(kwargs)
        return self._request('POST', '/api/v3/order', params=params, signed=True)

    def cancel_spot_order(self, symbol: str, order_id: int = None,
                         orig_client_order_id: str = None) -> Dict:
        """取消现货订单"""
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        return self._request('DELETE', '/api/v3/order', params=params, signed=True)

    def cancel_all_spot_orders(self, symbol: str) -> List[Dict]:
        """取消某交易对的所有现货订单"""
        params = {'symbol': symbol}
        return self._request('DELETE', '/api/v3/openOrders', params=params, signed=True)

    def get_spot_order(self, symbol: str, order_id: int) -> Dict:
        """查询现货订单"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('GET', '/api/v3/order', params=params, signed=True)

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """获取所有挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/openOrders', params=params, signed=True)

    def get_spot_trade_history(self, symbol: str = None, limit: int = 100,
                               from_id: int = None, start_time: int = None,
                               end_time: int = None) -> List[Dict]:
        """
        获取现货交易历史

        Args:
            symbol: 交易对 (如果不指定则返回所有交易对)
            limit: 返回数量 (默认100, 最大1000)
            from_id: 从哪个Trade ID开始返回
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        if from_id:
            params['fromId'] = from_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        return self._request('GET', '/api/v3/myTrades', params=params, signed=True)

    def get_spot_order_history(self, symbol: str, limit: int = 100,
                               order_id: int = None, start_time: int = None,
                               end_time: int = None) -> List[Dict]:
        """
        获取现货订单历史

        Args:
            symbol: 交易对 (必填)
            limit: 返回数量 (默认100, 最大1000)
            order_id: 订单ID (如果指定，则返回此订单ID之后的订单)
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        if order_id:
            params['orderId'] = order_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        return self._request('GET', '/api/v3/allOrders', params=params, signed=True)

    # ========== 合约交易接口 ==========

    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """设置杠杆倍数"""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._request('POST', '/fapi/v1/leverage', params=params,
                           signed=True, futures=True)

    def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """设置保证金模式 (ISOLATED/CROSSED)"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._request('POST', '/fapi/v1/marginType', params=params,
                           signed=True, futures=True)

    def create_futures_order(self, symbol: str, side: str, order_type: str,
                            quantity: float = None, price: float = None,
                            position_side: str = 'BOTH',
                            reduce_only: bool = False,
                            time_in_force: str = 'GTC', **kwargs) -> Dict:
        """
        创建合约订单

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            order_type: 订单类型 (LIMIT/MARKET/STOP/TAKE_PROFIT)
            quantity: 数量
            price: 价格
            position_side: 持仓方向 (BOTH/LONG/SHORT)
            reduce_only: 只减仓
            time_in_force: 有效期
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'positionSide': position_side
        }

        if quantity:
            params['quantity'] = quantity
        if price:
            params['price'] = price
        if reduce_only:
            params['reduceOnly'] = 'true'
        if order_type == 'LIMIT':
            params['timeInForce'] = time_in_force

        params.update(kwargs)
        return self._request('POST', '/fapi/v1/order', params=params,
                           signed=True, futures=True)

    def cancel_futures_order(self, symbol: str, order_id: int = None,
                            orig_client_order_id: str = None) -> Dict:
        """取消合约订单"""
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        return self._request('DELETE', '/fapi/v1/order', params=params,
                           signed=True, futures=True)

    def cancel_all_futures_orders(self, symbol: str) -> Dict:
        """取消某交易对的所有合约订单"""
        params = {'symbol': symbol}
        return self._request('DELETE', '/fapi/v1/allOpenOrders', params=params,
                           signed=True, futures=True)

    def get_futures_order(self, symbol: str, order_id: int) -> Dict:
        """查询合约订单"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('GET', '/fapi/v1/order', params=params,
                           signed=True, futures=True)

    def get_futures_open_orders(self, symbol: str = None) -> List[Dict]:
        """获取所有合约挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v1/openOrders', params=params,
                           signed=True, futures=True)

    def get_futures_trade_history(self, symbol: str = None, limit: int = 100,
                                  from_id: int = None, start_time: int = None,
                                  end_time: int = None) -> List[Dict]:
        """
        获取合约交易历史

        Args:
            symbol: 交易对
            limit: 返回数量 (默认100, 最大1000)
            from_id: 从哪个Trade ID开始返回
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        if from_id:
            params['fromId'] = from_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        return self._request('GET', '/fapi/v1/userTrades', params=params,
                           signed=True, futures=True)

    def get_futures_order_history(self, symbol: str, limit: int = 100,
                                  order_id: int = None, start_time: int = None,
                                  end_time: int = None) -> List[Dict]:
        """
        获取合约订单历史

        Args:
            symbol: 交易对 (必填)
            limit: 返回数量 (默认100, 最大1000)
            order_id: 订单ID (如果指定，则返回此订单ID之后的订单)
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        if order_id:
            params['orderId'] = order_id
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        return self._request('GET', '/fapi/v1/allOrders', params=params,
                           signed=True, futures=True)

    def get_futures_income_history(self, symbol: str = None, income_type: str = None,
                                   limit: int = 100, start_time: int = None,
                                   end_time: int = None) -> List[Dict]:
        """
        获取合约收益历史（包括实现盈亏、手续费等）

        Args:
            symbol: 交易对
            income_type: 收益类型 (TRANSFER, REALIZED_PNL, FUNDING_FEE, COMMISSION等)
            limit: 返回数量 (默认100, 最大1000)
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        if income_type:
            params['incomeType'] = income_type
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        return self._request('GET', '/fapi/v1/income', params=params,
                           signed=True, futures=True)

    def close_position(self, symbol: str, position_side: str = 'BOTH') -> Dict:
        """平仓"""
        positions = self.get_futures_positions()

        for pos in positions:
            if pos['symbol'] != symbol:
                continue
            if position_side != 'BOTH' and pos.get('positionSide') != position_side:
                continue

            position_amt = float(pos['positionAmt'])
            if position_amt == 0:
                continue

            side = 'SELL' if position_amt > 0 else 'BUY'
            quantity = abs(position_amt)

            # 使用positionSide来明确平仓方向,不需要reduce_only参数
            # 币安双向持仓模式下,positionSide已经足够明确
            return self.create_futures_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                position_side=pos.get('positionSide', 'BOTH')
            )

        return {'msg': 'No position to close'}

    def close_all_positions(self, symbol: str = None) -> List[Dict]:
        """
        平所有仓位并取消所有挂单

        Args:
            symbol: 指定交易对（可选），不指定则平所有仓位

        Returns:
            操作结果列表
        """
        positions = self.get_active_positions()
        results = []

        for pos in positions:
            if symbol and pos['symbol'] != symbol:
                continue

            try:
                # 先取消该交易对的所有挂单（止损止盈等）
                cancel_result = self.cancel_stop_orders(pos['symbol'])

                # 再平仓
                close_result = self.close_position(
                    pos['symbol'],
                    pos.get('positionSide', 'BOTH')
                )

                results.append({
                    'symbol': pos['symbol'],
                    'close': close_result,
                    'cancel': cancel_result
                })
            except Exception as e:
                results.append({'symbol': pos['symbol'], 'error': str(e)})

        return results

    def close_long(self, symbol: str) -> Dict:
        """
        平多单并取消所有挂单

        Args:
            symbol: 交易对

        Returns:
            平仓结果（包含取消挂单信息）
        """
        # 先取消挂单
        cancel_result = self.cancel_stop_orders(symbol)

        # 再平仓
        close_result = self.close_position(symbol, position_side='LONG')

        return {
            'close': close_result,
            'cancel': cancel_result
        }

    def close_short(self, symbol: str) -> Dict:
        """
        平空单并取消所有挂单

        Args:
            symbol: 交易对

        Returns:
            平仓结果（包含取消挂单信息）
        """
        # 先取消挂单
        cancel_result = self.cancel_stop_orders(symbol)

        # 再平仓
        close_result = self.close_position(symbol, position_side='SHORT')

        return {
            'close': close_result,
            'cancel': cancel_result
        }

    def close_position_partial(self, symbol: str, percentage: float,
                               position_side: str = 'BOTH') -> Dict:
        """
        部分平仓

        Args:
            symbol: 交易对
            percentage: 平仓百分比 (0-100)
            position_side: 持仓方向 ('BOTH', 'LONG', 'SHORT')

        Returns:
            平仓结果

        Example:
            # 平掉50%的多单仓位
            close_position_partial('BTCUSDT', 50, 'LONG')
        """
        if not 0 < percentage <= 100:
            raise ValueError("平仓百分比必须在0-100之间")

        positions = self.get_futures_positions()

        for pos in positions:
            if pos['symbol'] != symbol:
                continue
            if position_side != 'BOTH' and pos.get('positionSide') != position_side:
                continue

            position_amt = float(pos['positionAmt'])
            if position_amt == 0:
                continue

            # 计算平仓数量
            close_quantity = abs(position_amt) * (percentage / 100)

            # 根据交易对设置精度（与开仓逻辑保持一致）
            if 'BTC' in symbol:
                close_quantity = round(close_quantity, 3)  # BTC: 0.001
            elif 'ETH' in symbol:
                close_quantity = round(close_quantity, 3)  # ETH: 0.001
            elif 'BNB' in symbol:
                close_quantity = round(close_quantity, 1)  # BNB: 0.1
            elif 'SOL' in symbol:
                close_quantity = round(close_quantity, 1)  # SOL: 0.1
            elif 'DOGE' in symbol:
                close_quantity = round(close_quantity, 0)  # DOGE: 整数
            else:
                close_quantity = round(close_quantity, 1)  # 默认: 0.1

            # 确保不为0
            if close_quantity == 0:
                return {'success': False, 'error': '平仓数量太小，无法执行'}

            side = 'SELL' if position_amt > 0 else 'BUY'

            return self.create_futures_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=close_quantity,
                position_side=pos.get('positionSide', 'BOTH'),
                reduce_only=True  # 确保只平仓不开仓
            )

        return {'msg': 'No position to close'}

    def cancel_stop_orders(self, symbol: str) -> Dict:
        """
        取消指定交易对的所有止损止盈订单

        Args:
            symbol: 交易对

        Returns:
            取消结果 {'success': bool, 'cancelled_count': int}
        """
        try:
            # 获取所有挂单
            open_orders = self.get_futures_open_orders(symbol)

            cancelled_count = 0
            errors = []

            for order in open_orders:
                order_type = order.get('type', '')
                # 只取消止损止盈相关订单
                if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET',
                                 'STOP', 'TAKE_PROFIT', 'TRAILING_STOP_MARKET']:
                    try:
                        self.cancel_futures_order(symbol, order_id=order['orderId'])
                        cancelled_count += 1
                    except Exception as e:
                        errors.append(f"订单{order['orderId']}: {str(e)}")

            return {
                'success': True,
                'cancelled_count': cancelled_count,
                'message': f'成功取消 {cancelled_count} 个止损止盈订单',
                'errors': errors if errors else None
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'cancelled_count': 0
            }

    # ========== 便捷方法 ==========

    def get_usdt_balance(self) -> float:
        """获取USDT余额"""
        balance = self.get_asset_balance('USDT')
        return float(balance.get('free', 0))

    def get_futures_usdt_balance(self) -> float:
        """获取合约账户总钱包余额（所有资产，不包括未实现盈亏）"""
        # 使用账户级别的 totalWalletBalance，而不是单一 USDT 资产的 walletBalance
        # 因为账户可能持有 BNB、其他币种等多种资产
        account_info = self.get_futures_account_info()
        return float(account_info.get('totalWalletBalance', 0))

    def get_futures_available_balance(self) -> float:
        """获取合约账户可用余额（可用于开新仓）"""
        account_info = self.get_futures_account_info()
        return float(account_info.get('availableBalance', 0))

    def get_position_info(self, symbol: str) -> Dict:
        """获取特定交易对的持仓信息"""
        positions = self.get_futures_positions()
        for pos in positions:
            if pos['symbol'] == symbol and float(pos.get('positionAmt', 0)) != 0:
                return pos
        return None

    # ========== 高级订单类型 ==========

    def create_stop_loss_order(self, symbol: str, side: str, quantity: float,
                               stop_price: float, price: float = None,
                               futures: bool = False, position_side: str = None) -> Dict:
        """
        创建止损单 (STOP_LOSS / STOP_LOSS_LIMIT)

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            stop_price: 触发价格
            price: 限价单价格 (不填则为市价止损)
            futures: 是否为合约订单
            position_side: 持仓方向 (LONG/SHORT/BOTH，仅合约)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'stopPrice': stop_price,
        }

        if futures:
            order_type = 'STOP_MARKET' if price is None else 'STOP'
            params['type'] = order_type

            # 自动检测持仓模式
            if position_side is None:
                mode = self.get_position_mode()
                if mode.get('dualSidePosition'):
                    position_side = 'LONG' if side == 'SELL' else 'SHORT'
                else:
                    position_side = 'BOTH'

            params['positionSide'] = position_side

            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            return self._request('POST', '/fapi/v1/order', params=params,
                               signed=True, futures=True)
        else:
            order_type = 'STOP_LOSS' if price is None else 'STOP_LOSS_LIMIT'
            params['type'] = order_type
            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            return self._request('POST', '/api/v3/order', params=params, signed=True)

    def create_take_profit_order(self, symbol: str, side: str, quantity: float,
                                 stop_price: float, price: float = None,
                                 futures: bool = False, position_side: str = None) -> Dict:
        """
        创建止盈单 (TAKE_PROFIT / TAKE_PROFIT_LIMIT)

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            stop_price: 触发价格
            price: 限价单价格 (不填则为市价止盈)
            futures: 是否为合约订单
            position_side: 持仓方向 (LONG/SHORT/BOTH，仅合约)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'stopPrice': stop_price,
        }

        if futures:
            order_type = 'TAKE_PROFIT_MARKET' if price is None else 'TAKE_PROFIT'
            params['type'] = order_type

            # 自动检测持仓模式
            if position_side is None:
                mode = self.get_position_mode()
                if mode.get('dualSidePosition'):
                    position_side = 'LONG' if side == 'SELL' else 'SHORT'
                else:
                    position_side = 'BOTH'

            params['positionSide'] = position_side

            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            return self._request('POST', '/fapi/v1/order', params=params,
                               signed=True, futures=True)
        else:
            order_type = 'TAKE_PROFIT' if price is None else 'TAKE_PROFIT_LIMIT'
            params['type'] = order_type
            if price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            return self._request('POST', '/api/v3/order', params=params, signed=True)

    def create_trailing_stop_order(self, symbol: str, side: str, quantity: float,
                                   callback_rate: float, activation_price: float = None) -> Dict:
        """
        创建追踪止损单 (仅合约支持)

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            callback_rate: 回调幅度 (0.1 = 0.1%)
            activation_price: 激活价格 (可选)
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'TRAILING_STOP_MARKET',
            'quantity': quantity,
            'callbackRate': callback_rate,
        }

        if activation_price:
            params['activationPrice'] = activation_price

        return self._request('POST', '/fapi/v1/order', params=params,
                           signed=True, futures=True)

    def create_oco_order(self, symbol: str, side: str, quantity: float,
                        price: float, stop_price: float, stop_limit_price: float = None,
                        limit_iceberg_qty: float = None, stop_iceberg_qty: float = None) -> Dict:
        """
        创建 OCO 订单 (One-Cancels-Other，二选一订单，仅现货支持)

        Args:
            symbol: 交易对
            side: 方向 (BUY/SELL)
            quantity: 数量
            price: 限价单价格
            stop_price: 止损触发价格
            stop_limit_price: 止损限价单价格 (可选，不填则为市价止损)
            limit_iceberg_qty: 限价单冰山数量
            stop_iceberg_qty: 止损单冰山数量
        """
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stopPrice': stop_price,
        }

        if stop_limit_price:
            params['stopLimitPrice'] = stop_limit_price
            params['stopLimitTimeInForce'] = 'GTC'

        if limit_iceberg_qty:
            params['limitIcebergQty'] = limit_iceberg_qty
        if stop_iceberg_qty:
            params['stopIcebergQty'] = stop_iceberg_qty

        return self._request('POST', '/api/v3/order/oco', params=params, signed=True)

    def cancel_oco_order(self, symbol: str, order_list_id: int = None,
                        list_client_order_id: str = None) -> Dict:
        """取消 OCO 订单"""
        params = {'symbol': symbol}
        if order_list_id:
            params['orderListId'] = order_list_id
        if list_client_order_id:
            params['listClientOrderId'] = list_client_order_id
        return self._request('DELETE', '/api/v3/orderList', params=params, signed=True)

    # ========== 合约高级功能 ==========

    def get_funding_rate(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """
        查询资金费率历史

        Args:
            symbol: 交易对 (可选，不填则返回所有)
            limit: 返回数量 (默认100，最大1000)
        """
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v1/fundingRate', params=params, futures=True)

    def get_current_funding_rate(self, symbol: str) -> Dict:
        """获取当前资金费率"""
        result = self.get_funding_rate(symbol=symbol, limit=1)
        return result[0] if result else {}

    def get_open_interest(self, symbol: str) -> Dict:
        """
        获取合约持仓量（Open Interest）

        Args:
            symbol: 交易对（如 'BTCUSDT'）

        Returns:
            包含持仓量数据的字典：
            - openInterest: 持仓量
            - symbol: 交易对
            - time: 时间戳
        """
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/openInterest', params=params, futures=True)

    def get_open_interest_statistics(self, symbol: str, period: str = '5m', limit: int = 30) -> List[Dict]:
        """
        获取合约持仓量历史统计

        Args:
            symbol: 交易对
            period: 时间周期 (5m/15m/30m/1h/2h/4h/6h/12h/1d)
            limit: 返回数量 (默认30，最大500)

        Returns:
            持仓量历史数据列表
        """
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit
        }
        return self._request('GET', '/futures/data/openInterestHist', params=params, futures=True)

    def set_position_mode(self, dual_side_position: bool) -> Dict:
        """
        设置持仓模式

        Args:
            dual_side_position: True=双向持仓模式, False=单向持仓模式
        """
        params = {
            'dualSidePosition': 'true' if dual_side_position else 'false'
        }
        return self._request('POST', '/fapi/v1/positionSide/dual', params=params,
                           signed=True, futures=True)

    def get_position_mode(self) -> Dict:
        """查询持仓模式"""
        return self._request('GET', '/fapi/v1/positionSide/dual', signed=True, futures=True)

    def modify_isolated_position_margin(self, symbol: str, amount: float,
                                        margin_type: int, position_side: str = 'BOTH') -> Dict:
        """
        调整逐仓保证金

        Args:
            symbol: 交易对
            amount: 调整金额 (正数增加，负数减少)
            margin_type: 1=增加, 2=减少
            position_side: 持仓方向 (BOTH/LONG/SHORT)
        """
        params = {
            'symbol': symbol,
            'amount': abs(amount),
            'type': margin_type,
            'positionSide': position_side
        }
        return self._request('POST', '/fapi/v1/positionMargin', params=params,
                           signed=True, futures=True)

    def get_futures_exchange_info(self, symbol: str = None) -> Dict:
        """获取合约交易规则和交易对信息"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v1/exchangeInfo', params=params, futures=True)

    def get_futures_24h_ticker(self, symbol: str) -> Dict:
        """
        获取合约24小时价格统计

        Args:
            symbol: 交易对

        Returns:
            24小时统计数据
        """
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/ticker/24hr', params=params, futures=True)

    def get_spot_exchange_info(self, symbol: str = None) -> Dict:
        """获取现货交易规则和交易对信息"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/exchangeInfo', params=params)

    # ========== 账户划转 ==========

    def transfer_asset(self, asset: str, amount: float, from_account: str, to_account: str) -> Dict:
        """
        资金划转

        Args:
            asset: 资产名称 (如 'USDT')
            amount: 划转数量
            from_account: 源账户 (SPOT/USDT_FUTURE/COIN_FUTURE)
            to_account: 目标账户 (SPOT/USDT_FUTURE/COIN_FUTURE)
        """
        # 账户类型映射
        account_map = {
            'SPOT': 'MAIN',
            'USDT_FUTURE': 'UMFUTURE',
            'COIN_FUTURE': 'CMFUTURE'
        }

        # 确定划转类型
        from_type = account_map.get(from_account, from_account)
        to_type = account_map.get(to_account, to_account)
        transfer_type = f"{from_type}_{to_type}"

        params = {
            'type': transfer_type,
            'asset': asset,
            'amount': amount
        }

        return self._request('POST', '/sapi/v1/asset/transfer', params=params, signed=True)

    def get_transfer_history(self, transfer_type: str = 'UMFUTURE_MAIN',
                            start_time: int = None, end_time: int = None,
                            limit: int = 100) -> Dict:
        """
        查询资金划转历史

        Args:
            transfer_type: 划转类型
                - UMFUTURE_MAIN: 合约→现货
                - MAIN_UMFUTURE: 现货→合约
                - 或使用 'ALL' 查询所有类型（需多次调用）
            start_time: 开始时间戳(毫秒)
            end_time: 结束时间戳(毫秒)
            limit: 返回数量
        """
        # 如果是ALL，则查询所有类型并合并
        if transfer_type == 'ALL':
            all_types = ['UMFUTURE_MAIN', 'MAIN_UMFUTURE', 'CMFUTURE_MAIN', 'MAIN_CMFUTURE']
            all_results = []

            for t_type in all_types:
                try:
                    params = {
                        'type': t_type,
                        'size': limit
                    }
                    if start_time:
                        params['startTime'] = start_time
                    if end_time:
                        params['endTime'] = end_time

                    result = self._request('GET', '/sapi/v1/asset/transfer', params=params, signed=True)
                    if result.get('rows'):
                        all_results.extend(result['rows'])
                except:
                    continue

            return {'total': len(all_results), 'rows': all_results}

        # 单个类型查询
        params = {
            'type': transfer_type,
            'size': limit
        }

        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

        return self._request('GET', '/sapi/v1/asset/transfer', params=params, signed=True)
