#!/usr/bin/env python3
"""
Alpha Arena 数据备份管理器 (V3.4)
提供自动备份、恢复和归档功能
"""

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupManager:
    """数据备份管理器"""

    def __init__(self, backup_dir: str = 'backups'):
        """
        初始化备份管理器

        Args:
            backup_dir: 备份目录路径
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # 需要备份的文件列表
        self.backup_files = [
            'performance_data.json',
            'ai_decisions.json',
            'roll_state.json',
            'runtime_state.json'
        ]

    def create_backup(self, files: Optional[List[str]] = None) -> Dict:
        """
        创建备份

        Args:
            files: 要备份的文件列表（默认备份所有）

        Returns:
            备份信息字典
        """
        files = files or self.backup_files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_info = {
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'files': [],
            'success': [],
            'failed': []
        }

        for filename in files:
            if not Path(filename).exists():
                logger.warning(f"文件不存在，跳过: {filename}")
                backup_info['failed'].append(filename)
                continue

            try:
                # 备份文件命名: 原文件名_时间戳.json
                backup_name = f"{Path(filename).stem}_{timestamp}{Path(filename).suffix}"
                backup_path = self.backup_dir / backup_name

                shutil.copy2(filename, backup_path)

                file_size = backup_path.stat().st_size
                backup_info['files'].append({
                    'original': filename,
                    'backup': str(backup_path),
                    'size': file_size
                })
                backup_info['success'].append(filename)

                logger.info(f"✅ 备份成功: {filename} → {backup_path} ({file_size} bytes)")

            except Exception as e:
                logger.error(f"❌ 备份失败: {filename} - {e}")
                backup_info['failed'].append(filename)

        # 保存备份清单
        manifest_path = self.backup_dir / f"manifest_{timestamp}.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)

        return backup_info

    def list_backups(self, file_pattern: Optional[str] = None) -> List[Dict]:
        """
        列出所有备份

        Args:
            file_pattern: 文件名模式过滤（例如 "performance_data"）

        Returns:
            备份文件列表
        """
        backups = []

        for backup_file in self.backup_dir.glob('*.json'):
            if backup_file.name.startswith('manifest_'):
                continue  # 跳过清单文件

            if file_pattern and file_pattern not in backup_file.name:
                continue

            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        # 按创建时间倒序排序
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups

    def restore_backup(self, backup_filename: str, target_file: Optional[str] = None) -> bool:
        """
        恢复备份

        Args:
            backup_filename: 备份文件名
            target_file: 目标文件路径（默认恢复到原文件名）

        Returns:
            是否恢复成功
        """
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_path}")
            return False

        # 推断原始文件名
        if target_file is None:
            # 从备份文件名提取: performance_data_20251024_143000.json → performance_data.json
            parts = backup_filename.rsplit('_', 2)  # 从右边分割2次
            if len(parts) >= 2:
                target_file = f"{parts[0]}.json"
            else:
                logger.error(f"无法推断目标文件名: {backup_filename}")
                return False

        try:
            # 如果目标文件存在，先备份
            if Path(target_file).exists():
                temp_backup = f"{target_file}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_file, temp_backup)
                logger.info(f"📦 已备份当前文件: {temp_backup}")

            # 恢复备份
            shutil.copy2(backup_path, target_file)
            logger.info(f"✅ 恢复成功: {backup_path} → {target_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 恢复失败: {e}")
            return False

    def cleanup_old_backups(self, keep_days: int = 7, keep_count: int = 20) -> Dict:
        """
        清理旧备份

        Args:
            keep_days: 保留最近N天的备份
            keep_count: 至少保留N个备份

        Returns:
            清理统计信息
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        backups = self.list_backups()
        deleted = []
        kept = []

        # 按文件类型分组
        by_type = {}
        for backup in backups:
            # 提取文件类型（例如 "performance_data"）
            file_type = backup['filename'].rsplit('_', 2)[0]
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(backup)

        # 对每种文件类型单独处理
        for file_type, type_backups in by_type.items():
            # 保留最近的keep_count个
            for i, backup in enumerate(type_backups):
                if i < keep_count:
                    kept.append(backup['filename'])
                    continue

                # 检查日期
                backup_date = datetime.fromisoformat(backup['created'])
                if backup_date < cutoff_date:
                    try:
                        Path(backup['path']).unlink()
                        deleted.append(backup['filename'])
                        logger.info(f"🗑️  删除旧备份: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"删除失败: {backup['filename']} - {e}")
                else:
                    kept.append(backup['filename'])

        return {
            'deleted': deleted,
            'deleted_count': len(deleted),
            'kept': kept,
            'kept_count': len(kept)
        }

    def get_backup_stats(self) -> Dict:
        """获取备份统计信息"""
        backups = self.list_backups()

        total_size = sum(b['size'] for b in backups)
        by_type = {}

        for backup in backups:
            file_type = backup['filename'].rsplit('_', 2)[0]
            if file_type not in by_type:
                by_type[file_type] = {'count': 0, 'size': 0}
            by_type[file_type]['count'] += 1
            by_type[file_type]['size'] += backup['size']

        return {
            'total_backups': len(backups),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'by_type': by_type,
            'latest': backups[0] if backups else None
        }


def main():
    """命令行接口"""
    import sys

    manager = BackupManager()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python backup_manager.py backup           # 创建新备份")
        print("  python backup_manager.py list              # 列出所有备份")
        print("  python backup_manager.py restore <file>    # 恢复备份")
        print("  python backup_manager.py cleanup           # 清理旧备份")
        print("  python backup_manager.py stats             # 显示统计信息")
        return

    command = sys.argv[1]

    if command == 'backup':
        info = manager.create_backup()
        print(f"\n✅ 备份完成！")
        print(f"成功: {len(info['success'])} 个文件")
        print(f"失败: {len(info['failed'])} 个文件")
        if info['failed']:
            print(f"失败文件: {', '.join(info['failed'])}")

    elif command == 'list':
        backups = manager.list_backups()
        if not backups:
            print("没有找到备份文件")
            return

        print(f"\n📦 找到 {len(backups)} 个备份:")
        print("-" * 80)
        for backup in backups:
            size_kb = backup['size'] / 1024
            print(f"{backup['filename']:<50} {size_kb:>8.2f} KB  {backup['created']}")

    elif command == 'restore' and len(sys.argv) > 2:
        filename = sys.argv[2]
        success = manager.restore_backup(filename)
        if success:
            print(f"✅ 恢复成功: {filename}")
        else:
            print(f"❌ 恢复失败: {filename}")

    elif command == 'cleanup':
        result = manager.cleanup_old_backups()
        print(f"\n🗑️  清理完成:")
        print(f"删除: {result['deleted_count']} 个备份")
        print(f"保留: {result['kept_count']} 个备份")

    elif command == 'stats':
        stats = manager.get_backup_stats()
        print(f"\n📊 备份统计:")
        print(f"总备份数: {stats['total_backups']}")
        print(f"总大小: {stats['total_size_mb']:.2f} MB")
        print(f"\n按类型统计:")
        for file_type, data in stats['by_type'].items():
            print(f"  {file_type}: {data['count']} 个备份, {data['size']/1024:.2f} KB")

        if stats['latest']:
            print(f"\n最新备份:")
            print(f"  {stats['latest']['filename']}")
            print(f"  创建时间: {stats['latest']['created']}")

    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()
