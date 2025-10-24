#!/usr/bin/env python3
"""
Alpha Arena Web 仪表板
实时查看交易表现 - 直接从 Binance API 获取实时数据
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import threading
import time

# 导入 Binance 客户端
from binance_client import BinanceClient
from performance_tracker import PerformanceTracker
from risk_manager import RiskManager

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'alpha-arena-secret-key-2025'

# 初始化 SocketIO（支持 WebSocket 实时推送）
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 初始化 Binance 客户端（全局单例）
binance_client = None
performance_tracker = None
risk_manager = None

def init_clients():
    """初始化客户端（延迟加载）"""
    global binance_client, performance_tracker, risk_manager

    if binance_client is None:
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'

        binance_client = BinanceClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )

    if performance_tracker is None:
        # [NEW] 从Binance API获取实际余额，替代配置文件
        try:
            initial_capital = binance_client.get_futures_usdt_balance()
            print(f"[OK] Web仪表板: 从Binance API获取实际余额: ${initial_capital:,.2f}")
        except Exception as e:
            print(f"[WARNING] 无法获取Binance余额，使用配置文件默认值: {e}")
            initial_capital = float(os.getenv('INITIAL_CAPITAL', 10000))

        performance_tracker = PerformanceTracker(
            initial_capital=initial_capital,
            data_file='performance_data.json'
        )

    if risk_manager is None:
        # 初始化风险管理器
        risk_config = {
            'max_portfolio_risk': 0.02,
            'max_position_size': 0.1,
            'max_leverage': 10,
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_open_positions': 10
        }
        risk_manager = RiskManager(risk_config)


@app.route('/')
def index():
    """主页"""
    return render_template('dashboard.html')


@app.route('/api/performance')
def get_performance():
    """获取性能数据 API - 实时从 Binance 获取"""
    try:
        # 初始化客户端
        init_clients()

        # 直接从Binance获取合约账户信息
        account_info = binance_client.get_futures_account_info()

        # 获取合约账户总资产
        total_wallet_balance = float(account_info.get('totalWalletBalance', 0))  # 钱包余额（实际资金）
        total_unrealized_pnl = float(account_info.get('totalUnrealizedProfit', 0))  # 未实现盈亏
        total_margin_balance = float(account_info.get('totalMarginBalance', 0))  # 保证金余额 = 钱包余额 + 未实现盈亏

        # 账户价值 = 保证金余额（钱包余额 + 未实现盈亏）= 真实总价值
        account_value = total_margin_balance

        # 实时获取持仓
        positions = binance_client.get_active_positions()

        # 实时计算性能指标
        metrics = performance_tracker.calculate_metrics(total_wallet_balance, positions)

        return jsonify({
            'success': True,
            'data': {
                'model': 'DeepSeek-V3',
                'account_value': round(account_value, 2),
                'wallet_balance': round(total_wallet_balance, 2),
                'total_return_pct': metrics.get('total_return_pct', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                'win_rate_pct': metrics.get('win_rate_pct', 0),
                'total_trades': metrics.get('total_trades', 0),
                'open_positions': len(positions),
                'unrealized_pnl': round(total_unrealized_pnl, 2),
                'realized_pnl': metrics.get('realized_pnl', 0),
                'fees_paid': metrics.get('fees_paid', 0),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'timestamp': datetime.now().timestamp()  # 添加时间戳用于前端判断更新
            }
        })

    except Exception as e:
        # 如果 API 调用失败，回退到从文件读取
        try:
            with open('performance_data.json', 'r') as f:
                data = json.load(f)
            metrics = data.get('metrics', {})

            return jsonify({
                'success': True,
                'data': {
                    'model': 'DeepSeek-V3',
                    'account_value': metrics.get('account_value', 10000),
                    'wallet_balance': metrics.get('wallet_balance', 10000),
                    'total_return_pct': metrics.get('total_return_pct', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                    'win_rate_pct': metrics.get('win_rate_pct', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'open_positions': metrics.get('open_positions', 0),
                    'unrealized_pnl': metrics.get('unrealized_pnl', 0),
                    'realized_pnl': metrics.get('realized_pnl', 0),
                    'fees_paid': metrics.get('fees_paid', 0),
                    'last_update': metrics.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]),
                    'timestamp': datetime.now().timestamp(),
                    'fallback': True  # 标记为回退模式
                }
            })
        except:
            return jsonify({
                'success': False,
                'error': f'获取数据失败: {str(e)}'
            })


@app.route('/api/trades')
def get_trades():
    """获取交易历史 API"""
    try:
        with open('performance_data.json', 'r') as f:
            data = json.load(f)

        trades = data.get('trades', [])

        # 返回最近 200 笔交易（支持更多翻页）
        return jsonify({
            'success': True,
            'data': trades[-200:]
        })

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': '数据文件不存在'
        })


@app.route('/api/chart')
def get_chart_data():
    """获取图表数据 API"""
    try:
        with open('performance_data.json', 'r') as f:
            data = json.load(f)

        portfolio_values = data.get('portfolio_values', [])

        # 返回最近 500 个数据点
        return jsonify({
            'success': True,
            'data': portfolio_values[-500:]
        })

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': '数据文件不存在'
        })


@app.route('/api/system_status')
def get_system_status():
    """获取系统运行状态 API"""
    try:
        # 读取runtime_state.json
        with open('runtime_state.json', 'r') as f:
            runtime_state = json.load(f)

        # 格式化运行时间
        runtime_minutes = runtime_state.get('total_runtime_minutes', 0)
        if runtime_minutes >= 60:
            runtime_display = f"{runtime_minutes // 60}小时{runtime_minutes % 60}分"
        else:
            runtime_display = f"{runtime_minutes}分钟"

        return jsonify({
            'success': True,
            'data': {
                'runtime_minutes': runtime_minutes,
                'runtime_display': runtime_display,
                'ai_calls': runtime_state.get('total_ai_calls', 0),
                'trading_loops': runtime_state.get('total_trading_loops', 0),
                'session_start': runtime_state.get('session_start_time', ''),
                'last_update': runtime_state.get('last_update_timestamp', datetime.now().isoformat())
            }
        })

    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': '运行状态文件不存在',
            'data': {
                'runtime_minutes': 0,
                'runtime_display': '0分钟',
                'ai_calls': 0,
                'trading_loops': 0,
                'session_start': '',
                'last_update': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取系统状态失败: {str(e)}'
        })


@app.route('/api/positions')
def get_positions():
    """获取当前持仓 API - 实时从 Binance 获取"""
    try:
        # 初始化客户端
        init_clients()

        # 直接从 Binance 获取实时持仓数据
        raw_positions = binance_client.get_futures_positions()

        positions_list = []

        for pos in raw_positions:
            position_amt = float(pos.get('positionAmt', 0))

            # 只返回非零持仓
            if position_amt != 0:
                symbol = pos['symbol']
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                leverage = int(pos.get('leverage', 1))

                # 计算名义价值
                notional = abs(position_amt) * entry_price

                # 计算盈亏百分比
                pnl_pct = (unrealized_pnl / notional * 100) if notional > 0 else 0

                # 判断持仓方向
                side = 'LONG' if position_amt > 0 else 'SHORT'
                side_cn = '多单' if position_amt > 0 else '空单'

                positions_list.append({
                    'symbol': symbol,
                    'side': side,
                    'side_cn': side_cn,
                    'quantity': abs(position_amt),
                    'leverage': leverage,
                    'entry_price': entry_price,
                    'current_price': mark_price,
                    'pnl_usd': unrealized_pnl,
                    'pnl_pct': pnl_pct,
                    'notional': notional,
                    'timestamp': datetime.now().timestamp()  # 添加时间戳
                })

        return jsonify({
            'success': True,
            'data': positions_list,
            'count': len(positions_list),
            'timestamp': datetime.now().timestamp()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取持仓失败: {str(e)}',
            'data': []
        })


@app.route('/api/decisions')
def get_ai_decisions():
    """获取AI决策 API - 从ai_decisions.json读取结构化数据 (V3.5修复)"""
    try:
        decisions_file = 'ai_decisions.json'

        if not os.path.exists(decisions_file):
            return jsonify({'success': True, 'data': []})

        # 直接从结构化JSON读取
        with open(decisions_file, 'r', encoding='utf-8') as f:
            all_decisions = json.load(f)

        # 只返回最近20条,格式化为前端需要的结构
        recent = all_decisions[-20:] if len(all_decisions) > 20 else all_decisions

        formatted = []
        for d in recent:
            decision_data = d.get('decision', {})

            # 提取核心字段
            formatted_decision = {
                'time': d.get('timestamp', ''),
                'symbol': decision_data.get('symbol', 'N/A'),
                'action': decision_data.get('action', 'HOLD'),
                'confidence': decision_data.get('confidence', 0),
                'reasoning': decision_data.get('reasoning', '')[:300],  # 截断过长的理由
                'model_used': 'deepseek-chat',
                'leverage': decision_data.get('leverage', 1),
                'position_size': decision_data.get('position_size', 0),
                'executed': decision_data.get('executed', False)
            }

            formatted.append(formatted_decision)

        return jsonify({
            'success': True,
            'data': formatted
        })

    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'JSON解析错误: {str(e)}',
            'data': []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        })


@app.route('/api/liquidation_warnings')
def get_liquidation_warnings():
    """获取清算风险预警 API"""
    try:
        # 初始化客户端
        init_clients()

        # 获取当前持仓
        positions = binance_client.get_active_positions()

        # 检查清算风险
        warnings = risk_manager.check_liquidation_risk(
            positions,
            liquidation_threshold=0.03  # 3% 预警阈值
        )

        return jsonify({
            'success': True,
            'data': {
                'warnings': warnings,
                'count': len(warnings),
                'has_critical': any(w['risk_level'] == 'CRITICAL' for w in warnings),
                'last_check': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'warnings': [],
                'count': 0,
                'has_critical': False
            }
        })


# ==================== WebSocket 事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'⚡ 客户端已连接: {id}')
    emit('connection_response', {'status': 'connected', 'message': 'WebSocket 已连接'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'[ERROR] 客户端已断开')


# 后台推送线程：每500ms推送一次实时数据（延迟<100ms感知）
def background_push_thread():
    """后台线程：实时推送数据到所有连接的客户端"""
    while True:
        try:
            # 初始化客户端
            init_clients()

            # 直接从Binance获取合约账户信息
            account_info = binance_client.get_futures_account_info()

            # 获取合约账户总资产
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))  # 钱包余额（实际资金）
            total_unrealized_pnl = float(account_info.get('totalUnrealizedProfit', 0))  # 未实现盈亏
            total_margin_balance = float(account_info.get('totalMarginBalance', 0))  # 保证金余额 = 钱包余额 + 未实现盈亏

            # 账户价值 = 保证金余额（钱包余额 + 未实现盈亏）= 真实总价值
            account_value = total_margin_balance

            # 实时获取持仓
            positions = binance_client.get_active_positions()

            # 计算性能指标
            metrics = performance_tracker.calculate_metrics(total_wallet_balance, positions)

            # 推送性能数据
            socketio.emit('performance_update', {
                'success': True,
                'data': {
                    'account_value': round(account_value, 2),
                    'wallet_balance': round(total_wallet_balance, 2),
                    'total_return_pct': metrics.get('total_return_pct', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
                    'win_rate_pct': metrics.get('win_rate_pct', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'open_positions': len(positions),
                    'unrealized_pnl': round(total_unrealized_pnl, 2),
                    'realized_pnl': metrics.get('realized_pnl', 0),
                    'timestamp': datetime.now().timestamp()
                }
            })

            # 推送持仓数据
            raw_positions = binance_client.get_futures_positions()
            positions_list = []

            for pos in raw_positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    symbol = pos['symbol']
                    entry_price = float(pos.get('entryPrice', 0))
                    mark_price = float(pos.get('markPrice', 0))
                    unrealized_pnl_pos = float(pos.get('unRealizedProfit', 0))
                    leverage = int(pos.get('leverage', 1))

                    notional = abs(position_amt) * entry_price
                    pnl_pct = (unrealized_pnl_pos / notional * 100) if notional > 0 else 0

                    side = 'LONG' if position_amt > 0 else 'SHORT'
                    side_cn = '多单' if position_amt > 0 else '空单'

                    positions_list.append({
                        'symbol': symbol,
                        'side': side,
                        'side_cn': side_cn,
                        'quantity': abs(position_amt),
                        'leverage': leverage,
                        'entry_price': entry_price,
                        'current_price': mark_price,
                        'pnl_usd': unrealized_pnl_pos,
                        'pnl_pct': pnl_pct,
                        'notional': notional
                    })

            socketio.emit('positions_update', {
                'success': True,
                'data': positions_list,
                'timestamp': datetime.now().timestamp()
            })

        except Exception as e:
            print(f"[WARNING]  推送数据错误: {e}")

        # 每500ms推送一次（感知延迟<100ms）
        time.sleep(0.5)


if __name__ == '__main__':
    # 创建 templates 目录
    os.makedirs('templates', exist_ok=True)

    print("[WEB] 启动 Web 仪表板...")
    print("[ANALYZE] 访问: http://localhost:5001")
    print("⚡ WebSocket 实时推送已启用（延迟 <100ms）")

    # 启动后台推送线程
    push_thread = threading.Thread(target=background_push_thread, daemon=True)
    push_thread.start()

    # 使用 SocketIO 启动（而非 app.run）
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
