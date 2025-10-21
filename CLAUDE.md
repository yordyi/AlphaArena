# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Alpha Arena is a dual-system AI-powered cryptocurrency trading platform inspired by nof1.ai's Alpha Arena experiment. The repository contains:

1. **Python Legacy System**: A production-ready DeepSeek-V3 trading bot (currently operational)
2. **Next.js Modern System**: A full-stack multi-AI trading arena under development (alpha-arena-nextjs/)

Both systems trade cryptocurrency futures on Binance with AI-driven decision making, real-time monitoring, and comprehensive performance tracking.

**Primary Tech Stack**: Python 3.8+ (legacy), Next.js 15 + TypeScript + PostgreSQL (modern)

## Development Commands

### Python Legacy System (Root Directory)

```bash
# Quick start
./start.sh                          # Start trading bot
python3 alpha_arena_bot.py          # Direct bot execution

# Management
./manage.sh start                   # Start bot
./manage.sh dashboard               # Start web dashboard (Flask on port 5000)
./manage.sh logs                    # View real-time logs
./manage.sh status                  # Show performance metrics
./manage.sh stop                    # Stop bot
./manage.sh restart                 # Restart bot
./manage.sh screen                  # Start in background screen session

# Testing & Setup
python3 test_connection.py          # Test Binance and DeepSeek API connections
pip3 install -r requirements.txt    # Install dependencies

# Monitoring
tail -f logs/alpha_arena_*.log      # View logs
tail -f bot.log                     # View bot logs
tail -f dashboard.log               # View dashboard logs
python3 web_dashboard.py            # Launch Flask dashboard (http://localhost:5000)
```

### Next.js Modern System (alpha-arena-nextjs/)

```bash
cd alpha-arena-nextjs

# Development
npm run dev                         # Start Next.js dev server (http://localhost:3000)
npm run build                       # Build for production
npm run start                       # Start production server
npm run lint                        # Run ESLint

# Database
npx prisma generate                 # Generate Prisma client
npm run prisma:push                 # Push schema to database
npm run prisma:studio               # Open Prisma Studio GUI

# Trading & Testing
npm run worker                      # Run trading loop worker
npm run backtest                    # Run backtest with historical data
```

## Architecture Overview

### Python Legacy System Architecture

The system uses a layered architecture with clear separation of concerns:

**Core Components** (8 Python modules):

1. **alpha_arena_bot.py** (Main Entry Point)
   - Orchestrates all components
   - Manages 24/7 trading loop
   - Handles graceful shutdown (SIGINT/SIGTERM)
   - Configurable via environment variables

2. **ai_trading_engine.py** (AI Decision Layer)
   - Integrates DeepSeek API for trading decisions
   - Analyzes market data + technical indicators → AI decision
   - Implements 15-minute cooldown period to prevent rapid retries
   - Executes trades based on AI confidence levels

3. **deepseek_client.py** (AI Client)
   - DeepSeek API wrapper
   - Generates structured prompts with market context
   - Parses AI responses into actionable decisions
   - Returns: action, confidence, reasoning, position_size, leverage, stop_loss, take_profit

4. **binance_client.py** (Exchange Integration)
   - HMAC SHA256 signature authentication
   - Supports both spot and futures trading
   - Position management (open/close, leverage adjustment)
   - Account info, balance, K-line data retrieval
   - Testnet support via BINANCE_TESTNET env var

5. **market_analyzer.py** (Technical Analysis)
   - Technical indicators: RSI, MACD, Bollinger Bands, SMA, ATR
   - Support/resistance level detection
   - Market trend analysis
   - Real-time market data fetching

6. **risk_manager.py** (Risk Management)
   - Position sizing (max 10% per position)
   - Leverage limits (1-10x)
   - Stop-loss/take-profit calculation
   - Max drawdown protection (15%)
   - Daily loss limits (5%)
   - Position count limits (max 10 positions)

7. **performance_tracker.py** (Performance Metrics)
   - Real-time performance tracking
   - Metrics: Sharpe ratio, max drawdown, win rate, total return
   - JSON-based data persistence (performance_data.json)
   - Equity curve tracking
   - Trade history logging

8. **web_dashboard.py** (Monitoring Interface)
   - Flask web server (port 5000)
   - Real-time dashboard (auto-refresh every 10s)
   - Charts: equity curve (Chart.js)
   - Trade history table
   - Performance metrics cards

**Data Flow**:
```
Trading Loop (configurable interval, default 5 min):
  Market Data Fetch (BinanceClient)
    ↓
  Technical Analysis (MarketAnalyzer)
    ↓
  AI Decision (DeepSeekClient via AITradingEngine)
    ↓
  Risk Validation (RiskManager)
    ↓
  Trade Execution (BinanceClient)
    ↓
  Performance Tracking (PerformanceTracker)
    ↓
  Data Persistence (JSON files)
```

**Key Design Patterns**:
- **Dependency Injection**: Components passed to main bot class
- **Single Responsibility**: Each module has one clear purpose
- **Strategy Pattern**: AI decision-making as pluggable strategy
- **Observer Pattern**: Performance tracking observes trade events

### Next.js Modern System Architecture

See `alpha-arena-nextjs/CLAUDE.md` for detailed Next.js architecture documentation.

**Key Differences from Python System**:
- Multi-AI model support (DeepSeek, OpenAI, Claude) vs. single DeepSeek
- PostgreSQL database vs. JSON files
- React dashboard vs. Flask HTML templates
- Real-time WebSocket market data vs. REST polling
- Backtesting engine included
- TypeScript type safety

## Environment Configuration

### Python System (.env in root)

```env
# Binance API (REQUIRED)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=false              # true for testnet, false for mainnet

# DeepSeek API (REQUIRED)
DEEPSEEK_API_KEY=sk-your-key

# Trading Configuration
INITIAL_CAPITAL=10000              # Starting capital in USDT
MAX_POSITION_PCT=10                # Max position size (% of capital)
DEFAULT_LEVERAGE=3                 # Default leverage (1-10)
TRADING_INTERVAL_SECONDS=300       # Trading loop interval (5 min)
TRADING_SYMBOLS=BTCUSDT,ETHUSDT    # Comma-separated trading pairs
```

### Next.js System (.env.local in alpha-arena-nextjs/)

See `alpha-arena-nextjs/CLAUDE.md` for complete Next.js environment variables.

## Critical Patterns and Conventions

### Python System Conventions

**Logging**:
- All modules use Python's `logging` module
- Logs written to `logs/alpha_arena_YYYYMMDD.log`
- Console output includes timestamps and log levels
- Log rotation by date

**Error Handling**:
- All API calls wrapped in try/except
- Graceful degradation on errors
- Auto-retry with exponential backoff
- Trade cooldown on failures (15 min)

**Data Persistence**:
- Performance data: `performance_data.json`
- AI decisions: `ai_decisions.json`
- Trade history embedded in performance data
- Atomic file writes to prevent corruption

**AI Decision Structure**:
```python
{
    "action": "BUY" | "SELL" | "HOLD" | "CLOSE",
    "confidence": 0-100,  # percentage
    "reasoning": "Human-readable explanation",
    "position_size": 0-100,  # percentage of capital
    "leverage": 1-10,
    "stop_loss": 0-100,  # percentage below entry
    "take_profit": 0-100  # percentage above entry
}
```

**Position Management**:
```python
# Open long position
binance_client.open_long(
    symbol='BTCUSDT',
    quantity=0.001,  # BTC amount
    leverage=3
)

# Close all positions for symbol
binance_client.close_all_positions('BTCUSDT')

# Get current positions
positions = binance_client.get_positions()
```

**Risk Checks**:
```python
# RiskManager validates before trade execution:
# 1. Position size <= MAX_POSITION_PCT
# 2. Leverage <= max_leverage config
# 3. Current drawdown < max_drawdown threshold
# 4. Daily loss < daily_loss_limit
# 5. Total positions < max_positions

is_allowed, reason = risk_manager.check_can_open_position(
    symbol='BTCUSDT',
    side='LONG',
    size_usdt=1000
)
```

### Key Workflow: Adding a New Trading Symbol

1. Update `.env`:
   ```bash
   TRADING_SYMBOLS=BTCUSDT,ETHUSDT,NEWUSDT
   ```

2. Bot automatically picks up new symbol in next trading cycle
3. No code changes required

### Key Workflow: Adjusting Risk Parameters

Edit risk manager configuration in `alpha_arena_bot.py`:
```python
risk_config = {
    'max_portfolio_risk': 0.02,  # 2% max risk per trade
    'max_position_size': 0.1,    # 10% max position size
    'max_leverage': 10,          # Max 10x leverage
    'stop_loss_pct': 0.02,       # 2% stop loss
    'take_profit_pct': 0.05,     # 5% take profit
    'max_drawdown': 0.15,        # 15% max drawdown
    'max_positions': 10          # Max 10 concurrent positions
}
```

## Important Safety Considerations

**Real Money Trading System**: Both systems trade with real funds on Binance.

**Safety Checklist**:
1. **Always test on testnet first**: Set `BINANCE_TESTNET=true`
2. **Start with minimal capital**: Test with small amounts
3. **Monitor continuously**: Check logs and dashboard regularly
4. **Validate API keys**: Ensure keys have correct permissions (Futures trading enabled)
5. **IP whitelisting**: Add your IP to Binance API key whitelist
6. **Never commit secrets**: `.env` files are gitignored
7. **Set conservative limits**: Start with low leverage (2-3x) and small positions (5%)
8. **Emergency stop**: Keep `./manage.sh stop` or Ctrl+C readily available

**Binance API Permissions Required**:
- ✅ Enable Futures trading
- ✅ Enable Reading
- ✅ No withdrawal permissions needed (safer)
- ✅ IP whitelist recommended

## Common Development Tasks

### Running the Python Bot in Development

```bash
# Terminal 1: Start bot
./start.sh

# Terminal 2: Monitor logs
tail -f logs/alpha_arena_*.log

# Terminal 3: Web dashboard
python3 web_dashboard.py
# Visit http://localhost:5000
```

### Testing Changes Without Real Trading

1. Set `BINANCE_TESTNET=true` in `.env`
2. Get testnet API keys from https://testnet.binancefuture.com
3. Fund testnet account with fake USDT
4. Run bot normally - all trades execute on testnet

### Debugging AI Decisions

AI decisions are logged to `ai_decisions.json`:
```bash
cat ai_decisions.json | python3 -m json.tool | less
```

Each decision includes:
- Timestamp
- Symbol
- Market data snapshot
- Indicator values
- AI reasoning
- Final decision and confidence

### Modifying AI Decision Logic

Edit `deepseek_client.py` → `make_trading_decision()`:
- Modify the prompt template to change AI context
- Adjust confidence threshold requirements
- Change decision parsing logic

### Adding New Technical Indicators

1. Add indicator calculation to `market_analyzer.py`:
   ```python
   def calculate_new_indicator(self, klines):
       # Implementation
       return indicator_value
   ```

2. Include in `get_comprehensive_analysis()` return dict

3. AI will automatically receive new indicator in next decision

### Performance Monitoring

**Key Files**:
- `performance_data.json`: Current state, all metrics, trade history
- `logs/alpha_arena_*.log`: Detailed execution logs
- Web dashboard: Real-time visualization

**Key Metrics**:
- **Sharpe Ratio**: Risk-adjusted return (>1.0 good, >2.0 excellent)
- **Max Drawdown**: Peak-to-trough decline (<10% excellent, <20% acceptable)
- **Win Rate**: Percentage of profitable trades (>50% good, >60% excellent)
- **Total Return**: Overall profit/loss percentage

## Current Implementation Status

### Python Legacy System ✅ (100% Complete)
- Fully operational 24/7 trading bot
- Production-ready with comprehensive error handling
- Web dashboard operational
- Performance tracking active
- All features documented

### Next.js Modern System 📋 (70% Complete)
See `alpha-arena-nextjs/CLAUDE.md` for detailed status.

**Completed**: Core libraries, database schema, AI integration, backtesting
**In Progress**: API routes, React UI components
**Planned**: Multi-AI model arena, advanced analytics

## System Differences and Migration Path

**When to use Python system**:
- Immediate trading needs
- Single AI model (DeepSeek) sufficient
- Simple deployment requirements
- Familiar with Python ecosystem

**When to use Next.js system**:
- Multi-AI model comparison needed
- Advanced analytics and backtesting
- Modern web UI preferred
- Scalability and type safety important

**Migration Strategy**:
Both systems can run simultaneously. The Next.js system is designed as an enhanced replacement but is not yet feature-complete. Continue using Python system for production trading while developing Next.js features.

## File Organization

```
AlphaArena/
├── Python Trading System (Root)
│   ├── alpha_arena_bot.py          # Main bot orchestrator
│   ├── ai_trading_engine.py        # AI decision integration
│   ├── deepseek_client.py          # DeepSeek API wrapper
│   ├── binance_client.py           # Binance API wrapper
│   ├── market_analyzer.py          # Technical indicators
│   ├── risk_manager.py             # Risk management
│   ├── performance_tracker.py      # Performance metrics
│   ├── web_dashboard.py            # Flask dashboard
│   ├── start.sh                    # Quick start script
│   ├── manage.sh                   # Management utilities
│   ├── .env                        # Configuration (not in git)
│   ├── requirements.txt            # Python dependencies
│   ├── logs/                       # Log files
│   ├── templates/                  # Flask HTML templates
│   ├── performance_data.json       # Performance state
│   └── ai_decisions.json           # AI decision log
│
└── alpha-arena-nextjs/             # Next.js Modern System
    ├── app/                        # Next.js App Router
    ├── lib/                        # Core libraries
    ├── prisma/                     # Database schema
    ├── package.json                # Node dependencies
    └── CLAUDE.md                   # Next.js-specific docs
```

## Troubleshooting Common Issues

### Bot stops unexpectedly
- Check `logs/alpha_arena_*.log` for errors
- Verify API key validity and permissions
- Check Binance API rate limits
- Ensure sufficient balance in account

### DeepSeek API errors
- Verify API key in `.env`
- Check DeepSeek account balance/credits
- Review API rate limits
- Check `ai_decisions.json` for error messages

### Binance connection issues
- Verify API keys in `.env`
- Check IP whitelist on Binance
- Ensure Futures trading enabled on API key
- Test with `python3 test_connection.py`

### Dashboard not updating
- Verify `performance_data.json` exists and is valid JSON
- Check Flask server logs in `dashboard.log`
- Clear browser cache and refresh
- Ensure port 5000 not blocked by firewall

### Position execution failures
- Check account balance (need margin for futures)
- Verify minimum notional value (usually $20+ USDT)
- Check symbol is valid and trading
- Review risk manager limits in logs
