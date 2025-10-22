'use client'

import { useState, useEffect } from 'react'
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

  // 图表数据状态
  const [chartData, setChartData] = useState<Array<{time: string; value: number}>>([])

  // 获取真实图表数据
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const response = await fetch('/api/chart')
        const result = await response.json()
        if (result.success && result.data) {
          // 转换数据格式：取最近100个点
          const formattedData = result.data.slice(-100).map((item: any) => {
            const date = new Date(item.time)
            // 手动格式化避免 toLocaleTimeString 的问题
            const time = `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
            return {
              time,
              value: item.value
            }
          })
          setChartData(formattedData)
        }
      } catch (error) {
        console.error('Failed to fetch chart data:', error)
      }
    }

    fetchChartData()
    // 每30秒刷新一次图表数据
    const interval = setInterval(fetchChartData, 30000)
    return () => clearInterval(interval)
  }, [])

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
            <PerformanceChart data={chartData} />
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
