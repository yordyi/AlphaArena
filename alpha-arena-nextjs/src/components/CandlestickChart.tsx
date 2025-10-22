'use client'

import { useEffect, useRef, useState } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, HistogramData, LineData } from 'lightweight-charts'
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
  const ma7SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const ma25SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const ma99SeriesRef = useRef<ISeriesApi<'Line'> | null>(null)

  const [interval, setInterval] = useState(initialInterval)
  const [currentSymbol, setCurrentSymbol] = useState(symbol)
  const [historicalData, setHistoricalData] = useState<CandlestickData[]>([])
  const [volumeData, setVolumeData] = useState<HistogramData[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [priceChange, setPriceChange] = useState({ value: 0, percent: 0 })

  // 订阅实时K线数据
  const { data: klineData, connected, latency } = useBinanceKline([currentSymbol], interval)

  // 计算移动平均线
  const calculateMA = (data: CandlestickData[], period: number): LineData[] => {
    const result: LineData[] = []
    for (let i = period - 1; i < data.length; i++) {
      const sum = data.slice(i - period + 1, i + 1).reduce((acc, item) => acc + item.close, 0)
      result.push({
        time: data[i].time,
        value: sum / period
      })
    }
    return result
  }

  // 初始化图表
  useEffect(() => {
    // 只在浏览器环境中运行
    if (typeof window === 'undefined') {
      console.log('🚫 SSR环境，跳过图表初始化')
      return
    }
    if (!chartContainerRef.current) return

    console.log('🔍 创建图表中...', {
      hasCreateChart: typeof createChart === 'function',
      containerWidth: chartContainerRef.current.clientWidth
    })

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

    console.log('✅ Chart对象创建完成:', {
      chartType: typeof chart,
      hasAddCandlestickSeries: typeof chart.addCandlestickSeries === 'function',
      chartMethods: Object.getOwnPropertyNames(Object.getPrototypeOf(chart)).slice(0, 10)
    })

    // 保护性检查
    if (typeof chart.addCandlestickSeries !== 'function') {
      console.error('❌ chart.addCandlestickSeries 不是函数！', {
        chartType: typeof chart,
        chartConstructor: chart.constructor.name,
        availableMethods: Object.keys(chart)
      })
      return
    }

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

    // 添加移动平均线
    const ma7Series = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 2,
      title: 'MA7',
    })

    const ma25Series = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 2,
      title: 'MA25',
    })

    const ma99Series = chart.addLineSeries({
      color: '#06b6d4',
      lineWidth: 2,
      title: 'MA99',
    })

    chartRef.current = chart
    candlestickSeriesRef.current = candlestickSeries
    volumeSeriesRef.current = volumeSeries
    ma7SeriesRef.current = ma7Series
    ma25SeriesRef.current = ma25Series
    ma99SeriesRef.current = ma99Series

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
    // 只在浏览器环境中运行
    if (typeof window === 'undefined') return

    const fetchHistoricalData = async () => {
      try {
        console.log(`📊 开始获取历史K线: ${currentSymbol} ${interval}`)

        // 调用Binance API获取历史K线 (修复bug: 使用currentSymbol而不是symbol)
        const response = await fetch(
          `https://api.binance.com/api/v3/klines?symbol=${currentSymbol}&interval=${interval}&limit=500`
        )

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()

        if (!Array.isArray(data)) {
          throw new Error('Invalid API response format')
        }

        console.log(`✅ 获取到 ${data.length} 根K线`)

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

        // 计算价格变化
        if (candlesticks.length >= 2) {
          const firstPrice = candlesticks[0].close
          const lastPrice = candlesticks[candlesticks.length - 1].close
          const change = lastPrice - firstPrice
          const changePercent = (change / firstPrice) * 100
          setPriceChange({ value: change, percent: changePercent })
        }

        // 更新图表
        if (candlestickSeriesRef.current && volumeSeriesRef.current) {
          console.log('📈 更新图表数据...')
          candlestickSeriesRef.current.setData(candlesticks)
          volumeSeriesRef.current.setData(volumes)

          // 计算并显示移动平均线
          if (ma7SeriesRef.current && candlesticks.length >= 7) {
            const ma7Data = calculateMA(candlesticks, 7)
            ma7SeriesRef.current.setData(ma7Data)
            console.log(`✅ MA7: ${ma7Data.length} 个数据点`)
          }

          if (ma25SeriesRef.current && candlesticks.length >= 25) {
            const ma25Data = calculateMA(candlesticks, 25)
            ma25SeriesRef.current.setData(ma25Data)
            console.log(`✅ MA25: ${ma25Data.length} 个数据点`)
          }

          if (ma99SeriesRef.current && candlesticks.length >= 99) {
            const ma99Data = calculateMA(candlesticks, 99)
            ma99SeriesRef.current.setData(ma99Data)
            console.log(`✅ MA99: ${ma99Data.length} 个数据点`)
          }

          // 自动缩放到最新数据
          if (chartRef.current) {
            chartRef.current.timeScale().fitContent()
          }
        } else {
          console.warn('⚠️ 图表序列尚未初始化')
        }
      } catch (error) {
        console.error('❌ 获取历史K线失败:', error)
      }
    }

    fetchHistoricalData()
  }, [currentSymbol, interval])

  // 实时更新K线数据
  useEffect(() => {
    // 只在浏览器环境中运行
    if (typeof window === 'undefined') return
    if (!klineData || !candlestickSeriesRef.current || !volumeSeriesRef.current) return

    try {
      const time = Math.floor(klineData.openTime / 1000)
      const open = parseFloat(klineData.open)
      const high = parseFloat(klineData.high)
      const low = parseFloat(klineData.low)
      const close = parseFloat(klineData.close)
      const volume = parseFloat(klineData.volume)

      console.log(`⚡ 实时K线更新: ${currentSymbol} ${new Date(time * 1000).toLocaleTimeString()} O:${open} H:${high} L:${low} C:${close}`)

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

      // 更新历史数据数组（用于MA计算和价格变化）
      setHistoricalData(prevData => {
        const newData = [...prevData]
        // 检查是否是新K线还是更新现有K线
        const lastIndex = newData.length - 1
        if (lastIndex >= 0 && newData[lastIndex].time === time) {
          // 更新现有K线
          newData[lastIndex] = candlestick
        } else {
          // 新K线
          newData.push(candlestick)
          // 保持最多500根K线
          if (newData.length > 500) {
            newData.shift()
          }
        }

        // 实时更新移动平均线
        if (ma7SeriesRef.current && newData.length >= 7) {
          const ma7Data = calculateMA(newData, 7)
          ma7SeriesRef.current.setData(ma7Data)
        }

        if (ma25SeriesRef.current && newData.length >= 25) {
          const ma25Data = calculateMA(newData, 25)
          ma25SeriesRef.current.setData(ma25Data)
        }

        if (ma99SeriesRef.current && newData.length >= 99) {
          const ma99Data = calculateMA(newData, 99)
          ma99SeriesRef.current.setData(ma99Data)
        }

        // 更新价格变化
        if (newData.length > 0) {
          const firstPrice = newData[0].close
          const change = close - firstPrice
          const changePercent = (change / firstPrice) * 100
          setPriceChange({ value: change, percent: changePercent })
        }

        return newData
      })
    } catch (error) {
      console.error('❌ 实时K线更新失败:', error)
    }
  }, [klineData, currentSymbol])

  // 切换时间周期
  const handleIntervalChange = (newInterval: typeof interval) => {
    setInterval(newInterval)
  }

  const intervals: (typeof interval)[] = ['1m', '5m', '15m', '1h', '4h', '1d']
  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

  // 全屏切换
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const containerClass = isFullscreen
    ? 'fixed inset-0 z-50 bg-black/95 p-6'
    : 'glass-card-hover p-6 group/chart'

  return (
    <div className={containerClass}>
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg group-hover/chart:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📈</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gradient-cyan">实时K线图</h2>
            <p className="text-xs text-gray-500">{currentSymbol} - TradingView风格</p>
            {/* 价格变化显示 */}
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-sm font-bold ${priceChange.percent >= 0 ? 'text-success' : 'text-danger'}`}>
                {priceChange.percent >= 0 ? '+' : ''}{priceChange.value.toFixed(2)}
              </span>
              <span className={`text-xs font-semibold ${priceChange.percent >= 0 ? 'text-success' : 'text-danger'}`}>
                ({priceChange.percent >= 0 ? '+' : ''}{priceChange.percent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        {/* 连接状态和全屏按钮 */}
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

          {/* 全屏按钮 */}
          <button
            onClick={toggleFullscreen}
            className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-glass-light text-gray-400 hover:bg-glass-light/80 hover:text-white transition-all duration-300"
          >
            {isFullscreen ? '🗗' : '🗖'}
          </button>
        </div>
      </div>

      {/* 币种选择器 */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-400">币种:</span>
        {symbols.map((sym) => (
          <button
            key={sym}
            onClick={() => setCurrentSymbol(sym)}
            className={`
              px-3 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300
              ${
                currentSymbol === sym
                  ? 'bg-success text-white shadow-glow-green'
                  : 'bg-glass-light text-gray-400 hover:bg-glass-light/80 hover:text-white'
              }
            `}
          >
            {sym.replace('USDT', '')}
          </button>
        ))}
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
      <div className="mt-4 pt-4 border-t border-glass-border">
        {/* MA均线图例 */}
        <div className="flex items-center gap-4 mb-3">
          <span className="text-xs text-gray-500">均线:</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-[#f59e0b]"></div>
            <span className="text-xs text-[#f59e0b] font-semibold">MA7</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-[#8b5cf6]"></div>
            <span className="text-xs text-[#8b5cf6] font-semibold">MA25</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-[#06b6d4]"></div>
            <span className="text-xs text-[#06b6d4] font-semibold">MA99</span>
          </div>
        </div>

        {/* 数据信息 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
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
    </div>
  )
}
