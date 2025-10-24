#!/usr/bin/env python3
"""
系统健康监控脚本
实时监控Alpha Arena交易机器人和Dashboard的运行状态
"""

import time
import requests
import json
import subprocess
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """系统健康监控器"""

    def __init__(self):
        self.bot_process_name = "alpha_arena_bot.py"
        self.dashboard_process_name = "web_dashboard.py"
        self.dashboard_url = "http://localhost:5001"  # [V3.3] 修复端口配置
        self.performance_file = "performance_data.json"
        self.roll_state_file = "roll_state.json"

    def check_process_running(self, process_name: str) -> Dict:
        """检查进程是否运行"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            lines = [line for line in result.stdout.split('\n') if process_name in line and 'grep' not in line]

            if lines:
                # 计算CPU和内存使用
                processes = []
                for line in lines:
                    parts = line.split()
                    processes.append({
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'status': 'running'
                    })

                return {
                    'running': True,
                    'count': len(processes),
                    'processes': processes
                }
            else:
                return {
                    'running': False,
                    'count': 0,
                    'processes': []
                }
        except Exception as e:
            logger.error(f"检查进程失败: {e}")
            return {'running': False, 'error': str(e)}

    def check_dashboard_health(self) -> Dict:
        """检查Dashboard健康状态"""
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            return {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except requests.exceptions.ConnectionError:
            return {'accessible': False, 'error': 'Connection refused'}
        except requests.exceptions.Timeout:
            return {'accessible': False, 'error': 'Timeout'}
        except Exception as e:
            return {'accessible': False, 'error': str(e)}

    def check_performance_data(self) -> Dict:
        """检查性能数据文件"""
        try:
            with open(self.performance_file, 'r') as f:
                data = json.load(f)

            total_trades = len(data.get('trade_history', []))
            total_return = data.get('total_return_pct', 0)
            win_rate = data.get('win_rate', 0)
            sharpe_ratio = data.get('sharpe_ratio', 0)

            return {
                'accessible': True,
                'total_trades': total_trades,
                'total_return': f"{total_return:.2f}%",
                'win_rate': f"{win_rate:.1f}%",
                'sharpe_ratio': f"{sharpe_ratio:.2f}" if sharpe_ratio else "N/A"
            }
        except FileNotFoundError:
            return {'accessible': False, 'error': 'File not found'}
        except json.JSONDecodeError:
            return {'accessible': False, 'error': 'Invalid JSON'}
        except Exception as e:
            return {'accessible': False, 'error': str(e)}

    def check_roll_tracker(self) -> Dict:
        """检查ROLL追踪器状态"""
        try:
            with open(self.roll_state_file, 'r') as f:
                data = json.load(f)

            total_symbols = len(data)
            total_rolls = sum(s.get('roll_count', 0) for s in data.values())
            symbols_at_max = sum(1 for s in data.values() if s.get('roll_count', 0) >= 6)

            return {
                'accessible': True,
                'total_symbols': total_symbols,
                'total_rolls': total_rolls,
                'symbols_at_max_rolls': symbols_at_max
            }
        except FileNotFoundError:
            return {'accessible': True, 'total_symbols': 0, 'total_rolls': 0}
        except Exception as e:
            return {'accessible': False, 'error': str(e)}

    def check_log_errors(self, log_file: str = None, lines: int = 100) -> Dict:
        """检查最近日志中的错误"""
        if not log_file:
            # 查找最新日志文件
            import glob
            logs = glob.glob('logs/alpha_arena_*.log')
            if not logs:
                return {'errors': 0, 'warnings': 0}
            log_file = max(logs, key=lambda x: x.split('_')[-1])

        try:
            with open(log_file, 'r') as f:
                recent_lines = f.readlines()[-lines:]

            errors = sum(1 for line in recent_lines if 'ERROR' in line)
            warnings = sum(1 for line in recent_lines if 'WARNING' in line or 'RETRY' in line)

            return {
                'errors': errors,
                'warnings': warnings,
                'log_file': log_file
            }
        except Exception as e:
            return {'error': str(e)}

    def get_full_health_report(self) -> Dict:
        """获取完整健康报告"""
        bot_status = self.check_process_running(self.bot_process_name)
        dashboard_status = self.check_process_running(self.dashboard_process_name)
        dashboard_health = self.check_dashboard_health()
        performance = self.check_performance_data()
        roll_tracker = self.check_roll_tracker()
        log_status = self.check_log_errors()

        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'components': {
                'trading_bot': bot_status,
                'dashboard_process': dashboard_status,
                'dashboard_web': dashboard_health,
                'performance_tracker': performance,
                'roll_tracker': roll_tracker,
                'logs': log_status
            }
        }

        # 判断整体健康状态
        if not bot_status.get('running'):
            report['overall_status'] = 'CRITICAL'
        elif bot_status.get('count', 0) > 1:
            report['overall_status'] = 'WARNING'  # 多个实例
        elif log_status.get('errors', 0) > 5:
            report['overall_status'] = 'DEGRADED'  # 错误过多

        return report

    def print_health_report(self):
        """打印可读的健康报告"""
        report = self.get_full_health_report()

        print("\n" + "="*60)
        print("🏥 Alpha Arena 系统健康报告")
        print("="*60)
        print(f"时间: {report['timestamp']}")
        print(f"总体状态: {report['overall_status']}")
        print()

        # 交易机器人
        bot = report['components']['trading_bot']
        if bot.get('running'):
            print(f"✅ 交易机器人: 运行中 ({bot.get('count')}个进程)")
            for p in bot.get('processes', [])[:1]:  # 只显示第一个
                print(f"   PID: {p['pid']} | CPU: {p['cpu']}% | MEM: {p['mem']}%")
        else:
            print(f"❌ 交易机器人: 未运行")

        # Dashboard
        dash_proc = report['components']['dashboard_process']
        dash_web = report['components']['dashboard_web']
        if dash_proc.get('running'):
            print(f"✅ Dashboard进程: 运行中")
        else:
            print(f"❌ Dashboard进程: 未运行")

        if dash_web.get('accessible'):
            print(f"✅ Dashboard网页: 可访问 (响应时间: {dash_web.get('response_time'):.2f}s)")
        else:
            print(f"❌ Dashboard网页: 不可访问 ({dash_web.get('error', '未知错误')})")

        # 性能数据
        perf = report['components']['performance_tracker']
        if perf.get('accessible'):
            print(f"\n📊 性能统计:")
            print(f"   总交易次数: {perf.get('total_trades')}")
            print(f"   总收益率: {perf.get('total_return')}")
            print(f"   胜率: {perf.get('win_rate')}")
            print(f"   夏普比率: {perf.get('sharpe_ratio')}")

        # ROLL追踪
        roll = report['components']['roll_tracker']
        if roll.get('accessible') and roll.get('total_symbols', 0) > 0:
            print(f"\n🔄 ROLL状态:")
            print(f"   活跃Symbol: {roll.get('total_symbols')}")
            print(f"   总ROLL次数: {roll.get('total_rolls')}")
            print(f"   达到6次限制: {roll.get('symbols_at_max_rolls')}")

        # 日志状态
        logs = report['components']['logs']
        if not logs.get('error'):
            print(f"\n📝 最近日志 (100行):")
            print(f"   错误: {logs.get('errors')} | 警告: {logs.get('warnings')}")

        print("\n" + "="*60 + "\n")

        return report


if __name__ == "__main__":
    monitor = HealthMonitor()

    # 持续监控模式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--watch':
        print("启动持续监控模式 (按Ctrl+C退出)")
        try:
            while True:
                monitor.print_health_report()
                time.sleep(60)  # 每60秒更新一次
        except KeyboardInterrupt:
            print("\n监控已停止")
    else:
        # 单次检查
        monitor.print_health_report()
