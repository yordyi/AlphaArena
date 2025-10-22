#!/usr/bin/env python3
"""
日志管理系统
- 重置交易历史
- 归档旧数据
- 过滤测试数据
- 管理AI可见的历史范围
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LogManager:
    """日志管理器"""

    def __init__(self, data_dir: str = '.'):
        """
        初始化日志管理器

        Args:
            data_dir: 数据文件目录
        """
        self.data_dir = data_dir
        self.performance_file = os.path.join(data_dir, 'performance_data.json')
        self.decisions_file = os.path.join(data_dir, 'ai_decisions.json')
        self.archive_dir = os.path.join(data_dir, 'archives')
        self.config_file = os.path.join(data_dir, 'log_config.json')

        # 创建归档目录
        os.makedirs(self.archive_dir, exist_ok=True)

        # 加载配置
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载日志配置"""
        default_config = {
            'ai_reference_start_date': None,  # AI参考历史的起始日期 (YYYY-MM-DD)
            'min_trades_for_winrate': 20,  # 最少交易次数才显示胜率
            'production_mode': True,  # 是否为生产模式
            'testnet_mode': False,  # 是否为测试网模式
            'last_reset_date': None  # 上次重置日期
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception as e:
                logger.warning(f"加载配置失败，使用默认配置: {e}")

        return default_config

    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("✅ 配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def reset_all_data(self, backup: bool = True) -> bool:
        """
        重置所有交易数据

        Args:
            backup: 是否备份现有数据

        Returns:
            是否成功
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 备份现有数据
            if backup:
                logger.info("📦 备份现有数据...")
                backup_dir = os.path.join(self.archive_dir, f'backup_{timestamp}')
                os.makedirs(backup_dir, exist_ok=True)

                if os.path.exists(self.performance_file):
                    shutil.copy2(self.performance_file,
                               os.path.join(backup_dir, 'performance_data.json'))
                    logger.info(f"  ✅ performance_data.json → {backup_dir}")

                if os.path.exists(self.decisions_file):
                    shutil.copy2(self.decisions_file,
                               os.path.join(backup_dir, 'ai_decisions.json'))
                    logger.info(f"  ✅ ai_decisions.json → {backup_dir}")

            # 重置 performance_data.json
            initial_performance = {
                'initial_capital': 20.0,
                'current_capital': 20.0,
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'trade_history': [],
                'equity_curve': [],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.performance_file, 'w') as f:
                json.dump(initial_performance, f, indent=2)
            logger.info("✅ performance_data.json 已重置")

            # 重置 ai_decisions.json
            with open(self.decisions_file, 'w') as f:
                json.dump([], f, indent=2)
            logger.info("✅ ai_decisions.json 已重置")

            # 更新配置
            self.config['last_reset_date'] = timestamp
            self.config['ai_reference_start_date'] = datetime.now().strftime('%Y-%m-%d')
            self._save_config()

            logger.info("🎉 所有数据已重置，系统已准备好重新开始")
            return True

        except Exception as e:
            logger.error(f"❌ 重置数据失败: {e}")
            return False

    def set_ai_reference_date(self, date_str: str):
        """
        设置AI参考历史的起始日期

        Args:
            date_str: 日期字符串 (YYYY-MM-DD) 或 'now' 或 'none'
        """
        if date_str.lower() == 'now':
            self.config['ai_reference_start_date'] = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"✅ AI参考起始日期设置为: 今天 ({self.config['ai_reference_start_date']})")
        elif date_str.lower() == 'none':
            self.config['ai_reference_start_date'] = None
            logger.info("✅ AI将参考所有历史数据")
        else:
            # 验证日期格式
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                self.config['ai_reference_start_date'] = date_str
                logger.info(f"✅ AI参考起始日期设置为: {date_str}")
            except ValueError:
                logger.error("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
                return

        self._save_config()

    def set_min_trades_for_winrate(self, min_trades: int):
        """设置显示胜率的最小交易次数"""
        self.config['min_trades_for_winrate'] = max(0, min_trades)
        self._save_config()
        logger.info(f"✅ 最小交易次数阈值设置为: {min_trades}")

    def get_filtered_trade_history(self, trade_history: List[Dict]) -> List[Dict]:
        """
        获取过滤后的交易历史（AI可见部分）

        Args:
            trade_history: 完整交易历史

        Returns:
            过滤后的交易历史
        """
        if not self.config.get('ai_reference_start_date'):
            return trade_history

        try:
            start_date = datetime.strptime(self.config['ai_reference_start_date'], '%Y-%m-%d')

            filtered = []
            for trade in trade_history:
                trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
                if trade_time >= start_date:
                    filtered.append(trade)

            logger.debug(f"过滤交易历史: {len(trade_history)} → {len(filtered)} (起始日期: {self.config['ai_reference_start_date']})")
            return filtered

        except Exception as e:
            logger.warning(f"过滤交易历史失败: {e}，返回全部历史")
            return trade_history

    def should_show_winrate(self, trade_count: int) -> bool:
        """
        判断是否应该显示胜率

        Args:
            trade_count: 交易次数

        Returns:
            是否显示胜率
        """
        min_trades = self.config.get('min_trades_for_winrate', 20)
        return trade_count >= min_trades

    def archive_old_data(self, days_old: int = 30) -> bool:
        """
        归档旧数据

        Args:
            days_old: 归档多少天之前的数据

        Returns:
            是否成功
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            logger.info(f"📦 归档 {cutoff_date.strftime('%Y-%m-%d')} 之前的数据...")

            # 读取现有数据
            if not os.path.exists(self.performance_file):
                logger.warning("没有找到 performance_data.json")
                return False

            with open(self.performance_file, 'r') as f:
                data = json.load(f)

            trade_history = data.get('trade_history', [])

            # 分离新旧数据
            old_trades = []
            new_trades = []

            for trade in trade_history:
                trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
                if trade_time < cutoff_date:
                    old_trades.append(trade)
                else:
                    new_trades.append(trade)

            if not old_trades:
                logger.info("没有需要归档的旧数据")
                return True

            # 保存旧数据到归档
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = os.path.join(self.archive_dir, f'archived_trades_{timestamp}.json')

            with open(archive_file, 'w') as f:
                json.dump({
                    'archived_date': timestamp,
                    'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                    'trade_count': len(old_trades),
                    'trades': old_trades
                }, f, indent=2)

            logger.info(f"✅ {len(old_trades)} 笔旧交易已归档到: {archive_file}")

            # 更新 performance_data.json
            data['trade_history'] = new_trades
            data['last_updated'] = datetime.now().isoformat()

            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ performance_data.json 已更新，保留 {len(new_trades)} 笔最近交易")
            return True

        except Exception as e:
            logger.error(f"❌ 归档失败: {e}")
            return False

    def show_stats(self):
        """显示当前统计信息"""
        try:
            print("\n" + "=" * 60)
            print("📊 日志管理系统状态")
            print("=" * 60)

            # 配置信息
            print("\n🔧 当前配置:")
            print(f"  AI参考起始日期: {self.config.get('ai_reference_start_date', '全部历史')}")
            print(f"  显示胜率最小交易数: {self.config.get('min_trades_for_winrate', 20)}")
            print(f"  上次重置日期: {self.config.get('last_reset_date', '从未重置')}")
            print(f"  生产模式: {'是' if self.config.get('production_mode') else '否'}")

            # 交易数据统计
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)

                trade_history = data.get('trade_history', [])
                total_trades = len(trade_history)

                print(f"\n📈 交易数据:")
                print(f"  总交易次数: {total_trades}")
                print(f"  当前资金: ${data.get('current_capital', 0):.2f}")
                print(f"  总收益率: {data.get('total_return_pct', 0):.2f}%")
                print(f"  胜率: {data.get('win_rate', 0):.2f}%")

                if total_trades > 0:
                    first_trade = trade_history[0].get('timestamp', 'N/A')
                    last_trade = trade_history[-1].get('timestamp', 'N/A')
                    print(f"  最早交易: {first_trade}")
                    print(f"  最新交易: {last_trade}")

                # AI可见数据
                filtered_trades = self.get_filtered_trade_history(trade_history)
                print(f"\n🤖 AI可见数据:")
                print(f"  可见交易数: {len(filtered_trades)}")
                print(f"  是否显示胜率: {'是' if self.should_show_winrate(len(filtered_trades)) else '否（交易数太少）'}")
            else:
                print("\n⚠️  没有找到 performance_data.json")

            # 归档文件
            if os.path.exists(self.archive_dir):
                archives = [f for f in os.listdir(self.archive_dir) if f.endswith('.json')]
                print(f"\n📦 归档文件:")
                print(f"  归档数量: {len(archives)}")
                if archives:
                    for archive in sorted(archives)[-5:]:  # 显示最近5个
                        print(f"    - {archive}")

            print("\n" + "=" * 60)

        except Exception as e:
            logger.error(f"显示统计信息失败: {e}")


def main():
    """命令行主程序"""
    import sys

    manager = LogManager()

    if len(sys.argv) < 2:
        print("""
日志管理系统 - 使用方法:

  python3 log_manager.py stats              # 显示统计信息
  python3 log_manager.py reset              # 重置所有数据（会备份）
  python3 log_manager.py reset --no-backup  # 重置所有数据（不备份）
  python3 log_manager.py set-date now       # 设置AI参考起始日期为今天
  python3 log_manager.py set-date 2025-01-01  # 设置AI参考起始日期
  python3 log_manager.py set-date none      # AI参考所有历史
  python3 log_manager.py set-min-trades 10  # 设置最小交易数阈值
  python3 log_manager.py archive 30         # 归档30天前的数据

示例工作流:
  1. 开发阶段结束，准备正式运行:
     python3 log_manager.py reset

  2. 只想让AI看今天之后的数据:
     python3 log_manager.py set-date now

  3. 交易次数少时不显示胜率（避免误导AI）:
     python3 log_manager.py set-min-trades 20
        """)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'stats':
        manager.show_stats()

    elif command == 'reset':
        backup = '--no-backup' not in sys.argv
        print(f"\n⚠️  即将重置所有交易数据{'（会备份）' if backup else '（不备份）'}")
        confirm = input("确认执行？(yes/no): ")
        if confirm.lower() == 'yes':
            manager.reset_all_data(backup=backup)
        else:
            print("已取消")

    elif command == 'set-date':
        if len(sys.argv) < 3:
            print("❌ 请提供日期参数: now / YYYY-MM-DD / none")
            sys.exit(1)
        manager.set_ai_reference_date(sys.argv[2])

    elif command == 'set-min-trades':
        if len(sys.argv) < 3:
            print("❌ 请提供交易数参数")
            sys.exit(1)
        try:
            min_trades = int(sys.argv[2])
            manager.set_min_trades_for_winrate(min_trades)
        except ValueError:
            print("❌ 交易数必须是整数")
            sys.exit(1)

    elif command == 'archive':
        days = 30
        if len(sys.argv) >= 3:
            try:
                days = int(sys.argv[2])
            except ValueError:
                print("❌ 天数必须是整数")
                sys.exit(1)
        manager.archive_old_data(days)

    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python3 log_manager.py' 查看帮助")
        sys.exit(1)


if __name__ == '__main__':
    main()
