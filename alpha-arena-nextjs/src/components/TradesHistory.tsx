'use client'

import { useState, useEffect } from 'react'

interface Trade {
  time: string
  symbol: string
  action: string
  quantity: number
  price: number
  leverage: number
  confidence: number
  reasoning?: string
  stop_loss?: number
  take_profit?: number
}

interface TradesHistoryProps {
  maxItems?: number
}

export function TradesHistory({ maxItems = 50 }: TradesHistoryProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await fetch('/api/trades')
        const result = await response.json()
        if (result.success && result.data) {
          // 反转数组，最新的在前面，并限制数量
          setTrades(result.data.reverse().slice(0, maxItems))
        }
      } catch (error) {
        console.error('Failed to fetch trades:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTrades()
    // 每60秒刷新一次
    const interval = setInterval(fetchTrades, 60000)
    return () => clearInterval(interval)
  }, [maxItems])

  const getActionConfig = (action: string) => {
    if (action.includes('LONG') || action === 'BUY') {
      return {
        color: 'bg-success/20 text-success border-success/30',
        icon: '↗',
        label: '做多',
      }
    }
    if (action.includes('SHORT') || action === 'SELL') {
      return {
        color: 'bg-danger/20 text-danger border-danger/30',
        icon: '↘',
        label: '做空',
      }
    }
    if (action === 'CLOSE') {
      return {
        color: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
        icon: '✕',
        label: '平仓',
      }
    }
    return {
      color: 'bg-primary/20 text-primary border-primary/30',
      icon: '•',
      label: action,
    }
  }

  const formatTime = (time: string) => {
    const date = new Date(time)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hours}:${minutes}`
  }

  if (loading) {
    return (
      <div className="glass-card-hover p-6 group">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-warning/10 rounded-lg">
            <span className="text-2xl">📜</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">交易历史</h2>
        </div>
        <div className="text-center py-8 text-gray-400">加载中...</div>
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="glass-card-hover p-6 group">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-warning/10 rounded-lg group-hover:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📜</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">交易历史</h2>
        </div>
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-glass-light mb-4">
            <span className="text-4xl opacity-50">📋</span>
          </div>
          <p className="text-gray-400 text-sm">暂无交易记录</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card-hover p-6 group/container">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-warning/10 rounded-lg group-hover/container:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📜</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">交易历史</h2>
        </div>
        <div className="badge-primary">
          {trades.length} 笔
        </div>
      </div>

      {/* 交易列表 */}
      <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
        {trades.map((trade, index) => {
          const actionConfig = getActionConfig(trade.action)
          const isExpanded = expanded === index

          return (
            <div
              key={index}
              className="group relative backdrop-blur-sm bg-gradient-to-br from-glass-light/30 to-glass/30 border border-glass-border rounded-lg p-3 transition-all duration-300 hover:border-primary/30 cursor-pointer"
              onClick={() => setExpanded(isExpanded ? null : index)}
            >
              {/* 简要信息 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">{formatTime(trade.time)}</span>
                  <span className="font-bold text-white">{trade.symbol}</span>
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold border ${actionConfig.color}`}>
                    <span>{actionConfig.icon}</span>
                    <span>{actionConfig.label}</span>
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-300">
                    {trade.quantity} @ ${trade.price.toLocaleString()}
                  </span>
                  <span className="text-xs bg-warning/20 text-warning px-2 py-0.5 rounded border border-warning/30">
                    {trade.leverage}x
                  </span>
                  <span className="text-xs text-gray-500">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </div>

              {/* 展开详情 */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-glass-border space-y-2">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500">信心度: </span>
                      <span className="text-primary font-semibold">{trade.confidence}%</span>
                    </div>
                    {trade.stop_loss && (
                      <div>
                        <span className="text-gray-500">止损: </span>
                        <span className="text-danger">${trade.stop_loss.toLocaleString()}</span>
                      </div>
                    )}
                    {trade.take_profit && (
                      <div>
                        <span className="text-gray-500">止盈: </span>
                        <span className="text-success">${trade.take_profit.toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  {trade.reasoning && (
                    <div className="text-xs text-gray-400 leading-relaxed pl-3 border-l-2 border-primary/30">
                      {trade.reasoning}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
