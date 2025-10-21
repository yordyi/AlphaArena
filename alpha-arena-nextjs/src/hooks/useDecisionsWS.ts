'use client'

import { useState, useEffect } from 'react'
import { getSocket } from '@/lib/websocket'
import type { AIDecision } from '@/lib/types'

export function useDecisionsWS() {
  const [data, setData] = useState<AIDecision[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    const socket = getSocket()

    // 初始数据获取
    const fetchInitialData = async () => {
      try {
        const response = await fetch('/api/decisions')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
          setLastUpdate(new Date())
        } else {
          setError('Failed to fetch initial AI decisions')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchInitialData()

    // 监听WebSocket实时更新
    socket.on('decisions_update', (newData: AIDecision[]) => {
      console.log('🤖 AI Decisions update received via WebSocket')
      setData(newData)
      setLastUpdate(new Date())
      setError(null)
    })

    // 监听新的AI决策(单个)
    socket.on('new_decision', (decision: AIDecision) => {
      console.log('🆕 New AI decision received:', decision.symbol, decision.action)
      setData(prev => [decision, ...prev].slice(0, 20)) // 保持最新20条
      setLastUpdate(new Date())
    })

    // 清理
    return () => {
      socket.off('decisions_update')
      socket.off('new_decision')
    }
  }, [])

  return { data, loading, error, lastUpdate }
}
