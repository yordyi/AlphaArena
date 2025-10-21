'use client'

import { StatCard } from '@/components/StatCard'
import { PerformanceChart } from '@/components/PerformanceChart'
import { PositionsTable } from '@/components/PositionsTable'
import { AIDecisions } from '@/components/AIDecisions'
import { usePerformanceWS } from '@/hooks/usePerformanceWS'
import { usePositionsWS } from '@/hooks/usePositionsWS'
import { useDecisionsWS } from '@/hooks/useDecisionsWS'

export default function Home() {
  // WebSocket实时数据 (<100ms延迟)
  const { data: performance, loading: perfLoading, error: perfError, lastUpdate: perfUpdate } = usePerformanceWS()
  const { data: positions, lastUpdate: posUpdate } = usePositionsWS()
  const { data: decisions, lastUpdate: decUpdate } = useDecisionsWS()

  // 模拟图表数据 - 暂时使用,后续从performance.equity_curve获取
  const mockChartData = Array.from({ length: 20 }, (_, i) => ({
    time: new Date(Date.now() - (19 - i) * 3600000).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    }),
    value: performance ? performance.account_value * (0.95 + i * 0.003) : 10000,
  }))

  if (perfLoading && !performance) {
    return (
      <main className="min-h-screen p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⏳</div>
          <div className="text-xl text-gray-400">加载数据中...</div>
        </div>
      </main>
    )
  }

  if (perfError || !performance) {
    return (
      <main className="min-h-screen p-6 flex items-center justify-center">
        <div className="glass-card p-8 text-center max-w-md">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2">无法连接到后端</h2>
          <p className="text-gray-400 mb-4">
            请确保Python Flask服务器运行在 localhost:5000
          </p>
          <code className="text-sm bg-black/30 p-2 rounded block">
            ./manage.sh dashboard
          </code>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen p-6">
      <div className="max-w-[1800px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            🤖 Alpha Arena
          </h1>
          <p className="text-gray-400">
            AI驱动的加密货币交易系统 | Next.js 15 + TypeScript
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatCard
            icon="💰"
            title="账户价值"
            value={performance.account_value}
            prefix="$"
            valueColor="primary"
            change={performance.total_return_pct}
          />
          <StatCard
            icon="📈"
            title="总回报率"
            value={performance.total_return_pct}
            suffix="%"
            valueColor={performance.total_return_pct >= 0 ? 'success' : 'danger'}
          />
          <StatCard
            icon="📊"
            title="夏普比率"
            value={performance.sharpe_ratio}
            valueColor="warning"
          />
          <StatCard
            icon="📉"
            title="最大回撤"
            value={Math.abs(performance.max_drawdown)}
            suffix="%"
            valueColor="danger"
          />
          <StatCard
            icon="🎯"
            title="胜率"
            value={performance.win_rate}
            suffix="%"
            valueColor="success"
          />
          <StatCard
            icon="🔄"
            title="总交易数"
            value={performance.total_trades}
            valueColor="white"
          />
          <StatCard
            icon="📍"
            title="持仓数量"
            value={performance.positions_count}
            valueColor="primary"
          />
          <StatCard
            icon="💹"
            title="日均收益"
            value={performance.avg_daily_return}
            suffix="%"
            valueColor={performance.avg_daily_return >= 0 ? 'success' : 'danger'}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-3 gap-6">
          {/* Left Column - Chart + Positions */}
          <div className="col-span-2 space-y-6">
            <PerformanceChart data={mockChartData} />
            <PositionsTable positions={positions} />
          </div>

          {/* Right Column - AI Decisions */}
          <div>
            <AIDecisions decisions={decisions} />
          </div>
        </div>

        {/* Success Notice - WebSocket */}
        <div className="mt-6 glass-card p-4 border-l-4 border-success">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              <div>
                <h3 className="font-bold text-success">WebSocket实时推送已启用</h3>
                <p className="text-sm text-gray-400">
                  已连接到Python后端 (localhost:5001),数据延迟 &lt;100ms
                </p>
              </div>
            </div>
            {(perfUpdate || posUpdate || decUpdate) && (
              <div className="flex flex-col items-end gap-1 text-xs text-gray-500">
                {perfUpdate && <div>性能: {perfUpdate.toLocaleTimeString()}</div>}
                {posUpdate && <div>持仓: {posUpdate.toLocaleTimeString()}</div>}
                {decUpdate && <div>决策: {decUpdate.toLocaleTimeString()}</div>}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
