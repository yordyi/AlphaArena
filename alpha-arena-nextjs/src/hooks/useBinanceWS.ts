'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Binance WebSocket 实时市场数据 Hook
 *
 * 支持的流类型:
 * - ticker: 24小时价格变动统计
 * - kline: K线数据
 * - depth: 深度/订单簿数据
 * - trade: 最新成交数据
 * - aggTrade: 归集交易数据
 */

interface BinanceTickerData {
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

interface BinanceKlineData {
  symbol: string
  interval: string
  openTime: number
  closeTime: number
  open: string
  high: string
  low: string
  close: string
  volume: string
  isClosed: boolean
}

interface BinanceDepthData {
  symbol: string
  bids: [string, string][] // [price, quantity]
  asks: [string, string][]
  timestamp: number
}

interface BinanceTradeData {
  symbol: string
  price: string
  quantity: string
  timestamp: number
  isBuyerMaker: boolean
}

type MarketData = BinanceTickerData | BinanceKlineData | BinanceDepthData | BinanceTradeData

interface UseBinanceWSOptions {
  symbols: string[]        // 交易对列表，如 ['BTCUSDT', 'ETHUSDT']
  streamType: 'ticker' | 'kline' | 'depth' | 'trade' | 'aggTrade'
  interval?: string        // K线周期，如 '1m', '5m', '1h'
  depthLevel?: 5 | 10 | 20 // 深度档位
}

interface UseBinanceWSReturn<T> {
  data: T | null
  connected: boolean
  error: string | null
  latency: number  // 延迟（毫秒）
  reconnect: () => void
}

const BINANCE_WS_BASE = 'wss://stream.binance.com:9443/ws'
const BINANCE_FUTURES_WS_BASE = 'wss://fstream.binance.com/ws'

/**
 * Binance WebSocket Hook
 *
 * @example
 * // 订阅BTC和ETH的24小时价格统计
 * const { data, connected, latency } = useBinanceWS({
 *   symbols: ['BTCUSDT', 'ETHUSDT'],
 *   streamType: 'ticker'
 * })
 *
 * @example
 * // 订阅BTC的1分钟K线
 * const { data, connected } = useBinanceWS({
 *   symbols: ['BTCUSDT'],
 *   streamType: 'kline',
 *   interval: '1m'
 * })
 */
export function useBinanceWS<T = MarketData>({
  symbols,
  streamType,
  interval = '1m',
  depthLevel = 10,
}: UseBinanceWSOptions): UseBinanceWSReturn<T> {
  const [data, setData] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [latency, setLatency] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const lastMessageTimeRef = useRef<number>(0)

  // 构建WebSocket URL
  const buildStreamUrl = useCallback(() => {
    const streams = symbols.map((symbol) => {
      const s = symbol.toLowerCase()

      switch (streamType) {
        case 'ticker':
          return `${s}@ticker`
        case 'kline':
          return `${s}@kline_${interval}`
        case 'depth':
          return `${s}@depth${depthLevel}@100ms`
        case 'trade':
          return `${s}@trade`
        case 'aggTrade':
          return `${s}@aggTrade`
        default:
          return `${s}@ticker`
      }
    })

    // 使用组合流（Combined Streams）
    if (streams.length === 1) {
      return `${BINANCE_WS_BASE}/${streams[0]}`
    } else {
      return `${BINANCE_WS_BASE}/stream?streams=${streams.join('/')}`
    }
  }, [symbols, streamType, interval, depthLevel])

  // 解析消息
  const parseMessage = useCallback((rawData: any): T | null => {
    try {
      // 组合流返回格式: { stream: "btcusdt@ticker", data: {...} }
      const messageData = rawData.data || rawData

      switch (streamType) {
        case 'ticker': {
          return {
            symbol: messageData.s,
            priceChange: messageData.p,
            priceChangePercent: messageData.P,
            lastPrice: messageData.c,
            volume: messageData.v,
            quoteVolume: messageData.q,
            openPrice: messageData.o,
            highPrice: messageData.h,
            lowPrice: messageData.l,
            timestamp: messageData.E,
          } as T
        }

        case 'kline': {
          const k = messageData.k
          return {
            symbol: messageData.s,
            interval: k.i,
            openTime: k.t,
            closeTime: k.T,
            open: k.o,
            high: k.h,
            low: k.l,
            close: k.c,
            volume: k.v,
            isClosed: k.x,
          } as T
        }

        case 'depth': {
          return {
            symbol: messageData.s || symbols[0].toUpperCase(),
            bids: messageData.b || messageData.bids,
            asks: messageData.a || messageData.asks,
            timestamp: messageData.E || Date.now(),
          } as T
        }

        case 'trade':
        case 'aggTrade': {
          return {
            symbol: messageData.s,
            price: messageData.p,
            quantity: messageData.q,
            timestamp: messageData.T,
            isBuyerMaker: messageData.m,
          } as T
        }

        default:
          return messageData as T
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err)
      return null
    }
  }, [streamType, symbols])

  // 连接WebSocket
  const connect = useCallback(() => {
    // 只在浏览器环境中运行
    if (typeof window === 'undefined') {
      console.warn('⚠️ WebSocket 只能在浏览器环境中运行')
      return
    }

    try {
      const url = buildStreamUrl()
      console.log(`🔌 连接 Binance WebSocket: ${url}`)

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('✅ Binance WebSocket 已连接')
        setConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data)

          // 计算延迟
          const now = Date.now()
          const messageTime = rawData.E || rawData.data?.E || now
          const calculatedLatency = now - messageTime
          setLatency(calculatedLatency)
          lastMessageTimeRef.current = now

          // 解析并更新数据
          const parsed = parseMessage(rawData)
          if (parsed) {
            setData(parsed)
          }
        } catch (err) {
          console.error('WebSocket 消息解析错误:', err)
        }
      }

      ws.onerror = (event) => {
        console.error('❌ WebSocket 连接错误:', {
          type: event.type,
          url: url,
          readyState: ws.readyState,
          message: 'Failed to connect to Binance WebSocket'
        })
        setError('WebSocket connection error')
        setConnected(false)
      }

      ws.onclose = () => {
        console.log('🔌 WebSocket 已断开')
        setConnected(false)

        // 自动重连（5秒后）
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 尝试重新连接...')
          connect()
        }, 5000)
      }
    } catch (err) {
      console.error('WebSocket 连接失败:', err)
      setError('Failed to connect to Binance WebSocket')
    }
  }, [buildStreamUrl, parseMessage])

  // 手动重连
  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connect()
  }, [connect])

  // 初始化连接
  useEffect(() => {
    connect()

    // 清理函数
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return {
    data,
    connected,
    error,
    latency,
    reconnect,
  }
}

/**
 * 订阅多个交易对的24小时价格统计
 *
 * @example
 * const { data, connected, latency } = useBinanceTicker(['BTCUSDT', 'ETHUSDT'])
 */
export function useBinanceTicker(symbols: string[]) {
  return useBinanceWS<BinanceTickerData>({
    symbols,
    streamType: 'ticker',
  })
}

/**
 * 订阅K线数据
 *
 * @example
 * const { data } = useBinanceKline(['BTCUSDT'], '1m')
 */
export function useBinanceKline(symbols: string[], interval: string = '1m') {
  return useBinanceWS<BinanceKlineData>({
    symbols,
    streamType: 'kline',
    interval,
  })
}

/**
 * 订阅深度/订单簿数据
 *
 * @example
 * const { data } = useBinanceDepth(['BTCUSDT'], 20)
 */
export function useBinanceDepth(symbols: string[], depthLevel: 5 | 10 | 20 = 10) {
  return useBinanceWS<BinanceDepthData>({
    symbols,
    streamType: 'depth',
    depthLevel,
  })
}

/**
 * 订阅实时成交数据
 *
 * @example
 * const { data } = useBinanceTrade(['BTCUSDT'])
 */
export function useBinanceTrade(symbols: string[]) {
  return useBinanceWS<BinanceTradeData>({
    symbols,
    streamType: 'trade',
  })
}
