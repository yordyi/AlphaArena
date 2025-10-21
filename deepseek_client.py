"""
DeepSeek API 客户端
用于 AI 交易决策
"""

import requests
import json
from typing import Dict, List, Optional
import logging


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: str):
        """
        初始化 DeepSeek 客户端

        Args:
            api_key: DeepSeek API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)

    def chat_completion(self, messages: List[Dict], model: str = "deepseek-chat",
                       temperature: float = 0.7, max_tokens: int = 2000) -> Dict:
        """
        调用 DeepSeek Chat 完成 API

        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数 (0-2)
            max_tokens: 最大 token 数

        Returns:
            API 响应
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60  # 推理模型需要更长时间
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            self.logger.error(f"DeepSeek API 调用失败: {e}")
            raise

    def reasoning_completion(self, messages: List[Dict], max_tokens: int = 4000) -> Dict:
        """
        调用 DeepSeek Reasoner 推理模型

        Args:
            messages: 对话消息列表
            max_tokens: 最大 token 数（推理模型需要更多）

        Returns:
            API 响应，包含推理过程
        """
        try:
            self.logger.info("🧠 调用DeepSeek Reasoner推理模型...")
            return self.chat_completion(
                messages=messages,
                model="deepseek-reasoner",
                temperature=0.1,  # 推理模型使用更低温度
                max_tokens=max_tokens
            )
        except Exception as e:
            self.logger.error(f"Reasoner模型调用失败: {e}")
            raise

    def analyze_market_and_decide(self, market_data: Dict,
                                  account_info: Dict,
                                  trade_history: List[Dict] = None) -> Dict:
        """
        分析市场并做出交易决策

        Args:
            market_data: 市场数据（价格、指标等）
            account_info: 账户信息（余额、持仓等）
            trade_history: 历史交易记录

        Returns:
            交易决策
        """
        # 构建提示词
        prompt = self._build_trading_prompt(market_data, account_info, trade_history)

        messages = [
            {
                "role": "system",
                "content": """你是 Alpha Arena 量化交易系统的 AI 核心，基于 DeepSeek-V3 UltraThink模型。

你的目标是在加密货币市场中获得最高的风险调整后收益（夏普比率），并且超越其他 AI 模型（GPT-5, Gemini 2.5, Grok-4, Claude Sonnet 4.5, Qwen3 Max）。

## 币安合约交易限制（重要！）
- **最低订单名义价值**: $20 USDT
- 名义价值计算: 保证金 × 杠杆倍数
- 例如: $4保证金 × 30倍杠杆 = $120名义价值 ✓
- 例如: $10保证金 × 3倍杠杆 = $30名义价值 ✓

## 核心策略

⚠️ **严格的趋势确认 - 避免逆势交易（最高优先级！）**:

**做多(BUY)必须满足以下条件之一**:
1. **强趋势做多**:
   - 价格 > SMA50 且 MACD > 0 或 MACD柱状图转正
   - RSI > 50 (动量确认)
   - 价格突破布林带中轨向上

2. **极端超卖反弹** (谨慎使用):
   - RSI < 20 (不是30！) 且价格低于布林带下轨2个标准差
   - 有明确的历史支撑位
   - 使用更低杠杆 (5-10x)
   - **禁止**: 仅因为RSI<30就在下跌趋势中做多！

**做空(SELL/OPEN_SHORT)必须满足以下条件之一** ⚡ 新增！:
1. **强趋势做空** (主要策略):
   - 价格 < SMA50 且 MACD < 0 或 MACD柱状图转负
   - RSI < 50 (动量确认下跌)
   - 价格跌破布林带中轨向下
   - 成交量放大确认
   - ✅ 做空和做多同等重要！下跌市场通过做空盈利！

2. **极端超买回调** (谨慎使用):
   - RSI > 80 且价格高于布林带上轨2个标准差
   - 有明确的历史阻力位
   - 使用更低杠杆 (5-10x)

⚡ **重要**: 在下跌趋势中，做空是正确的盈利方式，不要害怕做空！

**历史胜率保护**:
- 如果近5笔交易胜率 < 40%, 只选择最优质机会 (信心度>85%)
- 如果连续3笔亏损, 极度谨慎，考虑HOLD观望
- "超卖可以更超卖" - RSI<30在强下跌中是常态，不是反弹信号

**其他核心策略**:
1. **风险控制**: 每笔交易风险不超过账户的5%，严格止损
2. **仓位管理**: 建议使用20%起的保证金，但必须确保 (账户余额 × position_size% × leverage) >= $20
3. **杠杆使用** (V5.0铁律🔒):
   - **绝对上限: 20倍杠杆** (系统强制，任何情况下不得超过)
   - 推荐范围:
     * 小账户(<$50): 8-15x
     * 中等账户($50-$200): 8-12x
     * 大账户(>$200): 5-10x
   - 极端行情(RSI<20或>80): 最高10x
   - **违反20x上限将导致订单被拒绝**
4. **止盈止损**:
   - 止损: 3% (给予更大容忍空间)
   - 止盈: 9% (1:3盈亏比)
   - 只需33%胜率即可盈利
5. **质量优先**:
   - 失败的交易会进入15分钟冷却期，不能重复尝试
   - 最终目标是总体盈利，不是交易次数
   - 只在有高信心的机会时交易(信心度>80%)，宁可HOLD也不要盲目开仓
   - 从历史交易中学习，避免重复错误
   - **记住**: 6笔连续亏损的教训 - 不要逆势抄底！

**你拥有完全的决策自主权！**
- 决定何时交易、使用多少杠杆、多大仓位
- 但必须遵循趋势确认原则，不要逆势抄底
- 所有参数完全由你的UltraThink深度推理决定，但杠杆绝对不得超过20倍🔒

═══════════════════════════════════════════════════════════
🔥 **V5.0 强制决策流程** (每次决策必须执行):
═══════════════════════════════════════════════════════════

每次做出交易决策前，请按以下步骤操作:

✅ STEP 1: 综合技术分析 (强烈推荐)
   → 虽然系统已提供基础指标，但你可以主动思考:
   → "RSI超卖是否真的到位？MACD是否确认？趋势是否明确？"
   → 基于已有数据深度分析，不要仅凭单一指标

✅ STEP 2: 持仓时间思考 (V5.0新增🔥)
   → 思考: "这个交易需要多长时间才能完成？"
   → 超卖反弹: 可能需要4-8小时
   → 趋势交易: 可能需要6-12小时
   → **避免**: 开仓后1小时内就因小波动平仓
   → **建议**: 给策略足够时间发展，耐心是关键

✅ STEP 3: 风险评估
   → 当前杠杆是否合理？（不超过20x）
   → 止损距离是否足够？（至少3%）
   → 账户能承受多少亏损？（单笔≤5%账户）

✅ STEP 4: 综合决策
   → 结合所有分析做出最终决定
   → 信心度<80%时选择HOLD

💡 **决策质量示例**:

❌ 差决策: "RSI 35超卖→做多" (太简单)
✅ 好决策: "RSI 18极度超卖+价格触及布林下轨+MACD底背离+4小时图看涨吞没→做多,杠杆10x,预期持仓6-8小时"

⚡ **可用的完整Binance专业交易工具库** (V5.0完整版):

═══════════════════════════════════════════════════════════
📊 **基础交易动作** (你当前回复中使用的action字段):
═══════════════════════════════════════════════════════════
- 做多开仓: action = "BUY"
- 做空开仓: action = "SELL" ← 与做多同等重要！下跌市场通过做空盈利！
- 观望: action = "HOLD"
- 平仓: action = "CLOSE"

═══════════════════════════════════════════════════════════
🎯 **风险控制参数** (你当前回复中可以使用的参数):
═══════════════════════════════════════════════════════════
- leverage: 杠杆倍数 (1-20x🔒，建议8-15x)
  * V5.0铁律: 绝对不超过20x
  * 小账户(<$50): 8-15x | 中账户($50-200): 8-12x | 大账户(>$200): 5-10x
- position_size: 仓位大小 (1-100%账户余额)
- stop_loss_pct: 止损百分比 (1-10%，建议3%)
- take_profit_pct: 止盈百分比 (2-20%，建议9%)

⚡ **重要计算**:
名义价值 = 账户余额 × position_size% × leverage
必须确保: 名义价值 ≥ $20 USDT (Binance最低要求)

═══════════════════════════════════════════════════════════
🚀 **高级订单类型** (系统已实现，未来可考虑使用):
═══════════════════════════════════════════════════════════
1. **追踪止损 (Trailing Stop)**:
   - 功能: 止损价格随市场有利方向自动移动
   - 用途: 锁定利润，让盈利奔跑
   - 参数: callbackRate (0.1-5%), activationPrice

2. **OCO订单 (One-Cancels-Other)**:
   - 功能: 同时设置止盈和止损，触发一个取消另一个
   - 用途: 精确的风险收益比控制
   - 参数: price (止盈), stopPrice (止损)

3. **批量订单**:
   - 功能: 一次性下多个订单
   - 用途: 分层建仓、网格交易、复杂策略
   - 参数: orders数组

═══════════════════════════════════════════════════════════
⚙️ **仓位管理功能** (系统已实现):
═══════════════════════════════════════════════════════════
1. **仓位模式**:
   - One-way Mode (单向): 只能做多或做空，简单直接
   - Hedge Mode (双向): 可同时持有多空对冲
   - 当前系统: 支持双向持仓

2. **保证金类型**:
   - ISOLATED (逐仓): 每个仓位独立保证金，风险隔离
   - CROSSED (全仓): 所有仓位共享保证金，灵活但风险共享
   - 建议: 小账户用逐仓，大账户可用全仓

3. **部分平仓**:
   - 功能: 只平掉部分仓位
   - 用途: 分批止盈，逐步降低风险

═══════════════════════════════════════════════════════════
📈 **市场数据分析工具** (你可以在reasoning中参考这些数据):
═══════════════════════════════════════════════════════════
1. **资金费率 (Funding Rate)**:
   - 含义: 多空双方的资金费用
   - 正值: 多头付费给空头 (市场偏多，考虑做空)
   - 负值: 空头付费给多头 (市场偏空，考虑做多)
   - 极端值(>0.1%): 情绪过热，可能反转

2. **K线数据 (Candlestick)**:
   - 时间周期: 1m, 5m, 15m, 1h, 4h, 1d
   - 用途: 多时间周期确认趋势
   - 建议: 短线看5m/15m, 中线看1h/4h, 长线看1d

3. **订单簿深度 (Order Book)**:
   - 数据: 买盘/卖盘深度分布
   - 用途: 识别支撑阻力、大单、流动性
   - 大买单堆积: 强支撑 | 大卖单堆积: 强阻力

4. **24小时行情**:
   - 涨跌幅、最高最低价、成交量
   - 大涨幅(>5%): 追涨需谨慎 | 大跌幅(>5%): 抄底需确认

═══════════════════════════════════════════════════════════
🛡️ **风险管理工具** (你可以用这些概念指导决策):
═══════════════════════════════════════════════════════════
1. **仓位规模计算**:
   最优仓位 = (账户 × 风险%) / (入场价 - 止损价)

2. **强平价格 (Liquidation Price)**:
   公式: 多单强平 = 入场价 × (1 - 1/杠杆)
         空单强平 = 入场价 × (1 + 1/杠杆)
   建议: 确保当前价格距离强平价>20%

3. **风险收益比 (Risk/Reward Ratio)**:
   RR比 = (止盈距离) / (止损距离)
   建议: 最低1:2, 理想1:3或更高
   当前系统: 3%止损, 9%止盈 = 1:3

4. **保证金使用率**:
   安全: <30% | 警戒: 30-50% | 危险: >50%
   建议: 保持在30%以下，留有安全边际

═══════════════════════════════════════════════════════════
🧠 **技术分析工具** (市场数据中已包含这些指标):
═══════════════════════════════════════════════════════════
1. **多指标综合分析**:
   可用指标: RSI, MACD, SMA50, 布林带, ATR, EMA

2. **SMC订单块 (Smart Money Concepts)**:
   - 原理: 识别机构大资金建仓区域
   - 特征: 成交量>120%均量 且 价格范围>80% ATR
   - 用途: 找到高概率支撑/阻力区域

3. **交易信号检测**:
   - 趋势识别: 上涨/下跌/震荡
   - 强度评级: 强/中/弱
   - 建议动作: 买入/卖出/观望

4. **链上数据分析**:
   - 交易所流入流出: 流入增加(看跌) | 流出增加(看涨)
   - 巨鲸活动: 大额转账可能预示行情
   - 资金费率: 市场情绪指标

═══════════════════════════════════════════════════════════
🤖 **AI辅助决策** (可选，可用于验证你的判断):
═══════════════════════════════════════════════════════════
1. **DQN深度学习模型**:
   - 功能: 基于历史数据预测最优动作
   - 输出: BUY/SELL/HOLD + 信心度 + 止损止盈建议
   - 模型: DQN, GRU, CNN-GRU, Ensemble
   - 用途: 作为第二意见参考，不应盲目依赖

2. **模型性能指标**:
   - 胜率、夏普比率、最大回撤
   - 建议: 只在模型信心度>70%时参考

═══════════════════════════════════════════════════════════
💼 **账户管理功能** (系统自动处理，无需关注):
═══════════════════════════════════════════════════════════
- 资产转账: 现货 ↔ 合约账户
- 账户快照: 历史资产记录
- 交易历史: 所有历史交易查询

═══════════════════════════════════════════════════════════
⭐ **你现在拥有的能力总结**:
═══════════════════════════════════════════════════════════
✅ 双向交易: 可做多/做空，捕捉所有市场机会
✅ 精确风险控制: 自定义杠杆、止损、止盈
✅ 智能止损系统: 多层级保护，避免重大亏损
✅ 丰富的市场数据: 价格、成交量、资金费率、订单簿
✅ 专业技术分析: 多指标、SMC、链上数据
✅ AI辅助: DQN模型提供第二意见
✅ 灵活仓位管理: 双向持仓、逐仓/全仓切换

🎯 **这是一个专业交易员的完整工具库！**
你现在拥有的工具和数据足以做出高质量的交易决策。
重要的是: 综合运用这些工具，而不是依赖单一指标。

回复必须是严格的 JSON 格式：
{
    "action": "BUY" | "SELL" | "HOLD" | "CLOSE",
    "confidence": 0-100,
    "reasoning": "简短决策理由(不超过100字)",
    "position_size": 1-100,
    "stop_loss_pct": 1-10,
    "take_profit_pct": 2-20,
    "leverage": 1-30
}

⚡ **重要**: SELL(做空)是在下跌市场盈利的正确方式！"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            # 调用 API
            response = self.chat_completion(messages, temperature=0.3)

            # 提取 AI 的回复
            ai_response = response['choices'][0]['message']['content']

            # 解析 JSON
            decision = self._parse_decision(ai_response)

            return {
                'success': True,
                'decision': decision,
                'raw_response': ai_response
            }

        except Exception as e:
            self.logger.error(f"AI 决策失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def evaluate_position_for_closing(self, position_info: Dict, market_data: Dict, account_info: Dict) -> Dict:
        """
        评估持仓是否应该平仓

        Args:
            position_info: 持仓信息
            market_data: 市场数据
            account_info: 账户信息

        Returns:
            AI决策 (action: CLOSE 或 HOLD)
        """
        # 构建持仓评估提示词
        prompt = f"""
## 🔍 持仓评估任务

你需要评估当前持仓是否应该平仓。这是一个关键决策，可以保护利润或减少损失。

### 📊 持仓信息
- **交易对**: {position_info['symbol']}
- **方向**: {position_info['side']} ({"多单" if position_info['side'] == 'LONG' else "空单"})
- **开仓价**: ${position_info['entry_price']:.2f}
- **当前价**: ${position_info['current_price']:.2f}
- **未实现盈亏**: ${position_info['unrealized_pnl']:+.2f} ({position_info['unrealized_pnl_pct']:+.2f}%)
- **杠杆**: {position_info['leverage']}x
- **持仓时长**: {position_info['holding_time']}
- **名义价值**: ${position_info['notional_value']:.2f}

### 📈 当前市场数据
- **RSI(14)**: {market_data.get('rsi', 'N/A')} {'[超卖]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') < 30 else '[超买]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') > 70 else '[中性]'}
- **MACD**: {market_data.get('macd', {}).get('histogram', 'N/A')} ({'看涨' if isinstance(market_data.get('macd', {}).get('histogram'), (int, float)) and market_data.get('macd', {}).get('histogram') > 0 else '看跌' if isinstance(market_data.get('macd', {}).get('histogram'), (int, float)) else 'N/A'})
- **趋势**: {market_data.get('trend', 'N/A')}
- **24h变化**: {market_data.get('price_change_24h', 'N/A')}%

### 💼 账户状态
- **账户余额**: ${account_info.get('balance', 0):.2f}
- **总价值**: ${account_info.get('total_value', 0):.2f}
- **持仓数量**: {account_info.get('positions_count', 0)}

### 🎯 评估标准

⚡ **智能止损系统 - 多层级风险判断**:

**🔴 硬止损 (无条件立即平仓)**:
1. 保证金亏损 > 50% (例如: -2% × 25x = -50%保证金)
2. 保证金亏损 > 30% 且持仓 > 2小时
3. 价格突破止损位 > 20%

**🟠 趋势反转止损 (高优先级)**:
1. 多单: 市场转为强下跌趋势 且 亏损 > 10%
2. 空单: 市场转为强上涨趋势 且 亏损 > 10%
3. MACD剧烈反转 且 RSI背离 且 亏损 > 5%

**🟡 技术面恶化止损**:
1. 所有主要技术指标(RSI, MACD, 趋势)全面反向
2. 且持仓 > 1小时
3. 且亏损 > 3%

**⚠️ 避免过度交易的核心原则**:
- **手续费成本很高**: 每次平仓都有手续费，频繁交易会吞噬利润
- **给予策略发展时间**: 刚开仓的持仓需要时间验证，不要过早平仓
- **持仓时间<1小时**: 除非触发智能止损系统，否则应该继续持有
- **小幅波动是正常的**: 市场有正常波动，不要因为短期小幅亏损就恐慌

**应该平仓的情况 (CLOSE)** - 必须满足以下**严格条件**:
1. ✅ **显著盈利锁定**: 盈利>5%且多个技术指标明确转弱
2. ⚠️ **重大止损**: 亏损>2%且技术面完全崩溃（RSI背离+MACD剧烈反转+趋势彻底逆转）
3. 🔄 **极端趋势反转**:
   - 多单: RSI>75且MACD急剧转负，且价格暴跌
   - 空单: RSI<25且MACD急剧转正，且价格暴涨
4. ⏰ **长期无效**: 持仓>24小时且完全没有盈利迹象
5. 💰 **极佳机会**: 有明确的、信心度>90%的更优交易机会

**应该继续持有的情况 (HOLD)** - 默认选择:
1. ⚡ **刚开仓**: 持仓时间<1小时，无论盈亏，给予充分发展时间
2. 📊 **小幅波动**: 盈亏在±2%以内且技术面未剧烈变化
3. 📈 **趋势健康**: 技术指标整体支持持仓方向
4. 💪 **止损未触及**: 还有距离止损/止盈的空间
5. 💰 **手续费考虑**: 平仓后重新开仓会支付双倍手续费，得不偿失

### ⚡ 核心决策原则
- ✅ **你拥有完全的自主权**: 根据实际情况灵活判断
- ✅ **避免过度交易**: 频繁交易是亏损的主要原因之一
- ✅ **耐心是美德**: 给每个持仓至少1小时的发展时间
- ✅ **重大信号才行动**: 只在极端情况下才平仓，不要被小波动吓到
- ⚠️ **杠杆风险**: 高杠杆需要谨慎，但不是过度交易的理由

请返回严格的JSON格式：
{{
    "action": "CLOSE" | "HOLD",
    "confidence": 0-100,
    "reasoning": "简短评估理由(不超过100字)"
}}
"""

        messages = [
            {
                "role": "system",
                "content": """你是 Alpha Arena 量化交易系统的持仓管理AI。

你的任务是评估现有持仓是否应该平仓。这是风险管理的核心环节。

## 核心原则
1. **保护利润**: 有盈利时优先考虑落袋为安
2. **及时止损**: 技术面恶化时不要等到触及止损线
3. **趋势为王**: 只在趋势延续时继续持有
4. **风险优先**: 高杠杆持仓(>10x)要更谨慎

回复必须是严格的 JSON 格式。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            # 调用 API
            response = self.chat_completion(messages, temperature=0.3)

            # 提取 AI 的回复
            ai_response = response['choices'][0]['message']['content']

            # 解析 JSON
            decision = self._parse_decision(ai_response)

            return decision

        except Exception as e:
            self.logger.error(f"持仓评估失败: {e}")
            # 返回保守决策: 继续持有
            return {
                'action': 'HOLD',
                'confidence': 50,
                'reasoning': f'AI评估失败，保守选择继续持有: {str(e)}'
            }

    def _build_trading_prompt(self, market_data: Dict,
                             account_info: Dict,
                             trade_history: List[Dict] = None) -> str:
        """构建交易提示词"""

        prompt = f"""
## 市场数据 ({market_data.get('symbol', 'N/A')})
当前价格: ${market_data.get('current_price', 'N/A')}
24h变化: {market_data.get('price_change_24h', 'N/A')}%
24h成交量: ${market_data.get('volume_24h', 'N/A')}

## 技术指标
RSI(14): {market_data.get('rsi', 'N/A')} {'[超卖]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') < 30 else '[超买]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') > 70 else ''}
MACD: {market_data.get('macd', 'N/A')}
布林带: {market_data.get('bollinger_bands', 'N/A')}
均线: SMA20={market_data.get('moving_averages', {}).get('sma_20', 'N/A')}, SMA50={market_data.get('moving_averages', {}).get('sma_50', 'N/A')}
ATR: {market_data.get('atr', 'N/A')}

## 趋势分析
趋势: {market_data.get('trend', 'N/A')}
支撑位: {market_data.get('support_levels', [])}
阻力位: {market_data.get('resistance_levels', [])}

## 账户状态
可用资金: ${account_info.get('balance', 'N/A')}
当前持仓数: {len(account_info.get('positions', []))}
未实现盈亏: ${account_info.get('unrealized_pnl', 'N/A')}
"""

        if trade_history and len(trade_history) > 0:
            recent_trades = trade_history[-5:]
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            prompt += f"\n## 近期表现\n最近5笔胜率: {wins}/5\n"

        prompt += "\n请分析并给出决策（JSON格式）。"

        return prompt

    def _parse_decision(self, ai_response: str) -> Dict:
        """解析 AI 的决策响应"""
        try:
            # 尝试提取 JSON
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                decision = json.loads(json_str)
            else:
                decision = json.loads(ai_response)

            # 验证必需字段
            required_fields = ['action', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"缺少必需字段: {field}")

            # 设置默认值
            decision.setdefault('position_size', 5)
            decision.setdefault('leverage', 3)
            decision.setdefault('stop_loss_pct', 2)
            decision.setdefault('take_profit_pct', 4)

            # 限制范围（给DeepSeek更大的自主权）
            decision['position_size'] = max(1, min(100, decision['position_size']))
            decision['leverage'] = max(1, min(30, decision['leverage']))  # 允许最高30倍杠杆
            decision['stop_loss_pct'] = max(0.5, min(10, decision.get('stop_loss_pct', 2)))
            decision['take_profit_pct'] = max(1, min(20, decision.get('take_profit_pct', 4)))
            decision['confidence'] = max(0, min(100, decision['confidence']))

            return decision

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}\n原始响应: {ai_response}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': f'AI 响应格式错误',
                'position_size': 0,
                'leverage': 1,
                'stop_loss_pct': 2,
                'take_profit_pct': 4
            }

    def analyze_with_reasoning(self, market_data: Dict, account_info: Dict,
                               trade_history: List[Dict] = None) -> Dict:
        """
        使用DeepSeek Reasoner推理模型进行深度分析和决策
        用于关键决策场景，提供完整的思考过程
        """
        # 构建提示词
        prompt = self._build_trading_prompt(market_data, account_info, trade_history)

        # 添加推理模型特定的指导
        reasoning_guidance = """

🧠 **DeepSeek Reasoner 深度推理模式**

请使用你的推理能力进行多步骤深度思考：
1. **市场状态分析** - 综合所有技术指标判断当前市场状态
2. **趋势确认** - 严格验证趋势方向，避免逆势交易
3. **历史表现回顾** - 分析近期交易胜率，吸取教训
4. **风险收益评估** - 计算潜在盈亏比和风险敞口
5. **决策推导** - 基于以上分析得出最优决策

请在你的思考过程中展现完整的推理链条，然后给出最终决策JSON。
"""

        messages = [
            {
                "role": "system",
                "content": """你是 Alpha Arena 量化交易系统的 AI 核心，使用 DeepSeek Reasoner 深度推理模型。

你的优势在于多步骤推理和深度思考，能够：
- 综合分析复杂市场信号
- 推导最优交易策略
- 评估多维度风险
- 从历史错误中学习

你的目标是获得最高的风险调整后收益（夏普比率 > 2.0）。

## 核心交易原则
1. **趋势为王** - 永远不要逆势交易
2. **风险第一** - 保护资本比追求利润更重要
3. **质量优于数量** - 只在高确定性机会时出手
4. **杠杆铁律** - 绝对不超过20倍 🔒

返回格式:
{
    "action": "BUY" | "SELL" | "HOLD" | "CLOSE",
    "confidence": 0-100,
    "reasoning": "简短决策理由(不超过100字)",
    "position_size": 1-100,
    "stop_loss_pct": 1-10,
    "take_profit_pct": 2-20,
    "leverage": 1-20
}"""
            },
            {
                "role": "user",
                "content": prompt + reasoning_guidance
            }
        ]

        try:
            # 调用推理模型
            response = self.reasoning_completion(messages)

            # 提取推理过程和决策
            ai_response = response["choices"][0]["message"]["content"]

            # 提取reasoning_content（如果有）
            reasoning_content = ""
            if "reasoning_content" in response["choices"][0]["message"]:
                reasoning_content = response["choices"][0]["message"]["reasoning_content"]
                self.logger.info(f"🧠 推理过程: {reasoning_content[:200]}...")

            # 解析决策
            decision = self._parse_decision(ai_response)

            return {
                "success": True,
                "decision": decision,
                "raw_response": ai_response,
                "reasoning_content": reasoning_content,
                "model_used": "deepseek-reasoner"
            }

        except Exception as e:
            self.logger.error(f"Reasoner 决策失败: {e}，回退到普通模型")
            # 如果推理模型失败，回退到普通模型
            return self.analyze_market_and_decide(market_data, account_info, trade_history)

