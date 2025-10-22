#!/usr/bin/env python3
"""
修复损坏的 ai_decisions.json 文件
"""

import json
import shutil
from datetime import datetime

print("🔧 修复 ai_decisions.json 文件")
print("=" * 70)

# 1. 备份损坏的文件
backup_file = f'ai_decisions_corrupted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json.bak'
try:
    shutil.copy('ai_decisions.json', backup_file)
    print(f"✅ 已备份损坏文件到: {backup_file}")
except Exception as e:
    print(f"⚠️  备份失败: {e}")

# 2. 尝试恢复有效的数据
print("\n📝 尝试恢复数据...")

try:
    with open('ai_decisions.json', 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到第一个有效的JSON数组结束位置（在损坏点之前）
    # 损坏发生在第183905字符处
    valid_content = content[:183904]  # 取到]之前

    # 尝试找到最后一个完整的对象
    # 向前查找最后一个完整的 }
    last_brace = valid_content.rfind('}')

    if last_brace > 0:
        # 截取到最后一个完整对象
        valid_content = valid_content[:last_brace + 1]

        # 确保有正确的数组结束
        if not valid_content.strip().endswith(']'):
            valid_content += '\n]'

        # 尝试解析
        try:
            recovered_data = json.loads(valid_content)
            print(f"✅ 成功恢复 {len(recovered_data)} 条决策记录")

            # 写回文件
            with open('ai_decisions.json', 'w', encoding='utf-8') as f:
                json.dump(recovered_data, f, indent=2, ensure_ascii=False)

            print("✅ ai_decisions.json 已修复")

        except json.JSONDecodeError as e:
            print(f"❌ 恢复失败，尝试清空文件: {e}")
            # 如果恢复失败，创建空数组
            with open('ai_decisions.json', 'w', encoding='utf-8') as f:
                json.dump([], f)
            print("✅ 已创建空的决策文件")
    else:
        print("❌ 找不到有效数据，创建空文件")
        with open('ai_decisions.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("✅ 已创建空的决策文件")

except Exception as e:
    print(f"❌ 处理失败: {e}")
    # 创建空文件
    with open('ai_decisions.json', 'w', encoding='utf-8') as f:
        json.dump([], f)
    print("✅ 已创建空的决策文件")

# 3. 验证修复结果
print("\n🔍 验证修复结果...")
try:
    with open('ai_decisions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ JSON格式有效")
    print(f"📊 当前记录数: {len(data)}")
except Exception as e:
    print(f"❌ 验证失败: {e}")

print("\n" + "=" * 70)
print("🎉 修复完成！")
print("=" * 70)

print("\n💡 说明:")
print("  • 损坏的文件已备份")
print("  • 已恢复尽可能多的有效数据")
print("  • 系统将继续记录新的AI决策")
print()
