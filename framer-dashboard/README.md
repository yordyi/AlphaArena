# Alpha Arena Dashboard

Framer风格的加密货币交易仪表板，使用Next.js 15、React 19和Framer Motion构建，实时显示Binance账户数据。

## 特性

- ✨ **Framer风格设计** - 采用现代暗黑主题，平滑动画效果
- 📊 **实时数据** - 每10秒自动更新账户和持仓信息
- 🎯 **可视化** - 圆环图显示资产分配，面积图显示盈亏曲线
- ⚡ **高性能** - Next.js 15 App Router，React 19，优化的包导入
- 🎨 **响应式设计** - 完美适配桌面和移动设备

## 技术栈

- **框架**: Next.js 15.1.4
- **UI库**: React 19.0.0
- **动画**: Framer Motion 11.15.0
- **图表**: Recharts 2.13.3
- **样式**: Tailwind CSS 3.4.17
- **语言**: TypeScript 5.7.2

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制`.env.local.example`为`.env.local`并填入你的Binance API密钥：

```bash
cp .env.local.example .env.local
```

编辑`.env.local`：

```env
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
BINANCE_TESTNET=false
```

> ⚠️ **安全提示**:
> - 使用测试网进行开发：`BINANCE_TESTNET=true`
> - 确保API密钥权限仅包含"读取"和"合约交易"
> - 不要将`.env.local`提交到Git仓库

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看仪表板。

### 4. 构建生产版本

```bash
npm run build
npm run start
```

## 项目结构

```
framer-dashboard/
├── app/                      # Next.js App Router
│   ├── api/                  # API路由
│   │   └── binance/          # Binance API端点
│   │       ├── account/      # 账户信息
│   │       ├── positions/    # 持仓数据
│   │       └── ticker/       # 行情数据
│   ├── globals.css           # 全局样式
│   ├── layout.tsx            # 根布局
│   └── page.tsx              # 主页面
├── components/               # React组件
│   ├── PortfolioChart.tsx    # 资产分配圆环图
│   ├── PLChart.tsx           # 盈亏曲线图
│   ├── PositionsTable.tsx    # 持仓列表
│   └── StatCard.tsx          # 统计卡片
├── lib/                      # 工具库
│   └── binance.ts            # Binance客户端
├── next.config.ts            # Next.js配置
├── tailwind.config.ts        # Tailwind配置
└── tsconfig.json             # TypeScript配置
```

## API端点

### GET /api/binance/account

获取账户信息、余额和持仓。

**响应示例**:
```json
{
  "account": {
    "totalWalletBalance": "1000.00",
    "totalUnrealizedProfit": "50.00",
    "totalMarginBalance": "1050.00",
    "availableBalance": "800.00"
  },
  "balances": [...],
  "positions": [...]
}
```

### GET /api/binance/positions

获取所有当前持仓及盈亏信息。

### GET /api/binance/ticker?symbol=BTCUSDT

获取指定交易对的24小时行情数据。

## 组件说明

### StatCard
显示统计数据的卡片组件，支持正负值颜色区分和动画。

**Props**:
- `title`: 标题
- `value`: 数值
- `change`: 变化值（可选）
- `changeType`: 'positive' | 'negative' | 'neutral'
- `delay`: 动画延迟

### PortfolioChart
使用Recharts的圆环图展示资产分配。

**Props**:
- `data`: `{ name: string, value: number, color: string }[]`

### PLChart
使用Recharts的面积图展示盈亏曲线。

**Props**:
- `data`: `{ time: string, value: number }[]`

### PositionsTable
表格展示所有持仓，包含币种、数量、杠杆、入场价、当前价、盈亏等信息。

**Props**:
- `positions`: 持仓数组

## 自定义主题

在`tailwind.config.ts`中修改颜色配置：

```typescript
colors: {
  background: {
    DEFAULT: '#0a0a0a',  // 主背景色
    card: '#141414',      // 卡片背景色
    hover: '#1a1a1a',     // 悬停背景色
  },
  accent: {
    green: '#00ff88',     // 绿色强调色
    red: '#ff3366',       // 红色强调色
    blue: '#0099ff',      // 蓝色强调色
    purple: '#9945ff',    // 紫色强调色
    neon: '#00ffff',      // 霓虹色
  },
}
```

## 开发脚本

- `npm run dev` - 启动开发服务器 (http://localhost:3000)
- `npm run build` - 构建生产版本
- `npm run start` - 启动生产服务器
- `npm run lint` - 运行ESLint检查

## 与AlphaArena Bot集成

本仪表板可以与AlphaArena AI交易机器人配合使用，显示机器人的交易数据。

确保两者使用相同的Binance API密钥配置。

## 常见问题

### API连接错误

如果看到"连接错误"提示：
1. 检查`.env.local`文件是否存在
2. 验证Binance API密钥是否正确
3. 确认API密钥权限设置正确
4. 检查IP是否在Binance白名单中

### 数据不更新

- 检查浏览器控制台是否有错误
- 确认Binance API未达到速率限制
- 验证网络连接正常

### 样式问题

如果样式未正确加载：
```bash
# 清除Next.js缓存并重新构建
rm -rf .next
npm run dev
```

## 许可证

MIT

## 贡献

欢迎提交Issue和Pull Request！
