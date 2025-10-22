'use client'

import { useState, useEffect } from 'react'
import { StatCard } from '@/components/StatCard'
import { PerformanceChart } from '@/components/PerformanceChart'
import { PositionsTable } from '@/components/PositionsTable'
import { AIDecisions } from '@/components/AIDecisions'
import { TradesHistory } from '@/components/TradesHistory'
import { MarketTicker } from '@/components/MarketTicker'
import { CandlestickChartWrapper } from '@/components/CandlestickChartWrapper'
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

        {/* Real-time Market Ticker - Binance WebSocket */}
        <div className="mb-6">
          <MarketTicker symbols={['BTCUSDT', 'ETHUSDT', 'BNBUSDT']} />
        </div>

        {/* Stats Grid - 专业交易仪表板布局 */}
        <div className="mb-6 space-y-4">
          {/* 第一层：核心账户指标 - 大卡片展示 */}
          <div className="grid grid-cols-2 gap-4">
            {/* 账户总价值 - 最重要指标 */}
            <div className="glass-card p-6 border-l-4 border-primary">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-4xl">💰</span>
                    <span className="text-sm text-gray-400 font-medium">账户总价值</span>
                  </div>
                  <div className="text-4xl font-bold text-primary mb-2">
                    ${performance.account_value?.toFixed(2) || '0.00'}
                  </div>
                  {performance.total_return_pct !== undefined && (
                    <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg ${performance.total_return_pct >= 0 ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
                      <span className="text-lg font-bold">
                        {performance.total_return_pct >= 0 ? '▲' : '▼'}
                      </span>
                      <span className="text-lg font-semibold">
                        {Math.abs(performance.total_return_pct).toFixed(2)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 总回报率 - 次重要指标 */}
            <div className={`glass-card p-6 border-l-4 ${performance.total_return_pct >= 0 ? 'border-success' : 'border-danger'}`}>
              <div className="flex items-start justify-between">
                <div className="w-full">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-4xl">📈</span>
                    <span className="text-sm text-gray-400 font-medium">总回报率</span>
                  </div>
                  <div className={`text-4xl font-bold mb-3 ${performance.total_return_pct >= 0 ? 'text-success' : 'text-danger'}`}>
                    {performance.total_return_pct >= 0 ? '+' : ''}{performance.total_return_pct?.toFixed(2) || '0.00'}%
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">盈亏金额</div>
                      <div className={`text-base font-semibold ${(performance.total_return_pct || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                        {(performance.total_return_pct || 0) >= 0 ? '+' : ''}${((performance.account_value || 0) - 10000).toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">日均收益</div>
                      <div className={`text-base font-semibold ${(performance.avg_daily_return || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                        {(performance.avg_daily_return || 0) >= 0 ? '+' : ''}{(performance.avg_daily_return || 0).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 第二层：核心绩效指标 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-card p-4 hover:bg-glass-light/50 transition-all duration-300">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">📊</span>
                <span className="text-sm text-gray-400">夏普比率</span>
              </div>
              <div className="text-2xl font-bold text-warning">
                {performance.sharpe_ratio?.toFixed(2) || '0.00'}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {(performance.sharpe_ratio || 0) > 2 ? '优秀' : (performance.sharpe_ratio || 0) > 1 ? '良好' : '一般'}
              </div>
            </div>

            <div className="glass-card p-4 hover:bg-glass-light/50 transition-all duration-300">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">📉</span>
                <span className="text-sm text-gray-400">最大回撤</span>
              </div>
              <div className="text-2xl font-bold text-danger">
                {Math.abs(performance.max_drawdown_pct || 0).toFixed(2)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {Math.abs(performance.max_drawdown_pct || 0) < 10 ? '优秀' : Math.abs(performance.max_drawdown_pct || 0) < 20 ? '可接受' : '需注意'}
              </div>
            </div>

            <div className="glass-card p-4 hover:bg-glass-light/50 transition-all duration-300">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">🎯</span>
                <span className="text-sm text-gray-400">胜率</span>
              </div>
              <div className="text-2xl font-bold text-success">
                {performance.win_rate_pct?.toFixed(1) || '0.0'}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {(performance.win_rate_pct || 0) > 60 ? '优秀' : (performance.win_rate_pct || 0) > 50 ? '良好' : '一般'}
              </div>
            </div>
          </div>

          {/* 第三层：辅助统计指标 - 紧凑布局 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-card p-3 flex items-center gap-3 hover:bg-glass-light/30 transition-all duration-300">
              <span className="text-2xl">🔄</span>
              <div className="flex-1">
                <div className="text-xs text-gray-500">总交易数</div>
                <div className="text-xl font-bold text-white">{performance.total_trades || 0}</div>
              </div>
            </div>

            <div className="glass-card p-3 flex items-center gap-3 hover:bg-glass-light/30 transition-all duration-300">
              <span className="text-2xl">📍</span>
              <div className="flex-1">
                <div className="text-xs text-gray-500">持仓数量</div>
                <div className="text-xl font-bold text-primary">{performance.open_positions || 0}</div>
              </div>
            </div>

            <div className="glass-card p-3 flex items-center gap-3 hover:bg-glass-light/30 transition-all duration-300">
              <span className="text-2xl">💹</span>
              <div className="flex-1">
                <div className="text-xs text-gray-500">今日盈亏</div>
                <div className={`text-xl font-bold ${(performance.avg_daily_return || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                  {(performance.avg_daily_return || 0) >= 0 ? '+' : ''}{(performance.avg_daily_return || 0).toFixed(2)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {/* Left Column - Candlestick Chart + Positions */}
          <div className="col-span-2 space-y-6">
            <CandlestickChartWrapper symbol="BTCUSDT" initialInterval="5m" />
            <PositionsTable positions={positions} />
          </div>

          {/* Right Column - Performance + AI Decisions */}
          <div className="space-y-6">
            <PerformanceChart data={chartData} />
            <AIDecisions decisions={decisions} />
          </div>
        </div>

        {/* Trades History - Full Width */}
        <TradesHistory maxItems={50} />

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
