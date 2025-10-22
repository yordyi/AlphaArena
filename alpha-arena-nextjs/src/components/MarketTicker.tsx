'use client'

import { useState, useEffect } from 'react'
import { useBinanceWS } from '@/hooks/useBinanceWS'

interface MarketTickerProps {
  symbols?: string[]  // 默认显示 BTC, ETH, BNB
}

interface TickerData {
  symbol: string
  priceChange: string
  priceChangePercent: string
  lastPrice: string
  volume: string
  quoteVolume: string
  openPrice: string
  highPrice: string
  lowPrice: string
  timestamp: number
}

export function MarketTicker({ symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] }: MarketTickerProps) {
  const [tickerMap, setTickerMap] = useState<Record<string, TickerData>>({})
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // 订阅所有交易对的实时行情
  const { data, connected, latency, reconnect } = useBinanceWS<TickerData>({
    symbols,
    streamType: 'ticker',
  })

  // 更新行情数据
  useEffect(() => {
    if (data) {
      setTickerMap((prev) => ({
        ...prev,
        [data.symbol]: data,
      }))
      setLastUpdate(new Date())
    }
  }, [data])

  // 格式化价格
  const formatPrice = (price: string) => {
    const num = parseFloat(price)
    if (num >= 1000) return num.toFixed(2)
    if (num >= 1) return num.toFixed(4)
    return num.toFixed(6)
  }

  // 格式化成交量（缩写）
  const formatVolume = (volume: string) => {
    const num = parseFloat(volume)
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`
    return num.toFixed(2)
  }

  // 格式化百分比
  const formatPercent = (percent: string) => {
    const num = parseFloat(percent)
    return num.toFixed(2)
  }

  return (
    <div className="glass-card-hover p-6 group/ticker">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-success/10 rounded-lg group-hover/ticker:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📊</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gradient-cyan">实时行情</h2>
            <p className="text-xs text-gray-500">Binance WebSocket 直连</p>
          </div>
        </div>

        {/* 连接状态 */}
        <div className="flex items-center gap-3">
          {connected ? (
            <div className="flex items-center gap-2">
              <div className="relative">
                <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
                <div className="absolute inset-0 w-2 h-2 bg-success rounded-full animate-ping"></div>
              </div>
              <span className="text-xs text-success font-semibold">已连接</span>
              <span className="text-xs text-gray-500">
                延迟: <span className="text-primary font-mono">{latency}ms</span>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-danger rounded-full"></div>
              <span className="text-xs text-danger font-semibold">未连接</span>
              <button
                onClick={reconnect}
                className="text-xs text-primary hover:text-cyan-400 transition-colors"
              >
                重连
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 行情网格 */}
      <div className="grid grid-cols-3 gap-4">
        {symbols.map((symbol) => {
          const ticker = tickerMap[symbol]

          if (!ticker) {
            // 加载中状态
            return (
              <div
                key={symbol}
                className="backdrop-blur-sm bg-gradient-to-br from-glass-light/30 to-glass/30 border border-glass-border rounded-lg p-4"
              >
                <div className="text-center py-8 text-gray-500 text-sm">
                  等待数据...
                </div>
              </div>
            )
          }

          const priceChangeNum = parseFloat(ticker.priceChangePercent)
          const isPositive = priceChangeNum >= 0
          const changeColor = isPositive ? 'text-success' : 'text-danger'
          const changeBg = isPositive ? 'bg-success/10' : 'bg-danger/10'
          const changeBorder = isPositive ? 'border-success/30' : 'border-danger/30'

          return (
            <div
              key={symbol}
              className="backdrop-blur-sm bg-gradient-to-br from-glass-light/30 to-glass/30 border border-glass-border rounded-lg p-4 hover:border-primary/30 transition-all duration-300 group/card"
            >
              {/* 交易对名称 */}
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-white text-lg group-hover/card:text-primary transition-colors">
                  {symbol.replace('USDT', '')}
                  <span className="text-gray-500 text-sm ml-1">/USDT</span>
                </h3>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${changeBg} ${changeColor} border ${changeBorder}`}>
                  {isPositive ? '↑' : '↓'}
                  {formatPercent(ticker.priceChangePercent)}%
                </span>
              </div>

              {/* 当前价格 */}
              <div className="mb-3">
                <div className={`text-2xl font-bold ${changeColor} font-mono`}>
                  ${formatPrice(ticker.lastPrice)}
                </div>
                <div className={`text-sm ${changeColor} font-medium`}>
                  {isPositive ? '+' : ''}${formatPrice(ticker.priceChange)}
                </div>
              </div>

              {/* 24小时统计 */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">24h最高: </span>
                  <span className="text-white font-mono">${formatPrice(ticker.highPrice)}</span>
                </div>
                <div>
                  <span className="text-gray-500">24h最低: </span>
                  <span className="text-white font-mono">${formatPrice(ticker.lowPrice)}</span>
                </div>
                <div>
                  <span className="text-gray-500">成交量: </span>
                  <span className="text-primary font-semibold">{formatVolume(ticker.volume)}</span>
                </div>
                <div>
                  <span className="text-gray-500">成交额: </span>
                  <span className="text-warning font-semibold">${formatVolume(ticker.quoteVolume)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* 底部信息栏 */}
      {lastUpdate && (
        <div className="mt-4 pt-4 border-t border-glass-border flex items-center justify-between text-xs text-gray-500">
          <div>
            最后更新: {String(lastUpdate.getHours()).padStart(2, '0')}:{String(lastUpdate.getMinutes()).padStart(2, '0')}:{String(lastUpdate.getSeconds()).padStart(2, '0')}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse"></div>
            实时更新中
          </div>
        </div>
      )}
    </div>
  )
}
