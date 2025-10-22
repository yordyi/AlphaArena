'use client'

import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts'
import { useBinanceKline } from '@/hooks/useBinanceWS'

interface CandlestickChartProps {
  symbol?: string
  initialInterval?: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
}

export function CandlestickChart({
  symbol = 'BTCUSDT',
  initialInterval = '5m'
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)

  const [interval, setInterval] = useState(initialInterval)
  const [historicalData, setHistoricalData] = useState<CandlestickData[]>([])
  const [volumeData, setVolumeData] = useState<HistogramData[]>([])

  // 订阅实时K线数据
  const { data: klineData, connected, latency } = useBinanceKline([symbol], interval)

  // 初始化图表
  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.3)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.3)' },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#06b6d4',
          width: 1,
          style: 2,
          labelBackgroundColor: '#06b6d4',
        },
        horzLine: {
          color: '#06b6d4',
          width: 1,
          style: 2,
          labelBackgroundColor: '#06b6d4',
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(42, 46, 57, 0.5)',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: 'rgba(42, 46, 57, 0.5)',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    // K线主图
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    // 成交量副图
    const volumeSeries = chart.addHistogramSeries({
      color: '#06b6d4',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries

    // 响应式调整大小
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  // 获取历史K线数据
  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        // 调用Binance API获取历史K线
        const response = await fetch(
          `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=500`
        )
        const data = await response.json()

        const candlesticks: CandlestickData[] = []
        const volumes: HistogramData[] = []

        data.forEach((kline: any) => {
          const time = Math.floor(kline[0] / 1000) // Convert to seconds
          const open = parseFloat(kline[1])
          const high = parseFloat(kline[2])
          const low = parseFloat(kline[3])
          const close = parseFloat(kline[4])
          const volume = parseFloat(kline[5])

          candlesticks.push({ time, open, high, low, close })

          // 成交量颜色：涨绿跌红
          const color = close >= open ? '#10b981' : '#ef4444'
          volumes.push({
            time,
            value: volume,
            color: color + '80', // 添加透明度
          })
        })

        setHistoricalData(candlesticks)
        setVolumeData(volumes)

        // 更新图表
        if (candlestickSeriesRef.current && volumeSeriesRef.current) {
          candlestickSeriesRef.current.setData(candlesticks)
          volumeSeriesRef.current.setData(volumes)
        }
      } catch (error) {
        console.error('Failed to fetch historical klines:', error)
      }
    }

    fetchHistoricalData()
  }, [symbol, interval])

  // 实时更新K线数据
  useEffect(() => {
    if (!klineData || !candlestickSeriesRef.current || !volumeSeriesRef.current) return

    const time = Math.floor(klineData.openTime / 1000)
    const open = parseFloat(klineData.open)
    const high = parseFloat(klineData.high)
    const low = parseFloat(klineData.low)
    const close = parseFloat(klineData.close)
    const volume = parseFloat(klineData.volume)

    const candlestick: CandlestickData = { time, open, high, low, close }
    const color = close >= open ? '#10b981' : '#ef4444'
    const volumeBar: HistogramData = {
      time,
      value: volume,
      color: color + '80',
    }

    // 更新最新的K线
    candlestickSeriesRef.current.update(candlestick)
    volumeSeriesRef.current.update(volumeBar)
  }, [klineData])

  // 切换时间周期
  const handleIntervalChange = (newInterval: typeof interval) => {
    setInterval(newInterval)
  }

  const intervals: (typeof interval)[] = ['1m', '5m', '15m', '1h', '4h', '1d']

  return (
    <div className="glass-card-hover p-6 group/chart">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg group-hover/chart:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📈</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gradient-cyan">实时K线图</h2>
            <p className="text-xs text-gray-500">{symbol} - TradingView风格</p>
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
              <span className="text-xs text-success font-semibold">实时</span>
              <span className="text-xs text-gray-500">
                延迟: <span className="text-primary font-mono">{latency}ms</span>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-danger rounded-full"></div>
              <span className="text-xs text-danger font-semibold">离线</span>
            </div>
          )}
        </div>
      </div>

      {/* 时间周期选择器 */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-400">周期:</span>
        {intervals.map((int) => (
          <button
            key={int}
            onClick={() => handleIntervalChange(int)}
            className={`
              px-3 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300
              ${
                interval === int
                  ? 'bg-primary text-white shadow-glow-cyan'
                  : 'bg-glass-light text-gray-400 hover:bg-glass-light/80 hover:text-white'
              }
            `}
          >
            {int}
          </button>
        ))}
      </div>

      {/* 图表容器 */}
      <div className="relative rounded-lg overflow-hidden border border-glass-border backdrop-blur-sm bg-gradient-to-br from-glass-light/30 to-glass/30">
        <div ref={chartContainerRef} className="w-full" />

        {/* 数据加载提示 */}
        {historicalData.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-glass/50 backdrop-blur-sm">
            <div className="text-center">
              <div className="text-4xl mb-2">⏳</div>
              <div className="text-sm text-gray-400">加载K线数据...</div>
            </div>
          </div>
        )}
      </div>

      {/* 底部信息 */}
      <div className="mt-4 pt-4 border-t border-glass-border flex items-center justify-between text-xs text-gray-500">
        <div>
          共 {historicalData.length} 根K线
        </div>
        {klineData && (
          <div className="flex items-center gap-4 text-xs">
            <div>
              <span className="text-gray-500">开: </span>
              <span className="text-white font-mono">{parseFloat(klineData.open).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">高: </span>
              <span className="text-success font-mono">{parseFloat(klineData.high).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">低: </span>
              <span className="text-danger font-mono">{parseFloat(klineData.low).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">收: </span>
              <span className="text-white font-mono font-bold">{parseFloat(klineData.close).toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">量: </span>
              <span className="text-primary font-semibold">{parseFloat(klineData.volume).toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
