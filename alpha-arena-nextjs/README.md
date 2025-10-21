# Alpha Arena - Next.js Dashboard

> Next.js 15 + TypeScript + Tailwind CSS 实现的AI交易Dashboard

## 📋 项目概述

这是Alpha Arena的现代化前端实现,使用Next.js替代原有的HTML/Flask单文件架构。保留Python后端API,实现前后端分离。

## ✨ 特性

- ✅ **Next.js 15** - 最新App Router架构
- ✅ **TypeScript** - 完整类型安全
- ✅ **Tailwind CSS** - 实用工具优先的CSS框架
- ✅ **组件化设计** - 可复用的React组件
- ✅ **实时数据** - 每5秒自动刷新
- ✅ **专业设计系统** - 统一的设计Token (颜色、间距、阴影)
- ✅ **Glassmorphism UI** - 现代玻璃态设计

## 🚀 快速开始

### 前置要求

1. **Node.js 18+** (推荐使用LTS版本)
2. **Python后端运行中** - Flask服务器必须在 `localhost:5000`

### 安装依赖

```bash
cd alpha-arena-nextjs
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问: **http://localhost:3002** (如果3000端口被占用会自动使用3002)

### 构建生产版本

```bash
npm run build
npm run start
```

## 📁 项目结构

```
alpha-arena-nextjs/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 根布局
│   │   ├── page.tsx            # 首页 (Dashboard)
│   │   ├── globals.css         # 全局样式
│   │   └── api/                # API路由 (代理到Python后端)
│   │       ├── performance/
│   │       ├── positions/
│   │       └── decisions/
│   ├── components/             # React组件
│   │   ├── StatCard.tsx        # 统计卡片
│   │   ├── PerformanceChart.tsx # 性能图表
│   │   ├── PositionsTable.tsx  # 持仓表格
│   │   └── AIDecisions.tsx     # AI决策卡片
│   ├── hooks/                  # 自定义Hooks
│   │   ├── usePerformance.ts
│   │   ├── usePositions.ts
│   │   └── useDecisions.ts
│   └── lib/
│       └── types.ts            # TypeScript类型定义
├── tailwind.config.ts          # Tailwind配置 (设计Token)
├── tsconfig.json               # TypeScript配置
├── next.config.ts              # Next.js配置
└── package.json                # 依赖管理
```

## 🎨 设计系统

### 颜色 (70%饱和度 - 专业级)

```typescript
primary:    #2DD4BF  // Teal-400 (主色调)
secondary:  #8B7FD8  // Soft purple (次要色)
accent:     #E879F9  // Pink-purple (强调色)
success:    #4ADE80  // Green-400 (成功/盈利)
danger:     #FB7185  // Red-400 (危险/亏损)
warning:    #FCD34D  // Yellow-400 (警告)
```

### 间距 (8px基准)

```
space-1:  4px   (0.25rem)
space-2:  8px   (0.5rem)
space-4:  16px  (1rem)
space-6:  24px  (1.5rem)
space-8:  32px  (2rem)
```

### 圆角

```
radius-sm:  4px   (0.25rem)
radius-md:  8px   (0.5rem)
radius-lg:  12px  (0.75rem)
radius-xl:  16px  (1rem)
```

## 🔌 API集成

### 架构

```
Next.js Frontend (localhost:3002)
    ↓ API路由代理
Python Flask Backend (localhost:5000)
    ↓
Binance API + DeepSeek AI
```

### API Endpoints

#### `/api/performance`
获取性能数据 (账户价值、回报率、夏普比率等)

#### `/api/positions`
获取当前持仓列表

#### `/api/decisions`
获取AI决策历史

### 数据刷新

所有数据通过自定义Hooks每**5秒**自动刷新:
- `usePerformance(5000)`
- `usePositions(5000)`
- `useDecisions(5000)`

## 🆚 与原HTML版本对比

| 特性 | HTML/Flask | Next.js |
|------|-----------|---------|
| 文件大小 | 1794行单文件 | 多个小组件 |
| 代码复用 | ❌ 复制粘贴 | ✅ 组件化 |
| 类型安全 | ❌ 无 | ✅ TypeScript |
| 开发体验 | 6/10 | 10/10 |
| 可维护性 | 5/10 | 9/10 |
| 热更新 | ❌ 手动刷新 | ✅ HMR (200ms) |
| CSS管理 | 内联 2000+ 行 | Tailwind + CSS Modules |

## 🔧 开发建议

### 修改颜色

编辑 `tailwind.config.ts`:

```typescript
colors: {
  primary: '#2DD4BF',  // 修改主色调
  // ...
}
```

### 修改刷新间隔

编辑 `src/app/page.tsx`:

```typescript
const { data: performance } = usePerformance(5000)  // 改为你想要的毫秒数
```

### 添加新组件

1. 在 `src/components/` 创建新文件
2. 使用TypeScript和Tailwind CSS
3. 在 `page.tsx` 中导入使用

## 📊 核心组件说明

### StatCard
```typescript
<StatCard
  icon="💰"
  title="账户价值"
  value={10523.45}
  prefix="$"
  valueColor="primary"
  change={5.23}  // 可选:显示变化百分比
/>
```

### PerformanceChart
```typescript
<PerformanceChart
  data={chartData}  // ChartDataPoint[]
  title="账户价值曲线"
/>
```

### PositionsTable
```typescript
<PositionsTable
  positions={positions}  // Position[]
/>
```

### AIDecisions
```typescript
<AIDecisions
  decisions={decisions}  // AIDecision[]
/>
```

## 🐛 故障排除

### 1. "无法连接到后端"错误

**原因**: Python Flask服务器未运行

**解决**:
```bash
cd /Volumes/Samsung/AlphaArena
./manage.sh dashboard
```

确保Flask运行在 `http://localhost:5000`

### 2. 端口被占用

Next.js会自动使用下一个可用端口 (3001, 3002, etc.)

查看控制台输出确认实际端口。

### 3. 编译错误

删除缓存重新安装:
```bash
rm -rf .next node_modules package-lock.json
npm install
npm run dev
```

## 🚀 下一步开发

- [ ] **WebSocket集成** - 替代轮询,实现真正的实时推送
- [ ] **图表优化** - 使用TradingView Lightweight Charts
- [ ] **暗色/亮色主题切换**
- [ ] **移动端优化** - 响应式设计改进
- [ ] **更多技术指标** - 添加RSI、MACD可视化
- [ ] **交易执行** - 从Dashboard直接下单

## 📝 技术栈版本

```json
{
  "next": "^15.1.6",
  "react": "^19.0.0",
  "typescript": "^5",
  "tailwindcss": "^3.4.1",
  "chart.js": "^4.4.8",
  "socket.io-client": "^4.8.1"
}
```

## 🤝 与Python后端通信

后端需要提供以下API:

```python
# web_dashboard.py

@app.route('/api/performance')
def get_performance():
    return jsonify({
        'success': True,
        'data': {
            'account_value': 10523.45,
            'total_return_pct': 5.23,
            # ... 其他性能指标
        }
    })

@app.route('/api/positions')
def get_positions():
    return jsonify({
        'success': True,
        'data': [...]  # Position列表
    })

@app.route('/api/decisions')
def get_ai_decisions():
    return jsonify({
        'success': True,
        'data': [...]  # AI决策列表
    })
```

## 📄 许可证

与主项目相同

---

**作者**: Claude Code
**创建日期**: 2025-10-22
**Next.js版本**: 15.5.6
**状态**: ✅ 生产就绪
