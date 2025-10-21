# 🏆 Alpha Arena - DeepSeek-V3 Trading Bot

灵感来自 [nof1.ai](https://nof1.ai) 的 Alpha Arena 实验，这是一个使用 DeepSeek-V3 AI 模型驱动的永不停机的加密货币量化交易系统。

## 📖 项目简介

Alpha Arena 是一个完全自主的 AI 交易机器人，它：
- 🤖 使用 **DeepSeek-V3** 进行智能交易决策
- 📊 实时分析市场技术指标（RSI、MACD、布林带等）
- ⚡ 自动执行交易（开多、开空、止损、止盈）
- 📈 追踪性能指标（夏普比率、最大回撤、胜率等）
- 🌐 提供 Web 仪表板实时监控
- 🔄 **永不停机** - 24/7 持续运行

### 与 nof1.ai Alpha Arena 的对比

nof1.ai 的 Alpha Arena 让 6 个 AI 模型（GPT-5、Gemini 2.5、Grok-4、Claude Sonnet 4.5、DeepSeek-V3、Qwen3 Max）各自使用 $10,000 在 Hyperliquid 交易所进行真实交易竞赛。

**我们的系统**：
- 专注于 DeepSeek-V3 模型
- 在 Binance 交易所运行
- 完全开源，可自定义
- 永久运行，持续优化

## 🎯 核心功能

### 1. AI 驱动的交易决策
- 使用 DeepSeek API 分析市场数据
- 基于技术指标和趋势分析做出决策
- 动态调整仓位和杠杆
- 智能止损止盈

### 2. 性能追踪系统
类似 nof1.ai 的 SharpeBench，追踪：
- ✅ 账户价值和收益率
- ✅ 夏普比率（风险调整后收益）
- ✅ 最大回撤
- ✅ 胜率
- ✅ 交易次数和手续费
- ✅ 每日收益

### 3. Web 仪表板
- 实时显示交易表现
- 资金曲线图表
- 交易历史记录
- 自动刷新（每 10 秒）

### 4. 风险管理
- 仓位大小控制
- 自动止损止盈
- 最大回撤保护
- 每日亏损限制

## 🚀 快速开始

### 1. 前置要求

- Python 3.8+
- Binance 账户和 API 密钥
- DeepSeek API 密钥

### 2. 安装依赖

```bash
cd /Volumes/Samsung/AlphaArena
pip3 install -r requirements.txt
```

### 3. 配置

编辑 `.env` 文件：

```bash
# Binance API
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
BINANCE_TESTNET=false

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# 交易配置
INITIAL_CAPITAL=10000
MAX_POSITION_PCT=10
DEFAULT_LEVERAGE=3
TRADING_INTERVAL_SECONDS=300

# 交易对（多个用逗号分隔）
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT
```

### 4. 启动机器人

```bash
./start.sh
```

或者直接运行：

```bash
python3 alpha_arena_bot.py
```

### 5. 启动 Web 仪表板（可选）

在另一个终端窗口：

```bash
python3 web_dashboard.py
```

然后访问：http://localhost:5000

## 📊 项目结构

```
AlphaArena/
├── alpha_arena_bot.py          # 主交易机器人
├── deepseek_client.py          # DeepSeek API 客户端
├── ai_trading_engine.py        # AI 交易引擎
├── performance_tracker.py      # 性能追踪系统
├── web_dashboard.py            # Web 仪表板
├── binance_client.py           # Binance API 客户端
├── market_analyzer.py          # 市场分析器
├── risk_manager.py             # 风险管理器
├── .env                        # 配置文件
├── requirements.txt            # Python 依赖
├── start.sh                    # 启动脚本
├── performance_data.json       # 性能数据（自动生成）
├── logs/                       # 日志目录
└── templates/                  # Web 模板
    └── dashboard.html
```

## 🎮 使用说明

### 永不停机运行

系统设计为 24/7 持续运行：

1. **自动重试**：遇到错误自动重试
2. **优雅关闭**：支持 Ctrl+C 优雅退出
3. **数据持久化**：所有交易和性能数据自动保存
4. **日志记录**：详细的日志文件

### 后台运行（推荐）

使用 `screen` 或 `tmux` 在后台运行：

```bash
# 使用 screen
screen -S alpha_arena
./start.sh
# 按 Ctrl+A 然后 D 脱离会话

# 重新连接
screen -r alpha_arena
```

或使用 `nohup`：

```bash
nohup ./start.sh > output.log 2>&1 &
```

### 监控运行状态

```bash
# 查看实时日志
tail -f logs/alpha_arena_*.log

# 查看 Web 仪表板
# 访问 http://localhost:5000
```

## 📈 性能指标说明

### Sharpe Ratio（夏普比率）
- 衡量风险调整后的收益
- > 1.0 = 良好
- > 2.0 = 优秀
- > 3.0 = 卓越

### Max Drawdown（最大回撤）
- 从峰值到谷底的最大跌幅
- 越小越好
- < 10% = 优秀
- < 20% = 良好

### Win Rate（胜率）
- 盈利交易占总交易的百分比
- > 50% = 不错
- > 60% = 良好
- > 70% = 优秀

## ⚠️ 风险警告

**重要提示**：

1. ⚠️ 加密货币交易存在高风险，可能导致资金损失
2. 🧪 建议先在 Binance 测试网测试（设置 `BINANCE_TESTNET=true`）
3. 💰 只投入你能承受损失的资金
4. 📊 定期监控机器人运行状态
5. 🔐 妥善保管 API 密钥，不要分享给他人
6. 🛡️ 建议设置 IP 白名单限制 API 访问

## 🔧 高级配置

### 调整交易频率

在 `.env` 中修改：
```bash
TRADING_INTERVAL_SECONDS=300  # 5分钟
```

### 调整仓位和杠杆

```bash
MAX_POSITION_PCT=5      # 最大单次仓位 5%
DEFAULT_LEVERAGE=2      # 默认杠杆 2x
```

### 修改交易对

```bash
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT
```

## 📝 更新日志

### v1.0.0 (2025-10-21)
- ✅ 实现 DeepSeek-V3 AI 交易引擎
- ✅ 性能追踪系统（SharpeBench）
- ✅ Web 实时仪表板
- ✅ 永不停机的交易循环
- ✅ 完整的风险管理系统

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- 灵感来自 [nof1.ai](https://nof1.ai) 的 Alpha Arena 实验
- 使用 [DeepSeek](https://www.deepseek.com) API
- 基于 [Binance](https://www.binance.com) 交易所

---

## 📞 联系方式

有问题或建议？欢迎联系！

**祝交易顺利！🚀**
