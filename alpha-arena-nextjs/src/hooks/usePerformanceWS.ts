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
    const socket = getSocket()

    // 初始数据获取
    const fetchInitialData = async () => {
      try {
        const response = await fetch('/api/performance')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
          setLastUpdate(new Date())
        } else {
          setError('Failed to fetch initial performance data')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchInitialData()

    // 监听WebSocket实时更新
    socket.on('performance_update', (newData: PerformanceData) => {
      console.log('📊 Performance update received via WebSocket')
      setData(newData)
      setLastUpdate(new Date())
      setError(null)
    })

    // 清理
    return () => {
      socket.off('performance_update')
    }
  }, [])

  return { data, loading, error, lastUpdate }
}
