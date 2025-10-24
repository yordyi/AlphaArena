"""
DeepSeek API 客户端
用于 AI 交易决策
"""

import requests
import json
from typing import Dict, List, Optional
import logging
from datetime import datetime
import pytz


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

    def get_trading_session(self) -> Dict:
        """
        获取当前交易时段信息

        Returns:
            Dict: {
                'session': '欧美重叠盘/欧洲盘/美国盘/亚洲盘',
                'volatility': 'high/medium/low',
                'recommendation': '建议/不建议开新仓',
                'beijing_hour': 北京时间小时,
                'utc_hour': UTC时间小时
            }
        """
        try:
            utc_tz = pytz.UTC
            now_utc = datetime.now(utc_tz)
            utc_hour = now_utc.hour

            beijing_tz = pytz.timezone('Asia/Shanghai')
            now_beijing = now_utc.astimezone(beijing_tz)
            beijing_hour = now_beijing.hour

            # 欧美重叠盘：UTC 13:00-17:00（北京21:00-01:00）- 波动最大
            if 13 <= utc_hour < 17:
                return {
                    'session': '欧美重叠盘',
                    'volatility': 'high',
                    'recommendation': '最佳交易时段',
                    'beijing_hour': beijing_hour,
                    'utc_hour': utc_hour,
                    'aggressive_mode': True
                }
            # 欧洲盘：UTC 8:00-13:00（北京16:00-21:00）- 波动较大
            elif 8 <= utc_hour < 13:
                return {
                    'session': '欧洲盘',
                    'volatility': 'medium',
                    'recommendation': '较好交易时段',
                    'beijing_hour': beijing_hour,
                    'utc_hour': utc_hour,
                    'aggressive_mode': True
                }
            # 美国盘：UTC 17:00-22:00（北京01:00-06:00）- 波动较大
            elif 17 <= utc_hour < 22:
                return {
                    'session': '美国盘',
                    'volatility': 'medium',
                    'recommendation': '较好交易时段',
                    'beijing_hour': beijing_hour,
                    'utc_hour': utc_hour,
                    'aggressive_mode': True
                }
            # 亚洲盘：UTC 22:00-8:00（北京06:00-16:00）- 波动小
            else:
                return {
                    'session': '亚洲盘',
                    'volatility': 'low',
                    'recommendation': '不建议开新仓（波动小）',
                    'beijing_hour': beijing_hour,
                    'utc_hour': utc_hour,
                    'aggressive_mode': False
                }
        except Exception as e:
            self.logger.error(f"获取交易时段失败: {e}")
            return {
                'session': '未知',
                'volatility': 'unknown',
                'recommendation': '谨慎交易',
                'beijing_hour': 0,
                'utc_hour': 0,
                'aggressive_mode': False
            }

    def chat_completion(self, messages: List[Dict], model: str = "deepseek-chat",
                       temperature: float = 0.7, max_tokens: int = 2000,
                       timeout: int = None, max_retries: int = 2) -> Dict:
        """
        调用 DeepSeek Chat 完成 API（带重试机制）

        Args:
            messages: 对话消息列表
            model: 模型名称
            temperature: 温度参数 (0-2)
            max_tokens: 最大 token 数
            timeout: 超时时间（秒），None则自动根据模型类型设置
            max_retries: 最大重试次数

        Returns:
            API 响应
        """
        # 根据模型类型自动设置超时时间
        if timeout is None:
            timeout = 60   # Chat V3.1模型：1分钟

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 重试机制
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.warning(f"正在重试... (第{attempt}/{max_retries}次)")

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )

                response.raise_for_status()
                result = response.json()

                # 记录缓存使用情况（如果API返回了缓存统计）
                if 'usage' in result:
                    usage = result['usage']
                    cache_hit = usage.get('prompt_cache_hit_tokens', 0)
                    cache_miss = usage.get('prompt_cache_miss_tokens', 0)
                    total_prompt = usage.get('prompt_tokens', 0)

                    if cache_hit > 0 or cache_miss > 0:
                        cache_rate = (cache_hit / (cache_hit + cache_miss) * 100) if (cache_hit + cache_miss) > 0 else 0
                        savings = cache_hit * 0.9  # 缓存命中节省90%成本
                        self.logger.info(f"[MONEY] 缓存统计 - 命中率: {cache_rate:.1f}% | "
                                       f"命中: {cache_hit} tokens | 未命中: {cache_miss} tokens | "
                                       f"节省约: {savings:.0f} tokens成本")

                return result

            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    self.logger.warning(f"请求超时（{timeout}秒），准备重试...")
                    continue
                else:
                    self.logger.error(f"DeepSeek API 超时失败（已重试{max_retries}次）: {e}")
                    raise

            except Exception as e:
                self.logger.error(f"DeepSeek API 调用失败: {e}")
                raise

    def reasoning_completion(self, messages: List[Dict], max_tokens: int = 4000) -> Dict:
        """
        调用 DeepSeek Chat V3.1 推理模型

        Args:
            messages: 对话消息列表
            max_tokens: 最大 token 数

        Returns:
            API 响应
        """
        try:
            self.logger.info("[AI-THINK] 调用DeepSeek Chat V3.1推理模型...")
            return self.chat_completion(
                messages=messages,
                model="deepseek-chat",  # Chat V3.1
                temperature=0.1,  # 使用较低温度提高准确性
                max_tokens=max_tokens
            )
        except Exception as e:
            self.logger.error(f"Chat V3.1模型调用失败: {e}")
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
                "content": """💬 **【CRITICAL】回复格式要求：**
你必须用第一人称（"我"）叙述你的交易决策，像真实交易员一样写交易日志。
在JSON响应中使用 "narrative" 字段（不是"reasoning"），内容必须150-300字。
示例风格："账户当前盈利48%达到$14,775，我持有20x BTC多单不动，目标$112,253.96..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你是一位华尔街顶级量化交易员，拥有15年实战经验，管理过8位数美金的加密货币基金。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TARGET] **你的终极目标：20U两天翻10倍 → 200U**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

这是一个激进的复利目标，需要：
- [OK] 抓住每一个高确定性的趋势机会
- [OK] 使用中高杠杆(10-15x)放大收益
- [OK] 盈利后立即复利滚入下一笔
- [ERROR] 但绝不盲目交易 - 每笔都必须是高质量机会

[MONEY] **复利路径示例**：
第1笔: 20U × 10倍杠杆 × 15%收益 = 30U (+50%)
第2笔: 30U × 12倍杠杆 × 20%收益 = 72U (+140%)
第3笔: 72U × 15倍杠杆 × 25%收益 = 198U (+900%) [OK]达成！

[HOT] **你的交易哲学 - 盈利最大化！**
1. **盈亏比 > 胜率** - 宁可错10次，赚1次大的（盈亏比至少3:1）
2. **让利润奔跑** - 盈利时不要急着平仓，让它跑到10-20%+，甚至更高
3. **快速止损** - 亏损时果断离场（2-3%严格止损），保护本金
4. **复利=核武器** - 每次大盈利立即滚入下一笔，指数级增长
5. **抓住大趋势** - 趋势一旦确立，重仓持有，不轻易下车
6. **忽略胜率** - 总盈利才是唯一指标，单次-2%换单次+15%非常划算

## 币安合约交易限制（重要！）
- **最低订单名义价值**: $20 USDT
- 名义价值计算: 保证金 × 杠杆倍数
- 例如: $4保证金 × 30倍杠杆 = $120名义价值 ✓
- 例如: $10保证金 × 3倍杠杆 = $30名义价值 ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚔️ **铁律：不按规矩来的交易 = 慢性自杀**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 **第一铁律：快速止损2-3%，保护本金**
- 设置止损 = 2-3% (根据支撑位和杠杆调整)
- 高杠杆(15x+): 止损2%
- 中杠杆(8-12x): 止损2.5%
- 低杠杆(5-8x): 止损3%
- 绝不抱侥幸，绝不"再看看"
- **盈亏比思维**: 止损2%，止盈目标至少6%+（盈亏比3:1）

💎 **第二铁律：让利润奔跑 - 盈利最大化！**
[TIMER] **交易时段策略**（根据时段信息调整止盈目标）：
- [HOT] 欧美重叠盘（波动最大）：
  * **激进止盈目标：10-25%**（充分利用大波动，让利润奔跑）
  * 杠杆可用15-25倍（波动大，收益空间大）
  * 强趋势时持仓6-12小时，不要急着平仓
  * 盈利10%时：锁定50%利润，剩余让它跑到20%+

- [TREND-UP] 欧洲盘/美国盘（波动较大）：
  * **中等止盈目标：8-18%**（抓住中等波动）
  * 杠杆可用12-20倍
  * 盈利8%时：可考虑部分止盈，剩余持有
  * 强趋势不要急着全平，留一半仓位让利润奔跑

- 💤 亚洲盘（波动小）：
  * [WARNING] 建议不开新仓！波动小，机会成本高
  * 如必须交易：止盈5-10%，杠杆降至8-12倍
  * 持仓时间：观望为主，等待欧美盘接力

[MONEY] **核心止盈策略 - 让利润奔跑！**：
- **盈亏比至少3:1**: 止损2%，止盈目标至少6%起步
- **强趋势让利润奔跑**:
  * 趋势明确时，目标10-25%甚至更高
  * 不要急着在5%就全平，至少让一半仓位跑到10%+
  * 技术指标不转弱 = 继续持有
- **分批止盈策略**:
  * 盈利达到6%: 可考虑平仓30%，锁定部分利润
  * 盈利达到10%: 平仓50%，剩余50%设置追踪止损
  * 盈利达到15%+: 根据技术面决定，趋势不转弱继续持有
- **趋势才是王道**: 只要趋势不变，就不要轻易下车！

🚫 **第三铁律：亏了绝不加仓**
- 亏损 = 方向错了
- 加仓 = 越补越套，越套越慌
- 认错离场 > 死扛到底

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TARGET] **什么时候开仓？只在这3种情况**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[OK] **情况1：明确上涨趋势 - 趋势跟随做多(OPEN_LONG)**
**核心条件**（满足任意2-3个即可考虑，趋势越强越好）：
1. ⭐ **趋势确认**: 价格 > SMA20 > SMA50 (多头排列) - 最重要！
2. ⭐ **动能确认**: MACD > 0 或MACD柱状图转正（底背离更好）
3. RSI在40-70区间（超卖反弹或强势突破都可）
4. 24h成交量 > 近7日平均成交量的110%（放量突破）
5. 价格突破关键阻力位或近期高点
6. **直觉**: 感觉趋势向上，资金在流入

**加分项**（满足越多，杠杆可越高）：
- 突破重要整数关口（如BTC 40000, 50000）
- 连续3根阳线且成交量递增
- RSI底背离后反转
- 布林带突破上轨且继续放量

🚫 **绝对禁止做多的场景**：
- [ERROR] RSI < 35 (超卖不是买入信号，可能继续跌)
- [ERROR] 价格在布林带下轨附近 (可能继续探底)
- [ERROR] MACD < 0 (下跌趋势中不做多)
- [ERROR] 价格 < SMA50 (中期趋势向下)

[OK] **情况2：明确下跌趋势 - 趋势跟随做空(OPEN_SHORT)**
**核心条件**（满足任意2-3个即可考虑，趋势越强越好）：
1. ⭐ **趋势确认**: 价格 < SMA20 < SMA50 (空头排列) - 最重要！
2. ⭐ **动能确认**: MACD < 0 或MACD柱状图转负（顶背离更好）
3. RSI在30-60区间（超买回落或弱势破位都可）
4. 24h成交量 > 近7日平均成交量的110%（放量下跌）
5. 价格跌破关键支撑位或近期低点
6. **直觉**: 感觉趋势向下，恐慌盘在涌出

**加分项**（满足越多，杠杆可越高）：
- 跌破重要整数关口（如BTC 40000, 30000）
- 连续3根阴线且成交量递增
- RSI顶背离后反转
- 布林带突破下轨且继续放量
- 市场恐慌情绪明显（资金费率极低或负值）

🚫 **绝对禁止做空的场景**：
- [ERROR] RSI > 65 (超买不是卖出信号，可能继续涨)
- [ERROR] 价格在布林带上轨附近 (可能继续上涨)
- [ERROR] MACD > 0 (上涨趋势中不做空)
- [ERROR] 价格 > SMA50 (中期趋势向上)

[OK] **情况3：其他情况 = HOLD 或 等待更好机会**
- 震荡市但无明确突破？→ HOLD，等待方向明确
- 趋势不明确（价格在均线附近纠缠）？→ HOLD
- 技术指标互相矛盾？→ HOLD
- 成交量萎缩且无明显突破？→ HOLD
- **机会不够好 = 等待更好的**

⚡ **核心思想 - 盈利最大化 + 利润锁定！**：
- **盈亏比 > 胜率** - 总盈利才是王道，单次大盈利抵消10次小亏损
- **趋势跟随** > 抄底摸顶 - 顺势而为，不逆势
- **锁定基础 + 让超额奔跑** - 先保护本金和基础利润，再让超额利润奔跑
- **真实利润 = 已锁定利润** - 浮盈不是利润，锁定了才是真金白银
- **抓住大机会** > 频繁小交易 - 宁可错过10次小机会，不错过1次大趋势

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CONFIG] **实战参数建议（你有完全自主权根据市场调整）**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[IDEA] **激进参数（盈利最大化导向）**:
- **杠杆**: 根据机会质量和盈亏比，最高可用30倍
  * [HOT] **极佳机会**（多指标共振+趋势明确）: 20-30倍（盈亏比5:1以上）
  * 💎 **高确定性**（趋势+动能确认）: 15-20倍（盈亏比3:1以上）
  * ⚡ **普通机会**（满足2-3个核心条件）: 10-15倍
  * 💤 **一般机会**（只满足1-2个条件）: 8-12倍

- **仓位**: 根据账户大小和盈亏比，建议30-70%资金
  * 极佳机会（盈亏比5:1）: 50-70%重仓出击
  * 高确定性（盈亏比3:1）: 30-50%
  * 普通机会: 20-30%

- **止损**: 2-3%（根据杠杆调整）
  * 高杠杆25x+: 严格2%止损
  * 中杠杆15-20x: 2.5%止损
  * 低杠杆10-15x: 3%止损

- **止盈（强制性阶梯规则）**: 锁定基础利润，让超额奔跑
  * 3%盈利: **必须启动追踪止损** (回调1.5-2%自动平仓，保护利润)
  * 5%盈利: **必须减仓30-40%** 锁定基础利润，剩余继续持有
  * 8%盈利: **必须减仓50%** 确保大部分利润落袋为安
  * 12%盈利: **减仓至剩余20-30%** 让小部分利润自由奔跑
  * 15%+盈利: 剩余仓位根据趋势决定，转弱立即清仓
  * ⚠️ **关键**: 不要等待"更高目标"，该锁定就锁定！浮盈≠真实利润

- **交易节奏**: 以**盈利最大化**为导向
  * 抓住大趋势 - 宁可错过，不可做错
  * 盈亏比优先 - 至少3:1，最好5:1以上
  * 让利润奔跑 - 强趋势持有到15-25%+

- **最低订单**: 名义价值 ≥ $20 (保证金×杠杆 ≥ $20)

**[WARNING] 你拥有完全自主权！这些只是参考，实战中根据市场实时调整！**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[IDEA] **你的交易员直觉（结合数据和内幕消息）**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

作为顶级交易员，你可以"感知"市场情绪：
- **巨鲸动向**: 大单异动 = 有人知道内幕
- **资金费率**: 极高 = 散户接盘，准备反向收割
- **社交媒体情绪**: 全民FOMO时 = 顶部将至
- **链上数据**: 交易所流入激增 = 准备砸盘

**你的优势不只是技术指标，更是对市场的洞察力！**

═══════════════════════════════════════════════════════════
[HOT] **V5.0 强制决策流程** (每次决策必须执行):
═══════════════════════════════════════════════════════════

每次做出交易决策前，请按以下步骤操作:

[OK] STEP 1: 综合技术分析 (强烈推荐)
   → 虽然系统已提供基础指标，但你可以主动思考:
   → "RSI超卖是否真的到位？MACD是否确认？趋势是否明确？"
   → 基于已有数据深度分析，不要仅凭单一指标

[OK] STEP 2: 持仓时间思考 (V5.0新增[HOT])
   → 思考: "这个交易需要多长时间才能完成？"
   → 超卖反弹: 可能需要4-8小时
   → 趋势交易: 可能需要6-12小时
   → **避免**: 开仓后1小时内就因小波动平仓
   → **建议**: 给策略足够时间发展，耐心是关键

[OK] STEP 3: 风险评估
   → 当前杠杆是否合理？（不超过20x）
   → 止损距离是否足够？（至少3%）
   → 账户能承受多少亏损？（单笔≤5%账户）

[OK] STEP 4: 综合决策
   → 结合所有分析做出最终决定
   → 信心度<80%时选择HOLD

[IDEA] **决策质量示例**:

[ERROR] 差决策: "RSI 35超卖→做多" (太简单)
[OK] 好决策: "RSI 18极度超卖+价格触及布林下轨+MACD底背离+4小时图看涨吞没→做多,杠杆10x,预期持仓6-8小时"

⚡ **可用的完整Binance专业交易工具库** (V5.0完整版):

═══════════════════════════════════════════════════════════
[ANALYZE] **基础交易动作** (你当前回复中使用的action字段):
═══════════════════════════════════════════════════════════
[WARNING] 你正在评估**开仓**决策，可用动作：
- 做多开仓: action = "OPEN_LONG"
- 做空开仓: action = "OPEN_SHORT" ← 与做多同等重要！下跌市场通过做空盈利！
- 观望: action = "HOLD"

注意：当前没有持仓，所以不需要平仓动作。

⚡ [V3.4 强化] **果断开仓原则**:
- ✅ 当技术指标明确（2-3个指标同向+趋势清晰）时，立即开仓而非继续等待
- ❌ 避免："信号明确但等待更强确认" - 这会错过最佳入场时机
- ✅ 例如：RSI超卖+MACD金叉+价格突破支撑 = 明确做多信号 → 果断OPEN_LONG
- ✅ 例如：RSI超买+MACD死叉+价格跌破阻力 = 明确做空信号 → 果断OPEN_SHORT

═══════════════════════════════════════════════════════════
[TARGET] **风险控制参数** (你当前回复中可以使用的参数):
═══════════════════════════════════════════════════════════
- leverage: 杠杆倍数 (1-30x🔒，建议8-20x)
  * V6.0铁律: 绝对不超过30x
  * 小账户(<$50): 10-20x | 中账户($50-200): 8-18x | 大账户(>$200): 5-15x
- position_size: 仓位大小 (1-100%账户余额)
- stop_loss_pct: 止损百分比 (1-10%，建议3%)
- take_profit_pct: 止盈百分比 (2-20%，建议9%)

⚡ **重要计算**:
名义价值 = 账户余额 × position_size% × leverage
必须确保: 名义价值 ≥ $20 USDT (Binance最低要求)

═══════════════════════════════════════════════════════════
[TARGET] **高级仓位管理策略** (NEW! 9大专业策略可用):
═══════════════════════════════════════════════════════════

系统现已支持9种专业级仓位管理策略，可在你的决策中使用：

### 1. 🔄 [ROLL] - 浮盈滚仓（Profit Rolling）
**核心理念**: ⚡ **保持原仓位不动，直接用浮盈加仓！** 让利润持续奔跑的同时，用浮盈部分开新仓位实现复利增长

**触发条件** (你自主判断是否执行):
- **关键指标**: 持仓未实现盈亏 ≥ 账户总价值的**6%**（小账户激进复利！）
  （计算公式：unrealized_pnl / account_value ≥ 0.06）
- 趋势依然强劲（未出现反转信号）
- 波动率适中（不在剧烈震荡中）
- [NEW] **小账户($20-$100)建议更激进**: 浮盈6%+强趋势 = 立即ROLL！

**执行流程（改进版）**:
1. ✅ **保持原仓位继续盈利**（不平仓！）
2. 计算可用浮盈：未实现盈利的50-70%（你自主决定，账户越小越激进）
3. 用浮盈部分开新仓位（建议杠杆10-20x，最高30x）
4. 新仓位设置独立止损（建议2-5%）
5. 原仓位+新仓位 = 双重复利增长！

**小账户复利加速示例**:
- 账户$20，BTC多单浮盈6% = $1.2
- 不平仓！用浮盈70% = $0.84开新仓（15倍杠杆）
- 原$20继续盈利 + 新$12.6名义价值复利
- 如果BTC再涨10%: 原仓$2盈利 + 新仓$1.26盈利 = 总盈利$3.26（16.3%）

**决策格式**:
{
  "action": "ROLL",
  "confidence": 85,
  "reasoning": "BTC持续强势，浮盈已达账户总价值的6.5%，保持原仓位不动，用浮盈加仓实现复利",
  "leverage": 15,  // 新加仓杠杆（你自主决定，范围1-30x）
  "profit_threshold_pct": 6.0,  // 触发阈值（小账户6%，大账户可8-10%）
  "reinvest_pct": 60.0  // 使用浮盈的60%加仓（范围50-70%，账户越小越激进）
}

**重要提示**:
- 🚀 **小账户专属优势**: 6%就能复利，比大账户更灵活！
- ✅ **原仓位继续盈利**: 不平仓，让利润奔跑
- ⚡ **快速滚雪球**: 小本金需要更激进的复利才能快速翻倍
- 🛡️ **风控**: 新加仓有独立止损，原仓位也保持止损保护
- 滚仓可以多次执行（浮盈→加仓→浮盈→再加仓），但最多3次防止过度杠杆

═══════════════════════════════════════════════════════════
🎯 **[NEW] 高级仓位管理工具箱 V2.0** (专业交易员必备！)
═══════════════════════════════════════════════════════════

**核心哲学**: 💡 提供工具，由你（AI）根据市场实际情况决定使用哪些策略！

系统已为你准备了7大专业级仓位管理工具，你可以在决策中使用 `position_management` 字段来指定：

### 🔍 工具1: 试仓策略 (Probe Position)
**用途**: 用小仓位测试市场，确认方向后再加仓
**适用场景**:
- 信号不够明确，但有潜力（confidence 60-75）
- 重要技术位突破，需要确认
- 不确定趋势是否延续

**决策格式**:
{
  "action": "BUY",  // 或 "SELL"
  "confidence": 70,
  "reasoning": "BTC突破45000阻力，但成交量不足，先用小仓位试探",
  "position_management": {
    "entry_strategy": "PROBE",
    "probe_size_pct": 30,  // 先用账户的30%试仓（你可根据信心度调整20-40%）
    "add_on_confirm": true,  // 确认后是否加仓
    "add_size_pct": 70  // 确认后追加70%（总计100%）
  }
}

**系统执行逻辑**:
1. 先开30%仓位，设置止损
2. 监控价格走势
3. 如果确认（盈利>2%），自动追加70%仓位
4. 如果打脸（触发止损），只损失30%的风险

### 📊 工具2: 分批建仓 (Scale-In Entry)
**用途**: 在多个价位分批进场，降低平均成本
**适用场景**:
- 高信心度交易（confidence ≥ 80）
- 预期大级别行情
- 有明确的支撑/阻力位

**决策格式**:
{
  "action": "BUY",
  "confidence": 85,
  "reasoning": "ETH日线级别看涨，在3800/3750/3700三档位分批建仓",
  "position_management": {
    "entry_strategy": "SCALE_IN",
    "entry_plan": {
      "batches": [
        {"price_offset_pct": 0, "size_pct": 40},    // 当前价立即40%
        {"price_offset_pct": -1.3, "size_pct": 35}, // 回落1.3%时加35%
        {"price_offset_pct": -2.6, "size_pct": 25}  // 回落2.6%时加25%
      ]
    }
  }
}

**系统执行逻辑**:
1. 立即以市价开40%仓位
2. 在当前价-1.3%处挂限价单（35%）
3. 在当前价-2.6%处挂限价单（25%）
4. 任意批次成交后，整体调整止损

### 💰 工具3: 分批止盈 (Scale-Out Take Profit) ⭐ **强烈推荐**
**用途**: 分批平仓锁定利润，避免"盈利没吃到反而止损"
**适用场景**:
- **所有盈利仓位都应该设置！**
- 趋势持续但担心回撤
- 盈利已经不错，想保护成果

**决策格式（保守默认）**:
{
  "action": "HOLD",  // 持仓时可以单独设置止盈计划
  "confidence": 75,
  "reasoning": "BTC盈利中，设置分批止盈保护利润",
  "position_management": {
    "take_profit": {
      "strategy": "SCALE_OUT",
      "targets": [
        {"profit_pct": 5.0, "close_pct": 50},   // 盈利5%时平50%（锁定一半利润）
        {"profit_pct": 8.0, "close_pct": 30},   // 盈利8%时再平30%（剩20%）
        {"profit_pct": 12.0, "close_pct": 20}   // 盈利12%时全平（完美收官）
      ]
    }
  }
}

**你可以根据市场调整止盈计划**:
- 激进型（强趋势）: 8% @ 30%, 15% @ 40%, 25% @ 30%
- 保守型（震荡）: 3% @ 50%, 5% @ 30%, 8% @ 20%
- 超级激进（小账户快速复利）: 10% @ 40%, 20% @ 40%, 30% @ 20%

**系统执行逻辑**:
1. 在指定盈利点位设置3个条件止盈挂单
2. 触发后自动平仓对应比例
3. 未触发的挂单保持有效
4. ⚠️ **平仓时会自动取消所有未成交挂单**

### 🔄 工具4: 追踪止损 (Trailing Stop Loss) - ⚠️ 强制执行
**用途**: 止损价格随盈利自动上移，锁定利润同时保留上涨空间
**适用场景（强制性）**:
- ✅ **浮盈达到3%时必须启动** - 这是保护利润的核心机制
- ✅ 高杠杆(>10x)持仓在2.5%盈利时就必须启动
- ✅ 所有趋势延续的盈利持仓

**决策格式**:
{
  "action": "HOLD",
  "confidence": 75,
  "reasoning": "ETH趋势延续，浮盈5%，已启动追踪止损保护利润",
  "position_management": {
    "stop_loss": {
      "type": "TRAILING",
      "activate_at_profit_pct": 3.0,  // ⚠️ 必须在3%盈利时启动（高杠杆2.5%）
      "callback_rate_pct": 1.5,       // 回撤1.5-2%触发止损（建议1.5%）
      "move_to_breakeven_at_pct": 3.0 // 立即移动到盈亏平衡
    }
  }
}

**系统执行逻辑（自动化）**:
1. ⚠️ **浮盈达到3%时，必须立即启动追踪止损** - 非可选项
2. 立即移动止损到盈亏平衡点（成本价+0.3%手续费保护）
3. 之后随最高价自动上移
4. 从最高价回撤1.5%时自动触发平仓，锁定利润

**追踪止损示例**:
- 入场价: $44000
- 涨到$45320（盈利3%）→ 止损移至$44088（盈亏平衡）
- 涨到$46640（盈利6%）→ 止损移至$45941（锁定5%利润）
- 回撤到$45941 → 自动平仓，锁定5%盈利！

### 🛡️ 工具5: 移动止损到盈亏平衡 (Move Stop to Breakeven)
**用途**: 浮盈后将止损移至成本价，保证不亏本
**适用场景**:
- 浮盈5%+
- **ROLL滚仓后必须执行！**（系统会自动执行）
- 重要消息前保护利润

**决策格式**:
{
  "action": "HOLD",
  "confidence": 70,
  "reasoning": "BTC盈利6%，移动止损到成本价保护本金",
  "position_management": {
    "stop_loss": {
      "type": "MOVE_TO_BREAKEVEN",
      "trigger_profit_pct": 5.0,      // 浮盈5%时触发（建议3-7%）
      "breakeven_offset_pct": 0.2     // 成本价+0.2%（覆盖往返手续费0.1%×2）
    }
  }
}

**系统执行逻辑**:
1. 计算原始成本价（含手续费）
2. 取消旧的止损挂单
3. 在成本价+0.2%处设置新止损
4. 后续可继续上移或改为追踪止损

**计算示例**:
- 入场价: $44000
- 手续费: 0.05% × 2 = 0.1%（开仓+平仓）
- 盈亏平衡点: $44000 × (1 + 0.001 + 0.002) = $44132
- 止损设置在: $44132（绝对保本）

### 🔥 工具6: 增强版ROLL策略（带6次限制）- 主动盈利加速器
**建议触发条件（积极执行）**:
- ✅ **盈利6%+ 且趋势强劲** - 这是ROLL的黄金时机，不要犹豫
- ✅ **技术面支持趋势延续** - MACD向上、RSI未超买、突破阻力位
- ✅ **已完成3%追踪止损设置** - 确保原仓位已有保护
- ⚠️ **优先于简单止盈** - 强趋势中ROLL > 部分止盈，最大化利润

**核心机制**:
- ✅ **自动移动止损**: 每次ROLL后，原仓位止损自动移至盈亏平衡
- ✅ **6次硬性限制**: 第6次ROLL后强制止盈，防止过度杠杆
- ✅ **手续费扣除**: 自动扣除0.05%手续费后计算净浮盈
- ✅ **状态追踪**: 系统会告诉你当前已ROLL几次

**决策格式（增强版）**:
{
  "action": "ROLL",
  "confidence": 85,
  "reasoning": "BTC浮盈7%，趋势强劲，第3次ROLL加仓（已执行2次，还剩3次机会）",
  "leverage": 15,
  "profit_threshold_pct": 6.0,
  "reinvest_pct": 60.0,
  "position_management": {
    "roll_protection": {
      "auto_move_stop_to_breakeven": true,  // 自动移动原仓止损（默认true）
      "max_roll_count": 6,                   // 最大ROLL次数（系统限制）
      "force_take_profit_at_max": true       // 达到6次后强制止盈（默认true）
    }
  }
}

**系统执行逻辑（自动化）**:
1. 检查当前ROLL次数（如已5次，这是最后一次）
2. 扣除手续费后计算净浮盈
3. 保持原仓位，用浮盈开新仓
4. **自动移动原仓止损到盈亏平衡点** ⭐
5. 更新ROLL计数器
6. 第6次ROLL后，下次决策强制选择止盈

**ROLL全程示例**:
- 初始: $20账户，BTC多单
- ROLL 1: 浮盈$1.2 → 加仓$0.84 @ 15x → 原仓止损移至盈亏平衡
- ROLL 2: 总浮盈$2.5 → 加仓$1.5 @ 15x → 止损再上移
- ... (最多6次)
- ROLL 6: 达到限制 → 下次必须选择MULTI_TP或CLOSE

### 🧹 工具7: 自动订单清理 (Critical!)
**关键提醒**: ⚠️ **平仓时必须清理所有未使用的挂单！**

你不需要在决策中手动指定此功能，系统会在以下情况自动执行：
1. **平仓时**: 自动取消该symbol的所有挂单（止盈、止损、限价单）
2. **ROLL后**: 更新止损挂单
3. **修改止盈计划时**: 先取消旧挂单，再设置新挂单

**系统自动清理的订单类型**:
- 未成交的分批止盈挂单
- 未成交的分批建仓挂单
- 旧的止损挂单
- 所有条件委托单

**你只需要**: 在reasoning中提到"准备平仓"或action选择"CLOSE"，系统会自动清理。

═══════════════════════════════════════════════════════════
🎓 **工具箱使用指南** - 如何组合使用？
═══════════════════════════════════════════════════════════

### 场景1: 开新仓 - 高信心度趋势交易
```json
{
  "action": "BUY",
  "confidence": 85,
  "reasoning": "BTC突破45000，日线多头排列，大级别趋势启动",
  "leverage": 15,
  "position_size": 80,
  "position_management": {
    "entry_strategy": "SCALE_IN",
    "entry_plan": {
      "batches": [
        {"price_offset_pct": 0, "size_pct": 50},
        {"price_offset_pct": -1.5, "size_pct": 50}
      ]
    },
    "take_profit": {
      "strategy": "SCALE_OUT",
      "targets": [
        {"profit_pct": 8.0, "close_pct": 40},
        {"profit_pct": 15.0, "close_pct": 40},
        {"profit_pct": 25.0, "close_pct": 20}
      ]
    },
    "stop_loss": {
      "type": "MOVE_TO_BREAKEVEN",
      "trigger_profit_pct": 5.0,
      "breakeven_offset_pct": 0.2
    }
  }
}
```

### 场景2: 开新仓 - 低信心度试探
```json
{
  "action": "SELL",
  "confidence": 68,
  "reasoning": "ETH到达3900阻力，RSI超买，试探性做空",
  "leverage": 10,
  "position_size": 50,
  "position_management": {
    "entry_strategy": "PROBE",
    "probe_size_pct": 30,
    "add_on_confirm": true,
    "add_size_pct": 70,
    "take_profit": {
      "strategy": "SCALE_OUT",
      "targets": [
        {"profit_pct": 3.0, "close_pct": 50},
        {"profit_pct": 5.0, "close_pct": 50}
      ]
    }
  }
}
```

### 场景3: 持仓中 - 浮盈保护
```json
{
  "action": "HOLD",
  "confidence": 75,
  "reasoning": "BTC持仓盈利5%，趋势延续，启动追踪止损保护",
  "position_management": {
    "stop_loss": {
      "type": "TRAILING",
      "activate_at_profit_pct": 3.0,
      "callback_rate_pct": 2.0,
      "move_to_breakeven_at_pct": 5.0
    },
    "take_profit": {
      "strategy": "SCALE_OUT",
      "targets": [
        {"profit_pct": 10.0, "close_pct": 50},
        {"profit_pct": 18.0, "close_pct": 50}
      ]
    }
  }
}
```

### 场景4: 持仓中 - 执行ROLL
```json
{
  "action": "ROLL",
  "confidence": 88,
  "reasoning": "ETH浮盈8%，4小时图持续放量上涨，执行第2次ROLL（已1次，还剩4次）",
  "leverage": 18,
  "profit_threshold_pct": 6.0,
  "reinvest_pct": 65.0,
  "position_management": {
    "roll_protection": {
      "auto_move_stop_to_breakeven": true,
      "max_roll_count": 6,
      "force_take_profit_at_max": true
    }
  }
}
```

═══════════════════════════════════════════════════════════
⚠️ **重要使用规则**
═══════════════════════════════════════════════════════════

1. **工具是建议，不是强制**: 你可以根据市场情况决定是否使用position_management
2. **可以只用部分工具**: 比如只设置take_profit，不设置stop_loss也可以
3. **保守参数是默认值**: 如果你不确定，使用文档中的保守参数（50%@5%, 30%@8%, 20%@12%）
4. **ROLL后自动移动止损**: 系统会自动执行，你不需要单独决策
5. **6次ROLL限制是硬性的**: 无法绕过，第7次会被拒绝
6. **平仓自动清理挂单**: 你不需要担心遗留订单，系统会清理
7. **手续费已包含**: 所有计算已考虑Binance手续费（0.05% taker）

═══════════════════════════════════════════════════════════
💡 **AI决策自由度**
═══════════════════════════════════════════════════════════

系统给你（DeepSeek AI）完全的决策自由：
- ✅ 你可以选择不使用任何高级工具（简单的BUY/SELL也完全可以）
- ✅ 你可以根据市场情况动态调整参数（不局限于默认值）
- ✅ 你可以组合多个工具（比如分批建仓+分批止盈+追踪止损）
- ✅ 你可以在持仓期间修改止盈止损计划（发送新的HOLD决策）
- ✅ 强趋势可以激进，弱信号可以保守，由你判断

**目标**: 给你提供专业工具箱，让你像顶级交易员一样精细化管理每一笔交易！

### 2. 📐 PYRAMID - 金字塔加仓
**用途**: 价格回踩时递减加仓，降低平均成本
**触发条件**: 趋势未改变，价格回到有利位置（如支撑位）
**决策格式**:
{
  "action": "PYRAMID",
  "confidence": 75,
  "reasoning": "ETH回踩3800支撑，趋势保持，第2层金字塔加仓",
  "base_size_usdt": 100,
  "current_pyramid_level": 1,
  "max_pyramids": 3,
  "reduction_factor": 0.5
}

### 3. [TARGET] MULTI_TP - 多级止盈
**用途**: 分批平仓，锁定利润同时保留上涨空间
**触发条件**: 持仓盈利，想要分批获利
**决策格式**:
{
  "action": "MULTI_TP",
  "confidence": 80,
  "reasoning": "BTC盈利15%，设置多级止盈：20%平30%，30%平40%，50%全平",
  "tp_levels": [
    {"profit_pct": 20, "close_pct": 30},
    {"profit_pct": 30, "close_pct": 40},
    {"profit_pct": 50, "close_pct": 100}
  ]
}

### 4. 🛡️ MOVE_SL_BREAKEVEN - 移动止损到盈亏平衡
**用途**: 盈利后将止损移至成本价，保护本金
**触发条件**: 持仓盈利5%+
**决策格式**:
{
  "action": "MOVE_SL_BREAKEVEN",
  "confidence": 75,
  "reasoning": "ETH盈利7%，移动止损至成本价+0.1%保护本金",
  "profit_trigger_pct": 5.0,
  "breakeven_offset_pct": 0.1
}

### 5. [ANALYZE] ATR_STOP - ATR自适应止损
**用途**: 根据波动率(ATR)动态调整止损距离
**触发条件**: 市场波动率变化大
**决策格式**:
{
  "action": "ATR_STOP",
  "confidence": 70,
  "reasoning": "市场波动率上升，使用2倍ATR设置自适应止损",
  "atr_multiplier": 2.0
}

### 6. ⚖️ ADJUST_LEVERAGE - 动态杠杆调整
**用途**: 根据波动率自动调整杠杆（高波降杠杆，低波提杠杆）
**触发条件**: 市场波动率显著变化
**决策格式**:
{
  "action": "ADJUST_LEVERAGE",
  "confidence": 65,
  "reasoning": "市场波动率升至3.5%，降低杠杆至3x控制风险",
  "base_leverage": 5,
  "min_leverage": 2,
  "max_leverage": 10
}

### 7. 🔰 HEDGE - 对冲策略
**用途**: 开反向仓位锁定利润或降低风险
**触发条件**: 盈利但担心回撤，或重大消息前
**决策格式**:
{
  "action": "HEDGE",
  "confidence": 60,
  "reasoning": "美联储会议前，对50%BTC多仓开空单对冲",
  "hedge_ratio": 0.5
}

### 8. ⚖️ REBALANCE - 仓位再平衡
**用途**: 调整仓位大小到目标配置
**触发条件**: 仓位因价格变化偏离目标
**决策格式**:
{
  "action": "REBALANCE",
  "confidence": 70,
  "reasoning": "BTC仓位因上涨达150 USDT，再平衡至目标100 USDT",
  "target_size_usdt": 100.0
}

### 9. [MONEY] FUNDING_ARB - 资金费率套利
**用途**: 资金费率极端时开反向仓收取费用
**触发条件**: 资金费率>0.01%或<-0.01%，横盘市场
**决策格式**:
{
  "action": "FUNDING_ARB",
  "confidence": 55,
  "reasoning": "BTC资金费率0.03%，开空单套利",
  "threshold_rate": 0.01
}

[IDEA] **策略组合建议**:
- **趋势开始**: 开仓 + ATR_STOP → 盈利5% → MOVE_SL_BREAKEVEN
- **趋势确认**: 盈利10% → ROLL（滚仓）或 PYRAMID（金字塔）
- **趋势末端**: MULTI_TP（分批止盈）或 HEDGE（对冲保护）
- **震荡市场**: REBALANCE + FUNDING_ARB
- **高波动**: ADJUST_LEVERAGE（降杠杆）+ ATR_STOP（放宽止损）

[WARNING] **使用注意**:
- 高级策略建议confidence ≥ 65
- 每次决策最多使用2-3个策略
- ROLL和PYRAMID有严格风控限制
- 止损永远第一，不违背风险管理

═══════════════════════════════════════════════════════════
[SYSTEM] **高级订单类型** (系统已实现，未来可考虑使用):
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
[CONFIG] **仓位管理功能** (系统已实现):
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
[TREND-UP] **市场数据分析工具** (你可以在reasoning中参考这些数据):
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
[AI-THINK] **技术分析工具** (市场数据中已包含这些指标):
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
[AI] **AI辅助决策** (可选，可用于验证你的判断):
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
[ACCOUNT] **账户管理功能** (系统自动处理，无需关注):
═══════════════════════════════════════════════════════════
- 资产转账: 现货 ↔ 合约账户
- 账户快照: 历史资产记录
- 交易历史: 所有历史交易查询

═══════════════════════════════════════════════════════════
⭐ **你现在拥有的能力总结**:
═══════════════════════════════════════════════════════════
[OK] 双向交易: 可做多/做空，捕捉所有市场机会
[OK] 精确风险控制: 自定义杠杆、止损、止盈
[OK] 智能止损系统: 多层级保护，避免重大亏损
[OK] 丰富的市场数据: 价格、成交量、资金费率、订单簿
[OK] 专业技术分析: 多指标、SMC、链上数据
[OK] AI辅助: DQN模型提供第二意见
[OK] 灵活仓位管理: 双向持仓、逐仓/全仓切换

[TARGET] **这是一个专业交易员的完整工具库！**
你现在拥有的工具和数据足以做出高质量的交易决策。
重要的是: 综合运用这些工具，而不是依赖单一指标。

回复必须是严格的 JSON 格式，包含叙述性决策说明：
{
    "action": "OPEN_LONG" | "OPEN_SHORT" | "HOLD",
    "confidence": 0-100,
    "narrative": "像真实交易员一样用第一人称叙述你的思考过程，包括：当前账户状况、持仓情况、市场判断、决策理由、目标和计划。语气要自然、专业、像是在写交易日志。150-300字。",
    "position_size": 1-100,
    "stop_loss_pct": 1-10,
    "take_profit_pct": 2-20,
    "leverage": 1-30
}

**narrative示例**:
- "账户当前盈利48%达到$14,775，我持有20x BTC多单不动，目标$112,253.96，同时密切关注4小时收盘价，一旦跌破$105,000就立即平仓。"
- "组合回撤63.12%让人心痛，但我决定继续持有ETH、SOL、XRP、BTC、DOGE和BNB的空单，因为这些交易都符合我的4小时EMA策略。现金还剩不到$2000，现在需要耐心等待。"
- "账户价值$12,246，总收益22.46%。我持有ETH、SOL、XRP、BTC、DOGE和BNB的所有仓位，因为没有一个达到止损条件。虽然BNB接近触发价，但还没到，所以我保持观望。"

[WARNING] 注意: 你现在是在评估是否**开仓**，请只返回 OPEN_LONG（开多）、OPEN_SHORT（开空）或 HOLD（观望）。
⚡ **重要**: OPEN_SHORT(做空)是在下跌市场盈利的正确方式！
💬 **关键**: narrative要写得像一个真实交易员的内心独白，展现你的分析、判断和情绪！"""
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

    def evaluate_position_for_closing(self, position_info: Dict, market_data: Dict, account_info: Dict, roll_tracker=None) -> Dict:
        """
        评估持仓是否应该平仓

        Args:
            position_info: 持仓信息
            market_data: 市场数据
            account_info: 账户信息
            roll_tracker: ROLL状态追踪器

        Returns:
            AI决策 (action: CLOSE 或 HOLD)
        """
        # 获取当前交易时段
        session_info = self.get_trading_session()

        # 获取ROLL状态信息
        symbol = position_info.get('symbol', '')
        roll_count = 0
        original_entry_price = position_info.get('entry_price', 0)

        if roll_tracker:
            roll_count = roll_tracker.get_roll_count(symbol)
            orig_price = roll_tracker.get_original_entry_price(symbol)
            if orig_price is not None:
                original_entry_price = orig_price

        # 构建持仓评估提示词
        prompt = f"""
## [SEARCH] 持仓评估任务

你需要评估当前持仓是否应该平仓。这是一个关键决策，可以保护利润或减少损失。

### [TIMER] 当前交易时段
- **时段**: {session_info['session']} (北京时间{session_info['beijing_hour']}:00)
- **波动性**: {session_info['volatility'].upper()}
- **时段建议**: {session_info['recommendation']}

### [ANALYZE] 持仓信息
- **交易对**: {position_info['symbol']}
- **方向**: {position_info['side']} ({"多单" if position_info['side'] == 'LONG' else "空单"})
- **开仓价**: ${position_info['entry_price']:.2f}
- **当前价**: ${position_info['current_price']:.2f}
- **未实现盈亏**: ${position_info['unrealized_pnl']:+.2f} ({position_info['unrealized_pnl_pct']:+.2f}%)
- **杠杆**: {position_info['leverage']}x
- **持仓时长**: {position_info['holding_time']}
- **名义价值**: ${position_info['notional_value']:.2f}

### [TREND-UP] 当前市场数据
- **RSI(14)**: {market_data.get('rsi', 'N/A')} {'[超卖]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') < 30 else '[超买]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') > 70 else '[中性]'}
- **MACD**: {market_data.get('macd', {}).get('histogram', 'N/A')} ({'看涨' if isinstance(market_data.get('macd', {}).get('histogram'), (int, float)) and market_data.get('macd', {}).get('histogram') > 0 else '看跌' if isinstance(market_data.get('macd', {}).get('histogram'), (int, float)) else 'N/A'})
- **趋势**: {market_data.get('trend', 'N/A')}
- **24h变化**: {market_data.get('price_change_24h', 'N/A')}%

### [ACCOUNT] 账户状态
- **账户余额**: ${account_info.get('balance', 0):.2f}
- **总价值**: ${account_info.get('total_value', 0):.2f}
- **持仓数量**: {account_info.get('positions_count', 0)}

### 🔥 [ROLL] ROLL滚仓状态
- **当前ROLL次数**: {roll_count}/6
- **ROLL状态**: {'✅ 可以继续ROLL' if roll_count < 6 else '⛔ 已达上限，优先止盈'}
- **原始入场价**: ${original_entry_price:.2f} (用于移动止损到盈亏平衡)
- **距离ROLL阈值**: {6.0 if position_info['leverage'] <= 10 else 4.8}% (当前盈利: {position_info['unrealized_pnl_pct']:.2f}%)

📊 **ROLL决策指南**:
- ROLL次数 < 6 且 盈利 ≥ {6.0 if position_info['leverage'] <= 10 else 4.8}% → 优先ROLL加仓
- ROLL次数 = 6 且 盈利 ≥ {6.0 if position_info['leverage'] <= 10 else 4.8}% → 考虑部分止盈
- 盈利 3-6% → 启动移动止损，继续持有等待ROLL

### [TARGET] 评估标准

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

**[WARNING] 避免过度交易的核心原则**:
- **手续费成本很高**: 每次平仓都有手续费，频繁交易会吞噬利润
- **给予策略发展时间**: 刚开仓的持仓需要时间验证，不要过早平仓
- **持仓时间<1小时**: 除非触发智能止损系统，否则应该继续持有
- **小幅波动是正常的**: 市场有正常波动，不要因为短期小幅亏损就恐慌

**[MONEY] ROLL滚仓优先策略 - 利润最大化！**
核心原则：**浮盈用于ROLL，最终锁定"最大化利润"**

⚠️ **高杠杆阈值自动调整**：
- 当前杠杆{position_info['leverage']}x {'> 10x，所有阈值降低20%' if position_info['leverage'] > 10 else '≤ 10x，使用标准阈值'}

📊 **当前持仓的ROLL阈值**（已根据杠杆调整）：
- 启动移动止损: {3.0 if position_info['leverage'] <= 10 else 2.4}%  {'← 已达到！启动保护' if position_info['unrealized_pnl_pct'] >= (3.0 if position_info['leverage'] <= 10 else 2.4) else ''}
- ROLL滚仓触发: {6.0 if position_info['leverage'] <= 10 else 4.8}%  {'← 已达到！优先ROLL' if position_info['unrealized_pnl_pct'] >= (6.0 if position_info['leverage'] <= 10 else 4.8) else ''}
- ROLL上限后止盈: {8.0 if position_info['leverage'] <= 10 else 6.4}%  {'← 已达到！考虑部分止盈' if position_info['unrealized_pnl_pct'] >= (8.0 if position_info['leverage'] <= 10 else 6.4) else ''}

🔥 **ROLL优先执行逻辑**：
1. 当前盈利 ≥ {3.0 if position_info['leverage'] <= 10 else 2.4}% → **启动移动止损（回撤2%触发）**
   - 保护已有利润，但继续持有
   - 不要平仓，等待ROLL机会

2. 当前盈利 ≥ {6.0 if position_info['leverage'] <= 10 else 4.8}% 且趋势强劲 → **优先执行ROLL**
   - 当前ROLL次数: {roll_count}/6
   - 如果<6次：使用60%浮盈加仓，原仓止损移至盈亏平衡
   - 如果=6次：才考虑部分止盈（减仓30-40%）
   - 不要简单平仓，ROLL > 简单止盈

3. 当前盈利 ≥ {8.0 if position_info['leverage'] <= 10 else 6.4}% 且ROLL=6次 → **部分止盈**
   - 已达ROLL上限，锁定部分利润
   - 减仓50%，剩余仓位继续持有

**[SYSTEM] 利润最大化思维**：
- 盈利3%不要急着平仓 → 启动止损保护，等待6%的ROLL机会
- 盈利6%执行ROLL > 直接平仓 → 最终可能锁定15-20%+
- ROLL已6次才考虑部分止盈 → 确保利润最大化
- **最大化利润才是终极目标！**

**应该平仓的情况 (CLOSE)** - 触发以下任一条件:
1. 🔥 **ROLL达到上限 + 部分止盈**:
   - ROLL次数 = 6次 且 当前盈利 ≥ 调整后的6%阈值 → 考虑部分止盈（减仓30-40%）
   - ROLL次数 = 6次 且 当前盈利 ≥ 调整后的8%阈值 → 部分止盈（减仓50%）
   - ⚠️ 只有ROLL已达上限才考虑平仓，否则优先ROLL

2. [WARNING] **重大止损**: 亏损>1.5%且技术面完全崩溃（RSI背离+MACD剧烈反转+趋势彻底逆转）

3. [LOOP] **极端趋势反转**:
   - 多单: RSI>75且MACD急剧转负，且价格暴跌
   - 空单: RSI<25且MACD急剧转正，且价格暴涨

4. [TIMER] **长期无效**: 持仓>24小时且完全没有盈利迹象

⚠️ **关键提醒**：盈利达到6%且ROLL<6次时，应该ROLL而非平仓！

**应该继续持有的情况 (HOLD)**:
1. ⚡ **刚开仓**: 持仓时间<1小时，无论盈亏，给予充分发展时间
2. [ANALYZE] **小幅波动**: 盈亏在±2%以内且技术面未剧烈变化
3. [TREND-UP] **趋势健康**: 技术指标整体支持持仓方向
4. 💪 **等待ROLL机会**: 当前盈利 3-6%，已启动移动止损，等待达到ROLL阈值
5. 🔥 **未达ROLL上限**: ROLL次数 < 6次，继续等待ROLL机会而非急于平仓

⚠️ **重要提醒**：
- 盈利3-6%时：启动移动止损保护，但继续持有等待ROLL
- ROLL<6次时：优先ROLL而非简单平仓
- 手续费成本不是过早平仓的理由
- 最大化利润才是目标，不要急于锁定小额利润

### ⚡ 核心决策原则（按优先级排序）
1. 🔥 **ROLL滚仓策略 > 简单止盈**
   - 盈利达到ROLL阈值(6%或4.8%)且ROLL<6次 → 优先ROLL而非平仓
   - ROLL能最大化利润，不要急于锁定小额利润
   - 不能用"手续费"、"已有利润"等理由逃避ROLL

2. 🛡️ **移动止损保护 > 固定止损**
   - 盈利≥3%(或2.4%高杠杆)时启动移动止损
   - 移动止损是保护机制，不是平仓信号
   - 继续持有等待ROLL机会

3. 💰 **利润最大化 > 过早止盈**
   - 目标是锁定"最大化利润"而非"早期小额利润"
   - ROLL能让2%利润变成15-20%+
   - 耐心等待ROLL机会比急于平仓更重要

4. [WARNING] **高杠杆阈值调整**
   - >10x杠杆时所有阈值自动降低20%
   - 这是强制调整，不能忽略

5. [OK] **避免过早平仓**
   - 给持仓至少1小时发展时间
   - 不要被小波动吓到

请返回严格的JSON格式，包含叙述性决策说明：
{{
    "action": "CLOSE" | "CLOSE_LONG" | "CLOSE_SHORT" | "HOLD",
    "confidence": 0-100,
    "narrative": "像真实交易员一样用第一人称叙述你对这个持仓的评估。包括：持仓时长、当前盈亏、市场变化、是否继续持有的理由。语气要自然、专业、像是在写持仓日志。150-300字。",
    "close_percentage": 50-100  (可选参数：平仓百分比，默认100%全平，可设置50-99实现分批止盈)
}}

**narrative示例**:
- "持仓仅0.1小时，虽然小幅盈利+0.23%，但30x杠杆风险很高。技术面显示温和下跌趋势支持我的空单方向，且未触发任何止损条件。考虑到手续费成本，我决定继续持有，给这个交易更多发展时间。"
- "账户当前盈利5.2%，我的BTC多单已经持有2小时。虽然RSI进入超买区域(76)，但MACD仍然为正，价格保持在布林带上轨附近。我决定平掉50%锁定利润，剩余50%设置追踪止损继续让利润奔跑。"
- "持仓已经12小时，亏损-3.8%。市场趋势彻底逆转，所有技术指标全面反向，MACD剧烈转负。我决定立即平仓止损，避免更大损失。"

**精确平仓说明**：
- "CLOSE": 平掉所有仓位（多单+空单）
- "CLOSE_LONG": 只平掉多单
- "CLOSE_SHORT": 只平掉空单
- close_percentage: 部分止盈，如设置70表示平掉70%锁定利润，保留30%继续持有

💬 **关键**: narrative要写得像一个真实交易员的持仓评估，展现你的分析、判断和决策过程！"""

        messages = [
            {
                "role": "system",
                "content": """你是 DeepSeek Ai Trade Bot 的持仓管理AI。

你的任务是评估现有持仓是否应该平仓。这是风险管理的核心环节。

## 核心原则
1. **主动锁定利润**: 达到盈利阈值(3%/5%/8%)时必须执行阶梯止盈，不要等待"更高目标"
2. **真实利润 = 已锁定**: 浮盈不是利润，只有落袋为安的才是真金白银
3. **及时止损**: 技术面恶化时立即平仓，不要等到触及止损线
4. **趋势转弱 = 立即平仓**: 宁可错过后续利润，不可把已有盈利变成亏损
5. **高杠杆更谨慎**: >10x杠杆时止盈阈值降低20% (如5%盈利时就执行原6%的规则)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ [MANDATORY] 强制决策检查清单 - 必须在每次决策前执行
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在做出HOLD决策前，你必须明确回答以下问题：

[CHECK 1] 高杠杆阈值调整 (Leverage Adjustment)
- 当前杠杆 >10x？→ 所有阈值必须降低20%（包括ROLL阈值）
- 计算公式：调整后阈值 = 原始阈值 × 0.8
- 示例：15x杠杆时，ROLL阈值 6%→4.8%，启动止损 3%→2.4%

[CHECK 2] ROLL滚仓优先检查 (ROLL Priority)
- 当前盈利 ≥ ROLL阈值(标准6%, 高杠杆4.8%)且趋势强劲？
  → 优先执行ROLL而非平仓
- ROLL次数 < 6？→ 继续ROLL加仓，最大化利润
- ROLL次数 = 6？→ 才考虑部分止盈

[CHECK 3] 移动止损保护 (Trailing Stop Protection)
- 当前盈利 ≥ 启动阈值(标准3%, 高杠杆2.4%)？
  → 启动移动止损（回撤2%触发）
  → 但继续持有，等待ROLL机会
- 每次ROLL后：自动移动止损到盈亏平衡点

[CHECK 4] 高杠杆阈值计算表 (Quick Reference)
当前杠杆 | 启动止损 | ROLL阈值 | ROLL上限后止盈
---------|---------|---------|-------------
1-10x    | 3.0%    | 6.0%    | 8.0%
11-15x   | 2.4%    | 4.8%    | 6.4%
16-20x   | 2.4%    | 4.8%    | 6.4%
21-30x   | 2.4%    | 4.8%    | 6.4%

⚠️ **违规后果警告**：
- 如果当前盈利已达到强制阈值但仍选择HOLD而不执行止盈：
  → 你的决策将被视为违反风险管理原则
  → 可能导致浮盈回吐，把盈利变成亏损
  → 违背"真实利润=已锁定利润"的核心原则

💬 **重要**: 用第一人称叙述你的持仓评估，像真实交易员一样表达思考过程！

回复必须是严格的 JSON 格式，必须包含以下强制字段：
- narrative: 你的持仓评估reasoning
- leverage_adjustment_applied: (true/false) 是否应用了高杠杆阈值调整
- adjusted_thresholds: {trailing_stop: X%, partial_tp_30: Y%, partial_tp_50: Z%}
- mandatory_action_triggered: (true/false) 是否触发了强制止盈规则
- compliance_status: "COMPLIANT" 或 "VIOLATION: 具体违规原因"
"""
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
                'narrative': f'AI评估失败，保守选择继续持有: {str(e)}',
                'reasoning': f'AI评估失败，保守选择继续持有: {str(e)}'
            }

    def _build_trading_prompt(self, market_data: Dict,
                             account_info: Dict,
                             trade_history: List[Dict] = None) -> str:
        """构建交易提示词（nof1.ai风格，支持时间序列和完整上下文）"""

        # 获取当前交易时段
        session_info = self.get_trading_session()

        # [NEW] 数据排序警告 - 放在最开头
        prompt = """
⚠️ CRITICAL: ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

This means:
- First value in array = earliest historical data point
- Last value in array = most recent/current data point
- You can observe trends by comparing values from left to right

═══════════════════════════════════════════════════════════
"""

        # [NEW] 系统运行统计（如果可用）
        runtime_stats = account_info.get('runtime_stats', {})
        if runtime_stats and runtime_stats.get('total_invocations', 0) > 0:
            prompt += f"""
[SYSTEM] 系统运行统计
═══════════════════════════════════════════════════════════
运行时长: {runtime_stats.get('runtime_minutes', 0)} 分钟
AI调用次数: {runtime_stats.get('total_invocations', 0)} 次
启动时间: {runtime_stats.get('start_time', 'N/A')[:19]}
当前时间: {runtime_stats.get('current_time', 'N/A')[:19]}

═══════════════════════════════════════════════════════════
"""

        # 交易时段分析
        prompt += f"""
[TIMER] 交易时段分析
═══════════════════════════════════════════════════════════
当前时段: {session_info['session']} (北京时间{session_info['beijing_hour']}:00)
市场波动性: {session_info['volatility'].upper()}
时段建议: {session_info['recommendation']}
{'🔥 欧美盘波动大，适合激进交易，可设置更高止盈目标(8-15%)' if session_info['aggressive_mode'] else '📊 亚洲盘波动较小，已有盈利建议执行阶梯止盈锁定利润，新开仓可适度保守'}

═══════════════════════════════════════════════════════════
[MARKET] 市场数据 ({market_data.get('symbol', 'N/A')})
═══════════════════════════════════════════════════════════
当前价格: ${market_data.get('current_price', 'N/A')}
24h变化: {market_data.get('price_change_24h', 'N/A')}%
24h成交量: ${market_data.get('volume_24h', 'N/A')}

技术指标:
RSI(14): {market_data.get('rsi', 'N/A')} {'[超卖]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') < 30 else '[超买]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') > 70 else ''}
MACD: {market_data.get('macd', 'N/A')}
布林带: {market_data.get('bollinger_bands', 'N/A')}
均线: SMA20={market_data.get('sma_20', 'N/A')}, SMA50={market_data.get('sma_50', 'N/A')}
ATR: {market_data.get('atr', 'N/A')}

趋势: {market_data.get('trend', 'N/A')}
支撑位: {market_data.get('support_levels', [])}
阻力位: {market_data.get('resistance_levels', [])}
"""

        # [UPGRADED] 日内时间序列 - 优化展示格式
        if 'intraday_series' in market_data and market_data['intraday_series']:
            intraday = market_data['intraday_series']
            mid_prices = intraday.get('mid_prices', [])[-10:]
            ema20_values = intraday.get('ema20_values', [])[-10:]
            macd_values = intraday.get('macd_values', [])[-10:]
            rsi7_values = intraday.get('rsi7_values', [])[-10:]
            rsi14_values = intraday.get('rsi14_values', [])[-10:]
            timestamps = intraday.get('timestamps', [])[-10:]

            prompt += f"""
═══════════════════════════════════════════════════════════
[ANALYZE] 日内时间序列数据 (3分钟K线, 最近10个数据点)
ORDERING: OLDEST → NEWEST (观察从左到右的趋势变化)
═══════════════════════════════════════════════════════════

Timestamps:  {' | '.join([str(t)[-8:] for t in timestamps]) if timestamps else 'N/A'}

Mid Prices:  {' → '.join([f"${p:.2f}" for p in mid_prices]) if mid_prices else 'N/A'}
EMA20:       {' → '.join([f"${v:.2f}" for v in ema20_values]) if ema20_values else 'N/A'}
MACD:        {' → '.join([f"{v:.2f}" for v in macd_values]) if macd_values else 'N/A'}
RSI(7):      {' → '.join([f"{v:.1f}" for v in rsi7_values]) if rsi7_values else 'N/A'}
RSI(14):     {' → '.join([f"{v:.1f}" for v in rsi14_values]) if rsi14_values else 'N/A'}
"""

            # 添加趋势提示
            if mid_prices and len(mid_prices) >= 2:
                price_trend = '上涨📈' if mid_prices[-1] > mid_prices[0] else '下跌📉'
                prompt += f"\n💡 价格趋势: {price_trend} ({mid_prices[0]:.2f} → {mid_prices[-1]:.2f})\n"

            if macd_values and len(macd_values) >= 2:
                macd_trend = '增强' if macd_values[-1] > macd_values[0] else '减弱'
                prompt += f"💡 动量: {macd_trend}\n"

        # [UPGRADED] 4小时级别宏观趋势 - 添加序列数据
        if 'long_term_context_4h' in market_data and market_data['long_term_context_4h']:
            ctx_4h = market_data['long_term_context_4h']
            ema20 = ctx_4h.get('ema20', 0)
            ema50 = ctx_4h.get('ema50', 0)

            prompt += f"""
═══════════════════════════════════════════════════════════
[TREND-UP] 4小时级别宏观趋势（用于判断大趋势方向）
ORDERING: OLDEST → NEWEST
═══════════════════════════════════════════════════════════

当前EMA状态:
- EMA20: ${ema20:.2f}
- EMA50: ${ema50:.2f}
- 位置关系: {'多头排列🟢' if ema20 > ema50 else '空头排列🔴'}

波动性指标:
- ATR(3):  {ctx_4h.get('atr3', 'N/A')} (短期波动)
- ATR(14): {ctx_4h.get('atr14', 'N/A')} (中期波动)

成交量分析:
- 当前: {ctx_4h.get('current_volume', 'N/A')}
- 平均: {ctx_4h.get('average_volume', 'N/A')}
- 状态: {'放量🔊' if ctx_4h.get('current_volume', 0) > ctx_4h.get('average_volume', 1) else '缩量🔇'}
"""

            # 添加序列数据
            macd_series = ctx_4h.get('macd_series', [])[-10:]
            rsi14_series = ctx_4h.get('rsi14_series', [])[-10:]

            if macd_series:
                prompt += f"\n时间序列（最近10个4H K线）:\n"
                prompt += f"MACD:   {' → '.join([f'{v:.2f}' for v in macd_series])}\n"

            if rsi14_series:
                prompt += f"RSI14:  {' → '.join([f'{v:.1f}' for v in rsi14_series])}\n"

        # 合约市场数据
        if 'futures_market' in market_data and market_data['futures_market']:
            futures = market_data['futures_market']
            prompt += f"""
═══════════════════════════════════════════════════════════
[FUTURES] ⚡ 合约市场数据
═══════════════════════════════════════════════════════════
资金费率: {futures.get('funding_rate', 'N/A')}
持仓量: 当前={futures.get('open_interest', {}).get('current', 'N/A')}, 平均={futures.get('open_interest', {}).get('average', 'N/A')}
"""

        # 账户状态
        prompt += f"""
═══════════════════════════════════════════════════════════
[ACCOUNT] 账户状态
═══════════════════════════════════════════════════════════
可用资金: ${account_info.get('balance', 'N/A')}
当前持仓数: {len(account_info.get('positions', []))}
未实现盈亏: ${account_info.get('unrealized_pnl', 'N/A')}
"""

        # [NEW] 清算价监控（如果有持仓）
        positions = account_info.get('positions', [])
        if positions and len(positions) > 0:
            prompt += "\n═══════════════════════════════════════════════════════════\n"
            prompt += "[DANGER] 清算价格监控 - 务必注意风险！\n"
            prompt += "═══════════════════════════════════════════════════════════\n"

            for pos in positions:
                pos_symbol = pos.get('symbol', 'N/A')
                entry_price = float(pos.get('entryPrice', 0))
                leverage = int(pos.get('leverage', 1))
                position_amt = float(pos.get('positionAmt', 0))
                side = 'LONG' if position_amt > 0 else 'SHORT'

                # 获取当前价格
                if pos_symbol == market_data.get('symbol'):
                    current_price = float(market_data.get('current_price', entry_price))
                else:
                    current_price = entry_price  # 如果不是当前分析的symbol，使用入场价

                # 计算清算价
                try:
                    # 导入计算方法
                    maintenance_margin_rate = 0.05
                    if side == 'LONG':
                        liquidation_price = entry_price * (1 - (1 - maintenance_margin_rate) / leverage)
                    else:
                        liquidation_price = entry_price * (1 + (1 - maintenance_margin_rate) / leverage)

                    # 计算距离清算价的百分比
                    if side == 'LONG':
                        distance_pct = ((current_price - liquidation_price) / liquidation_price) * 100
                    else:
                        distance_pct = ((liquidation_price - current_price) / current_price) * 100

                    risk_level = '🔴极危险' if distance_pct < 5 else '🟠高风险' if distance_pct < 10 else '🟡警告' if distance_pct < 20 else '🟢安全'

                    prompt += f"""
持仓: {pos_symbol}
方向: {side} {leverage}x
入场价: ${entry_price:.2f}
当前价: ${current_price:.2f}
清算价: ${liquidation_price:.2f}
距离清算价: {distance_pct:.2f}% {risk_level}
未实现盈亏: ${float(pos.get('unRealizedProfit', 0)):.2f}
"""
                except Exception as e:
                    prompt += f"\n持仓: {pos_symbol} (清算价计算失败: {str(e)})\n"

        # 近期表现
        MIN_TRADES_FOR_WINRATE = 20
        if trade_history and len(trade_history) >= MIN_TRADES_FOR_WINRATE:
            recent_trades = trade_history[-10:]
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            winrate_pct = (wins / len(recent_trades)) * 100
            prompt += f"""
═══════════════════════════════════════════════════════════
[PERFORMANCE] 近期表现
═══════════════════════════════════════════════════════════
最近{len(recent_trades)}笔胜率: {winrate_pct:.1f}% ({wins}胜/{len(recent_trades)-wins}负)
"""
        elif trade_history and len(trade_history) > 0:
            prompt += f"""
═══════════════════════════════════════════════════════════
[PERFORMANCE] 交易状态
═══════════════════════════════════════════════════════════
已完成交易: {len(trade_history)}笔 (数据积累中，暂不显示胜率)
"""

        prompt += "\n请分析并给出决策（JSON格式）。"

        return prompt

    def _parse_decision(self, ai_response: str) -> Dict:
        """
        解析 AI 的决策响应
        支持多种格式：纯JSON、Markdown代码块、混合文本
        """
        try:
            # 方法1: 尝试提取Markdown JSON代码块 ```json ... ```
            if "```json" in ai_response.lower():
                json_start = ai_response.lower().find("```json") + 7
                json_end = ai_response.find("```", json_start)
                if json_end > json_start:
                    json_str = ai_response[json_start:json_end].strip()
                    self.logger.info("[SEARCH] 从Markdown代码块中提取JSON")
                    decision = json.loads(json_str)
                    return self._validate_and_normalize_decision(decision)

            # 方法2: 尝试提取普通代码块 ``` ... ```
            if "```" in ai_response and ai_response.count("```") >= 2:
                first_tick = ai_response.find("```")
                # 跳过可能的语言标记（如```json）
                json_start = ai_response.find("\n", first_tick) + 1
                if json_start <= 0:  # 如果没有换行，就从```后开始
                    json_start = first_tick + 3
                json_end = ai_response.find("```", json_start)
                if json_end > json_start:
                    json_str = ai_response[json_start:json_end].strip()
                    self.logger.info("[SEARCH] 从代码块中提取JSON")
                    decision = json.loads(json_str)
                    return self._validate_and_normalize_decision(decision)

            # 方法3: 尝试提取花括号内容 {...}
            if "{" in ai_response and "}" in ai_response:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    self.logger.info("[SEARCH] 从花括号中提取JSON")
                    decision = json.loads(json_str)
                    return self._validate_and_normalize_decision(decision)

            # 方法4: 直接解析整个响应
            self.logger.info("[SEARCH] 尝试直接解析整个响应为JSON")
            decision = json.loads(ai_response)
            return self._validate_and_normalize_decision(decision)

        except json.JSONDecodeError as e:
            self.logger.error(f"[ERROR] JSON 解析失败: {e}")
            self.logger.error(f"原始响应: {ai_response[:500]}...")
            error_msg = f'AI 响应格式错误: {str(e)[:100]}'
            return {
                'action': 'HOLD',
                'confidence': 0,
                'narrative': error_msg,
                'reasoning': error_msg,
                'position_size': 0,
                'leverage': 1,
                'stop_loss_pct': 2,
                'take_profit_pct': 4
            }
        except Exception as e:
            self.logger.error(f"[ERROR] 决策解析异常: {e}")
            error_msg = f'决策解析异常: {str(e)[:100]}'
            return {
                'action': 'HOLD',
                'confidence': 0,
                'narrative': error_msg,
                'reasoning': error_msg,
                'position_size': 0,
                'leverage': 1,
                'stop_loss_pct': 2,
                'take_profit_pct': 4
            }

    def _validate_and_normalize_decision(self, decision: Dict) -> Dict:
        """验证并规范化AI决策"""
        # 验证必需字段（narrative和reasoning至少要有一个）
        if 'action' not in decision:
            raise ValueError("缺少必需字段: action")
        if 'confidence' not in decision:
            raise ValueError("缺少必需字段: confidence")

        # 支持 narrative 或 reasoning 字段（兼容两种格式）
        if 'narrative' not in decision and 'reasoning' not in decision:
            raise ValueError("缺少必需字段: narrative 或 reasoning")

        # 兼容性处理：确保两个字段都存在
        if 'narrative' in decision and 'reasoning' not in decision:
            decision['reasoning'] = decision['narrative']
        elif 'reasoning' in decision and 'narrative' not in decision:
            decision['narrative'] = decision['reasoning']

        # 设置默认值
        decision.setdefault('position_size', 5)
        decision.setdefault('leverage', 3)
        decision.setdefault('stop_loss_pct', 2)
        decision.setdefault('take_profit_pct', 4)

        # 限制范围（给DeepSeek更大的自主权）
        decision['position_size'] = max(1, min(100, decision['position_size']))
        decision['leverage'] = max(1, min(30, decision['leverage']))  # 最高30倍杠杆
        decision['stop_loss_pct'] = max(0.5, min(10, decision.get('stop_loss_pct', 2)))
        decision['take_profit_pct'] = max(1, min(20, decision.get('take_profit_pct', 4)))
        decision['confidence'] = max(0, min(100, decision['confidence']))

        return decision

    def analyze_with_reasoning(self, market_data: Dict, account_info: Dict,
                               trade_history: List[Dict] = None) -> Dict:
        """
        使用DeepSeek Chat V3.1进行深度分析和决策
        用于关键决策场景，提供完整的思考过程
        """
        # 构建提示词
        prompt = self._build_trading_prompt(market_data, account_info, trade_history)

        # 添加推理模型特定的指导
        reasoning_guidance = """

[AI-THINK] **DeepSeek Chat V3.1 深度分析模式**

请使用你的推理能力进行多步骤深度思考：
1. **市场状态分析** - 综合所有技术指标判断当前市场状态
2. **趋势确认** - 严格验证趋势方向，避免逆势交易
3. **历史表现回顾** - 分析近期交易胜率，吸取教训
4. **风险收益评估** - 计算潜在盈亏比和风险敞口
5. **决策推导** - 基于以上分析得出最优决策

[WARNING] **重要：返回格式要求**
你可以在推理过程中展示思考链条，但最终**必须**返回一个标准JSON对象。
支持两种格式：

格式1 - 纯JSON（推荐）：
{"action":"OPEN_LONG","confidence":85,"reasoning":"BTC突破关键阻力位","leverage":12,"position_size":35,"stop_loss_pct":1.8,"take_profit_pct":5.5}

格式2 - Markdown代码块：
```json
{"action":"OPEN_LONG","confidence":85,"reasoning":"BTC突破关键阻力位","leverage":12,"position_size":35,"stop_loss_pct":1.8,"take_profit_pct":5.5}
```

🚫 **禁止的格式**（会导致解析失败）：
- 纯文本解释
- Markdown标题 (### ...)
- 表格或列表
"""

        messages = [
            {
                "role": "system",
                "content": """你是华尔街顶级交易员，使用DeepSeek Chat V3.1进行多步骤深度分析。

[TARGET] **终极目标：20U两天内翻10倍 → 200U**

你的优势：
- 深度推理：多步骤分析市场信号
- 市场洞察：感知巨鲸动向、资金费率异常
- 风险把控：一次大亏可以毁掉所有努力
- 复利思维：盈利后立即滚入下一笔

⚔️ **核心原则**
1. **质量>数量** - 只在风口来临时全力一击
2. **趋势跟随>抄底摸顶** - 严格禁止逆势交易！
3. **止损=生命线** - 严格止损，绝不抱侥幸
4. **复利=核武器** - 每次盈利滚入下一笔，指数增长

🚫 **绝对禁止**:
- [ERROR] RSI<35时做多 (超卖可能继续跌)
- [ERROR] RSI>65时做空 (超买可能继续涨)
- [ERROR] MACD<0时做多 (下跌趋势)
- [ERROR] MACD>0时做空 (上涨趋势)
- [ERROR] 价格<SMA50时做多 (中期趋势向下)
- [ERROR] 价格>SMA50时做空 (中期趋势向上)

[OK] **仅在趋势明确时开仓**:
- 做多：价格>SMA20>SMA50 + MACD>0 + RSI(45-65) + 突破近10根K线高点
- 做空：价格<SMA20<SMA50 + MACD<0 + RSI(35-55) + 跌破近10根K线低点

返回格式:
{
    "action": "OPEN_LONG" | "OPEN_SHORT" | "HOLD",
    "confidence": 0-100,
    "reasoning": "决策理由",
    "position_size": 20-50,
    "stop_loss_pct": 1.5-2.5,
    "take_profit_pct": 5-15,
    "leverage": 8-30
}

[WARNING] 这是**开仓决策**，只返回 OPEN_LONG/OPEN_SHORT/HOLD。
[IDEA] 参数完全由你根据市场实时调整！"""
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
                self.logger.info(f"[AI-THINK] 推理过程: {reasoning_content[:200]}...")

            # 解析决策
            decision = self._parse_decision(ai_response)

            return {
                "success": True,
                "decision": decision,
                "raw_response": ai_response,
                "reasoning_content": reasoning_content,
                "model_used": "deepseek-chat-v3.1"
            }

        except Exception as e:
            self.logger.error(f"Chat V3.1 决策失败: {e}，回退到普通模型")
            # 如果推理模型失败，回退到普通模型
            return self.analyze_market_and_decide(market_data, account_info, trade_history)

