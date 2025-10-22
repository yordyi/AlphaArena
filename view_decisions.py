#!/usr/bin/env python3
"""
AI决策卡片查看器 - 兼容新旧格式
"""
import json
from datetime import datetime

def format_timestamp(iso_str: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%m/%d %H:%M:%S")
    except:
        return iso_str

def display_decision_card(decision: dict, index: int):
    """展示单个决策卡片 - 兼容新旧格式"""
    print("\n" + "="*70)
    
    # 时间戳
    ts = format_timestamp(decision.get('timestamp', ''))
    cycle = decision.get('cycle', index + 1)
    print(f"⏰ {ts} | Cycle #{cycle}")
    print("="*70)
    
    # 账户快照（新格式）
    if 'account_snapshot' in decision:
        snapshot = decision['account_snapshot']
        print(f"\n💼 账户状态:")
        print(f"  总价值: ${snapshot.get('total_value', 0):.2f}")
        print(f"  现金: ${snapshot.get('cash_balance', 0):.2f}")
        print(f"  收益率: {snapshot.get('total_return_pct', 0):+.2f}%")
        print(f"  持仓数: {snapshot.get('positions_count', 0)}")
    
    # 交易时段（新格式）
    if 'session_info' in decision:
        session = decision['session_info']
        print(f"\n⏰ 时段: {session.get('session', 'N/A')} | 波动: {session.get('volatility', 'N/A').upper()}")
    
    # 决策详情（兼容新旧格式）
    if 'decision' in decision:
        # 新格式
        dec = decision['decision']
        symbol = dec.get('symbol', 'N/A')
        action = dec.get('action', 'HOLD')
        confidence = dec.get('confidence', 0)
        reasoning = dec.get('reasoning', '')
    else:
        # 旧格式
        symbol = decision.get('symbol', 'N/A')
        action = decision.get('action', 'HOLD')
        confidence = decision.get('confidence', 0)
        reasoning = decision.get('reasoning', '')
    
    action_emoji = {'OPEN_LONG': '🟢', 'OPEN_SHORT': '🔴', 'HOLD': '⏸️', 'CLOSE': '✂️'}.get(action, '❓')
    print(f"\n{action_emoji} 决策: {action} | {symbol}")
    print(f"  信心度: {confidence}%")
    if reasoning:
        print(f"  理由: {reasoning[:80]}...")
    
    # 持仓详情（新格式）
    if 'position_snapshot' in decision and decision['position_snapshot']:
        pos = decision['position_snapshot']
        dir_emoji = '🟢' if pos.get('direction') == 'LONG' else '🔴'
        print(f"\n💼 持仓: {dir_emoji} {pos.get('direction')} {pos.get('leverage')}x")
        print(f"  盈亏: {pos.get('unrealized_pnl', 0):+.2f} ({pos.get('unrealized_pnl_pct', 0):+.2f}%)")

def main():
    """主函数"""
    try:
        with open('ai_decisions.json', 'r') as f:
            decisions = json.load(f)
        
        if not decisions:
            print("暂无AI决策记录")
            return
        
        # 显示最近5条
        recent = decisions[-5:]
        
        print("\n" + "🏆 ALPHA ARENA - AI决策历史".center(70, "="))
        print(f"总决策数: {len(decisions)}")
        
        for i, decision in enumerate(recent):
            display_decision_card(decision, len(decisions) - len(recent) + i)
        
        # 最新状态
        latest = decisions[-1]
        print("\n" + "="*70)
        if 'account_snapshot' in latest:
            snapshot = latest['account_snapshot']
            print(f"✨ 最新状态:")
            print(f"  账户价值: ${snapshot.get('total_value', 0):.2f}")
            print(f"  总收益率: {snapshot.get('total_return_pct', 0):+.2f}%")
            print(f"  持仓数: {snapshot.get('positions_count', 0)}")
        print("="*70)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
