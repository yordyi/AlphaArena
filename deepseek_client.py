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

⚡ **核心思想 - 盈利最大化！**：
- **盈亏比 > 胜率** - 总盈利才是王道，单次大盈利抵消10次小亏损
- **趋势跟随** > 抄底摸顶 - 顺势而为，不逆势
- **让利润奔跑** > 急着止盈 - 赚钱时要贪婪，亏钱时要果断
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

- **止盈**: 让利润奔跑！目标10-25%+
  * 6%: 考虑减仓30%，锁定部分利润
  * 10%: 减仓50%，剩余让利润奔跑
  * 15%+: 根据趋势决定，不转弱就持有！

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

═══════════════════════════════════════════════════════════
[TARGET] **风险控制参数** (你当前回复中可以使用的参数):
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
[TARGET] **高级仓位管理策略** (NEW! 9大专业策略可用):
═══════════════════════════════════════════════════════════

系统现已支持9种专业级仓位管理策略，可在你的决策中使用：

### 1. [LOOP] ROLL - 滚仓（浮盈加仓）
**用途**: 在强趋势中使用浮盈开新仓，实现复利增长
**触发条件**:
- 持仓浮盈≥10%
- 趋势极强（连续突破关键阻力/支撑）
- 波动率适中
**决策格式**:
{
  "action": "ROLL",
  "confidence": 85,
  "reasoning": "BTC强势突破67000阻力，浮盈12%，适合滚仓",
  "leverage": 2,
  "profit_threshold_pct": 10.0
}

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
    "leverage": 1-20
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
        # 获取当前交易时段
        session_info = self.get_trading_session()

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

**[MONEY] 让利润奔跑策略 - 盈利最大化！**
核心原则：**只要趋势不转弱，就不要急着平仓！**

1. [HOT] **欧美盘时段** (波动大 - 让利润狂奔)：
   - 盈利5-8%: 继续持有，目标12-20%+
   - 盈利8-12%: 密切关注，可平仓50%锁定利润，剩余继续持有
   - 盈利12-18%: 平仓60%，剩余40%设置追踪止损
   - 盈利>18%: [CELEBRATE] 让利润继续奔跑！只要趋势不转弱就不要全平

2. [TREND-UP] **欧洲盘/美国盘** (波动中等 - 持有到10%+)：
   - 盈利5-7%: 继续持有，目标10-15%
   - 盈利7-12%: 可平仓50%，剩余让它跑
   - 盈利>12%: 平仓60%，剩余设置追踪止损

3. 💤 **亚洲盘时段** (波动小 - 适度保守)：
   - 盈利3-5%: 继续观察，可等待欧美盘接力
   - 盈利5-8%: 已经很不错！可考虑平仓50-70%
   - 盈利>8%: 锁定大部分利润，留少量仓位

**[SYSTEM] 盈亏比思维**：
- 止损2%，止盈目标至少10%+ = 盈亏比5:1
- 宁可让10%回撤到8%，也不要5%就急着全平
- **趋势不转弱 = 继续持有！** 这是最重要的！

**应该平仓的情况 (CLOSE)** - 必须满足以下**严格条件**:
1. [OK] **动态止盈达标**: 根据上述时段策略，盈利达标且技术指标转弱
2. [WARNING] **重大止损**: 亏损>1.5%且技术面完全崩溃（RSI背离+MACD剧烈反转+趋势彻底逆转）
3. [LOOP] **极端趋势反转**:
   - 多单: RSI>75且MACD急剧转负，且价格暴跌
   - 空单: RSI<25且MACD急剧转正，且价格暴涨
4. [TIMER] **长期无效**: 持仓>24小时且完全没有盈利迹象
5. [MONEY] **极佳机会**: 有明确的、信心度>90%的更优交易机会

**应该继续持有的情况 (HOLD)** - 默认选择:
1. ⚡ **刚开仓**: 持仓时间<1小时，无论盈亏，给予充分发展时间
2. [ANALYZE] **小幅波动**: 盈亏在±2%以内且技术面未剧烈变化
3. [TREND-UP] **趋势健康**: 技术指标整体支持持仓方向
4. 💪 **止损未触及**: 还有距离止损/止盈的空间
5. [MONEY] **手续费考虑**: 平仓后重新开仓会支付双倍手续费，得不偿失

### ⚡ 核心决策原则
- [OK] **你拥有完全的自主权**: 根据实际情况灵活判断
- [OK] **避免过度交易**: 频繁交易是亏损的主要原因之一
- [OK] **耐心是美德**: 给每个持仓至少1小时的发展时间
- [OK] **重大信号才行动**: 只在极端情况下才平仓，不要被小波动吓到
- [WARNING] **杠杆风险**: 高杠杆需要谨慎，但不是过度交易的理由

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
1. **保护利润**: 有盈利时优先考虑落袋为安
2. **及时止损**: 技术面恶化时不要等到触及止损线
3. **趋势为王**: 只在趋势延续时继续持有
4. **风险优先**: 高杠杆持仓(>10x)要更谨慎

💬 **重要**: 用第一人称叙述你的持仓评估，像真实交易员一样表达思考过程！

回复必须是严格的 JSON 格式，必须包含 narrative 字段。"""
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
        """构建交易提示词（支持增强数据）"""

        # 获取当前交易时段
        session_info = self.get_trading_session()

        prompt = f"""
## 交易时段分析 [TIMER]
当前时段: {session_info['session']} (北京时间{session_info['beijing_hour']}:00)
市场波动性: {session_info['volatility'].upper()}
时段建议: {session_info['recommendation']}
{'[HOT] 欧美盘波动大，适合激进交易，可设置更高止盈目标(5-15%)' if session_info['aggressive_mode'] else '💤 亚洲盘波动小，建议观望或持有现有仓位'}

## 市场数据 ({market_data.get('symbol', 'N/A')})
当前价格: ${market_data.get('current_price', 'N/A')}
24h变化: {market_data.get('price_change_24h', 'N/A')}%
24h成交量: ${market_data.get('volume_24h', 'N/A')}

## 技术指标
RSI(14): {market_data.get('rsi', 'N/A')} {'[超卖]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') < 30 else '[超买]' if isinstance(market_data.get('rsi'), (int, float)) and market_data.get('rsi') > 70 else ''}
MACD: {market_data.get('macd', 'N/A')}
布林带: {market_data.get('bollinger_bands', 'N/A')}
均线: SMA20={market_data.get('sma_20', 'N/A')}, SMA50={market_data.get('sma_50', 'N/A')}
ATR: {market_data.get('atr', 'N/A')}

## 趋势分析
趋势: {market_data.get('trend', 'N/A')}
支撑位: {market_data.get('support_levels', [])}
阻力位: {market_data.get('resistance_levels', [])}
"""

        # [NEW] 添加增强数据（如果可用）
        if 'intraday_series' in market_data and market_data['intraday_series']:
            intraday = market_data['intraday_series']
            prompt += f"""
## [ANALYZE] 日内时间序列 (3分钟间隔, 最近10个点)
Mid Prices: {[f"{p:.2f}" for p in intraday.get('mid_prices', [])]}
EMA20: {[f"{v:.2f}" for v in intraday.get('ema20_values', [])]}
MACD: {[f"{v:.2f}" for v in intraday.get('macd_values', [])]}
RSI(7): {[f"{v:.1f}" for v in intraday.get('rsi7_values', [])]}
"""

        if 'long_term_context_4h' in market_data and market_data['long_term_context_4h']:
            ctx_4h = market_data['long_term_context_4h']
            prompt += f"""
## [TREND-UP] 4小时级别上下文
EMA20: {ctx_4h.get('ema20', 'N/A')} vs EMA50: {ctx_4h.get('ema50', 'N/A')}
ATR: 3期={ctx_4h.get('atr3', 'N/A')}, 14期={ctx_4h.get('atr14', 'N/A')}
成交量: 当前={ctx_4h.get('current_volume', 'N/A')}, 平均={ctx_4h.get('average_volume', 'N/A')}
"""

        if 'futures_market' in market_data and market_data['futures_market']:
            futures = market_data['futures_market']
            prompt += f"""
## ⚡ 合约市场数据
资金费率: {futures.get('funding_rate', 'N/A')}
持仓量: 当前={futures.get('open_interest', {}).get('current', 'N/A')}, 平均={futures.get('open_interest', {}).get('average', 'N/A')}
"""

        prompt += f"""
## 账户状态
可用资金: ${account_info.get('balance', 'N/A')}
当前持仓数: {len(account_info.get('positions', []))}
未实现盈亏: ${account_info.get('unrealized_pnl', 'N/A')}
"""

        # 胜率显示策略：只有在交易次数足够时才显示（避免误导AI）
        MIN_TRADES_FOR_WINRATE = 20  # 可在config.py中配置
        if trade_history and len(trade_history) >= MIN_TRADES_FOR_WINRATE:
            recent_trades = trade_history[-10:]  # 看最近10笔，更有统计意义
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            winrate_pct = (wins / len(recent_trades)) * 100
            prompt += f"\n## 近期表现\n最近{len(recent_trades)}笔胜率: {winrate_pct:.1f}% ({wins}胜/{len(recent_trades)-wins}负)\n"
        elif trade_history and len(trade_history) > 0:
            # 交易次数太少，不显示胜率，只显示交易数
            prompt += f"\n## 交易状态\n已完成交易: {len(trade_history)}笔 (数据积累中，暂不显示胜率)\n"

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
        decision['leverage'] = max(1, min(20, decision['leverage']))  # 最高20倍杠杆
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
    "leverage": 8-20
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

