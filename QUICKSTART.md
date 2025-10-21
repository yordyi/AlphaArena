# 🚀 Alpha Arena 快速启动指南

## 5 分钟快速开始

### 1️⃣ 安装依赖 (1 分钟)

```bash
cd /Volumes/Samsung/AlphaArena
pip3 install -r requirements.txt
```

### 2️⃣ 配置 API 密钥 (2 分钟)

编辑 `.env` 文件，已经预配置好了密钥：

```bash
# 已配置的密钥
BINANCE_API_KEY=QxrZTEurayg3VYbA4sT6Qk1C2zLd1lX5bMF2tV1aKmI40gZSQjWxAovrBEIdkBwd
BINANCE_API_SECRET=sFONmPmdVFV6zVGHjxLJWUUZLFEaRLIUHnglsFJg8Qro5BMAxmZ5Mvsq04PP8L8q
DEEPSEEK_API_KEY=sk-3c3bd887afb54e0ab863d16f8ab2fc14

# 交易配置（可选修改）
INITIAL_CAPITAL=10000                    # 初始资金
MAX_POSITION_PCT=10                      # 最大单次仓位 10%
DEFAULT_LEVERAGE=3                       # 默认杠杆 3x
TRADING_INTERVAL_SECONDS=300             # 交易间隔 5 分钟
TRADING_SYMBOLS=BTCUSDT,ETHUSDT         # 交易对
```

### 3️⃣ 测试连接 (1 分钟)

```bash
python3 test_connection.py
```

应该看到：
```
✅ Binance 连接成功
✅ DeepSeek 连接成功
```

### 4️⃣ 启动机器人 (1 分钟)

```bash
./start.sh
```

## 📊 查看实时仪表板

在另一个终端窗口启动 Web 仪表板：

```bash
python3 web_dashboard.py
```

然后访问：**http://localhost:5000**

## 🔄 后台永久运行

### 方法 1: 使用 screen（推荐）

```bash
# 创建新会话
screen -S alpha_arena

# 启动机器人
./start.sh

# 按 Ctrl+A 然后 D 脱离会话

# 重新连接
screen -r alpha_arena

# 停止机器人
# 在 screen 会话中按 Ctrl+C
```

### 方法 2: 使用 nohup

```bash
# 后台运行
nohup ./start.sh > output.log 2>&1 &

# 查看日志
tail -f output.log

# 停止
ps aux | grep alpha_arena_bot
kill <PID>
```

## 📝 监控机器人

### 查看日志

```bash
# 实时日志
tail -f logs/alpha_arena_*.log

# 所有日志
cat logs/alpha_arena_*.log
```

### 查看性能数据

```bash
# 查看性能数据文件
cat performance_data.json | python3 -m json.tool
```

### Web 仪表板

访问 http://localhost:5000 查看：
- 📊 实时账户价值
- 📈 收益曲线图
- 💹 交易历史
- 📉 性能指标

## ⚙️ 常见配置调整

### 降低风险（保守策略）

```bash
MAX_POSITION_PCT=5          # 降低仓位到 5%
DEFAULT_LEVERAGE=2          # 降低杠杆到 2x
```

### 增加交易频率

```bash
TRADING_INTERVAL_SECONDS=180   # 3 分钟一次
```

### 添加更多交易对

```bash
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT,DOGEUSDT
```

## 🆘 故障排查

### 问题 1: Binance 连接失败

```bash
# 检查 API 密钥是否正确
# 检查 IP 是否在白名单中
# 检查网络连接
```

### 问题 2: DeepSeek 连接失败

```bash
# 检查 API 密钥是否有效
# 检查密钥余额是否充足
# 检查网络连接
```

### 问题 3: 依赖安装失败

```bash
# 升级 pip
pip3 install --upgrade pip

# 重新安装
pip3 install -r requirements.txt --force-reinstall
```

## 🛑 停止机器人

### 正常停止（推荐）

在运行的终端按 `Ctrl+C`，机器人会优雅关闭。

### 强制停止

```bash
ps aux | grep alpha_arena_bot
kill <PID>
```

## ✅ 检查清单

启动前确认：
- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装（`pip3 install -r requirements.txt`）
- [ ] .env 文件已配置
- [ ] Binance API 连接测试通过
- [ ] DeepSeek API 连接测试通过
- [ ] 有足够的余额进行交易

## 📈 下一步

1. **监控表现**：定期查看 Web 仪表板
2. **调整参数**：根据表现调整配置
3. **分析日志**：定期查看日志文件
4. **风险管理**：确保仓位和杠杆合理

---

**准备好了吗？让我们开始交易！** 🚀

```bash
./start.sh
```
