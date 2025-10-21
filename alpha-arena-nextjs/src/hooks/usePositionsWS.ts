'use client'

import { useState, useEffect } from 'react'
import { getSocket } from '@/lib/websocket'
import type { Position } from '@/lib/types'

export function usePositionsWS() {
  const [data, setData] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    const socket = getSocket()

    // 初始数据获取
    const fetchInitialData = async () => {
      try {
        const response = await fetch('/api/positions')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
          setLastUpdate(new Date())
        } else {
          setError('Failed to fetch initial positions')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchInitialData()

    // 监听WebSocket实时更新
    socket.on('positions_update', (newData: Position[]) => {
      console.log('📍 Positions update received via WebSocket')
      setData(newData)
      setLastUpdate(new Date())
      setError(null)
    })

    // 清理
    return () => {
      socket.off('positions_update')
    }
  }, [])

  return { data, loading, error, lastUpdate }
}
