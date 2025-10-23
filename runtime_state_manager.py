#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行状态管理器
负责持久化和管理交易机器人的运行状态
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

class RuntimeStateManager:
    """运行状态管理器"""

    def __init__(self, state_file: str = "runtime_state.json"):
        """
        初始化运行状态管理器

        Args:
            state_file: 状态文件路径
        """
        self.state_file = state_file
        self.state = self._load_or_initialize()

    def _load_or_initialize(self) -> Dict[str, Any]:
        """加载或初始化状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    logger.info(f"[OK] 加载运行状态: 已运行 {state['total_runtime_minutes']} 分钟, {state['total_ai_calls']} 次AI调用")
                    return state
            except Exception as e:
                logger.error(f"[ERROR] 加载状态文件失败: {e}, 将创建新状态")

        # 初始化新状态
        initial_state = {
            "start_timestamp": datetime.now().isoformat(),
            "last_update_timestamp": datetime.now().isoformat(),
            "total_runtime_minutes": 0,
            "total_ai_calls": 0,
            "total_trading_loops": 0,
            "session_start_time": datetime.now().isoformat(),
            "metadata": {
                "version": "2.0",
                "description": "Alpha Arena Trading Bot Runtime State"
            }
        }

        self._save(initial_state)
        logger.info("[NEW] 创建新的运行状态文件")
        return initial_state

    def _save(self, state: Dict[str, Any] = None):
        """保存状态到文件"""
        if state is None:
            state = self.state

        try:
            # 更新最后保存时间
            state['last_update_timestamp'] = datetime.now().isoformat()

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[ERROR] 保存状态文件失败: {e}")

    def increment_ai_calls(self):
        """增加AI调用计数"""
        self.state['total_ai_calls'] += 1
        self._save()

    def increment_trading_loops(self):
        """增加交易循环计数"""
        self.state['total_trading_loops'] += 1
        self._save()

    def update_runtime(self):
        """更新运行时长（分钟）"""
        start_time = datetime.fromisoformat(self.state['session_start_time'])
        current_time = datetime.now()
        runtime_minutes = int((current_time - start_time).total_seconds() / 60)

        self.state['total_runtime_minutes'] = runtime_minutes
        self._save()

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state.copy()

    def get_runtime_summary(self) -> str:
        """获取运行时长摘要（格式化字符串）"""
        minutes = self.state['total_runtime_minutes']
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours > 0:
            return f"{hours}小时{remaining_minutes}分钟"
        else:
            return f"{remaining_minutes}分钟"

    def reset_session(self):
        """重置会话（保留历史总计，但重新开始计时）"""
        logger.info("[LOOP] 重置会话状态")
        self.state['session_start_time'] = datetime.now().isoformat()
        self.state['total_runtime_minutes'] = 0
        self._save()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    manager = RuntimeStateManager()
    print("当前状态:", manager.get_state())

    # 模拟一些操作
    manager.increment_ai_calls()
    manager.increment_trading_loops()
    manager.update_runtime()

    print("更新后状态:", manager.get_state())
    print("运行时长:", manager.get_runtime_summary())
