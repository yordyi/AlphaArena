#!/usr/bin/env python3
"""
测试 ZenMux API 连接
验证 DeepSeek 模型是否正常工作
"""

import os
from dotenv import load_dotenv
from deepseek_client import DeepSeekClient

def test_zenmux_connection():
    """测试 ZenMux API 连接"""
    print("=" * 60)
    print("测试 ZenMux API 连接")
    print("=" * 60)

    # 加载环境变量
    load_dotenv()
    api_key = os.getenv('DEEPSEEK_API_KEY')

    if not api_key:
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        print("请在 .env 文件中设置 ZenMux 的 API Key")
        return False

    print(f"✅ API Key 已加载 (前8位): {api_key[:8]}...")
    print()

    # 初始化客户端
    client = DeepSeekClient(api_key)
    print(f"✅ API 端点: {client.base_url}")
    print(f"✅ 模型名称: {client.model_name}")
    print()

    # 测试简单对话
    print("📡 发送测试请求...")
    try:
        test_messages = [
            {
                "role": "system",
                "content": "你是一个专业的加密货币交易AI助手。"
            },
            {
                "role": "user",
                "content": "请用一句话介绍比特币。"
            }
        ]

        response = client.chat_completion(
            messages=test_messages,
            model="deepseek/deepseek-chat",
            temperature=0.7,
            max_tokens=100
        )

        if response and 'choices' in response:
            content = response['choices'][0]['message']['content']
            print("✅ API 连接成功!")
            print()
            print("📝 AI 回复:")
            print(f"   {content}")
            print()

            # 显示 token 使用情况
            if 'usage' in response:
                usage = response['usage']
                print(f"📊 Token 使用:")
                print(f"   Prompt: {usage.get('prompt_tokens', 0)}")
                print(f"   Completion: {usage.get('completion_tokens', 0)}")
                print(f"   Total: {usage.get('total_tokens', 0)}")

            return True
        else:
            print("❌ API 返回格式异常")
            print(f"响应: {response}")
            return False

    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return False

if __name__ == "__main__":
    success = test_zenmux_connection()
    print()
    print("=" * 60)
    if success:
        print("✅ ZenMux API 测试通过!")
        print("系统已就绪，可以开始交易")
    else:
        print("❌ ZenMux API 测试失败")
        print("请检查:")
        print("1. .env 文件中的 DEEPSEEK_API_KEY 是否正确")
        print("2. ZenMux 账户是否有余额")
        print("3. 网络连接是否正常")
    print("=" * 60)
