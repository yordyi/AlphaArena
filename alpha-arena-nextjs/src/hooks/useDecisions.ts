'use client'

import { useState, useEffect } from 'react'
import type { AIDecision } from '@/lib/types'

export function useDecisions(refreshInterval: number = 5000) {
  const [data, setData] = useState<AIDecision[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/decisions')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
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
    const interval = setInterval(fetchData, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  return { data, loading, error }
}
