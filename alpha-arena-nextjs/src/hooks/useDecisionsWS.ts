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
    // 浏览器环境检查
    if (typeof window === 'undefined') return

    const socket = getSocket()

    // 数据获取函数
    const fetchData = async () => {
      try {
        const response = await fetch('/api/decisions')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
          setLastUpdate(new Date())
        } else {
          setError('Failed to fetch AI decisions')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()

    // 监听WebSocket实时更新（作为备选）
    socket.on('decisions_update', (newData: AIDecision[]) => {
      console.log('🤖 AI Decisions update received via WebSocket')
      setData(newData)
      setLastUpdate(new Date())
      setError(null)
    })

    // 监听新的AI决策(单个)
    socket.on('new_decision', (decision: AIDecision) => {
      console.log('🆕 New AI decision received:', decision.symbol, decision.action)
      // 保留所有历史记录，最多200条（避免内存溢出）
      setData(prev => [decision, ...prev].slice(0, 200))
      setLastUpdate(new Date())
    })

    // 同时使用定时轮询作为fallback（每5秒刷新，决策更新频率较低）
    const pollingInterval = setInterval(() => {
      fetchData()
    }, 5000)

    // 清理
    return () => {
      socket.off('decisions_update')
      socket.off('new_decision')
      clearInterval(pollingInterval)
    }
  }, [])

  return { data, loading, error, lastUpdate }
}
