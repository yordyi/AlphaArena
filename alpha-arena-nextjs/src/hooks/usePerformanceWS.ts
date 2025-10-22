'use client'

import { useState, useEffect } from 'react'
import { getSocket } from '@/lib/websocket'
import type { PerformanceData } from '@/lib/types'

export function usePerformanceWS() {
  const [data, setData] = useState<PerformanceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    // 浏览器环境检查
    if (typeof window === 'undefined') return

    const socket = getSocket()

    // 初始数据获取
    const fetchData = async () => {
      try {
        const response = await fetch('/api/performance')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
          setLastUpdate(new Date())
        } else {
          setError('Failed to fetch performance data')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // 监听WebSocket实时更新（作为备选）
    socket.on('performance_update', (newData: PerformanceData) => {
      console.log('📊 Performance update received via WebSocket')
      setData(newData)
      setLastUpdate(new Date())
      setError(null)
    })

    // 同时使用定时轮询作为fallback（每2秒刷新）
    const pollingInterval = setInterval(() => {
      fetchData()
    }, 2000)

    // 清理
    return () => {
      socket.off('performance_update')
      clearInterval(pollingInterval)
    }
  }, [])

  return { data, loading, error, lastUpdate }
}
