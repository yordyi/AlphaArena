'use client'

import { useState, useEffect } from 'react'
import type { Position } from '@/lib/types'

export function usePositions(refreshInterval: number = 5000) {
  const [data, setData] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/positions')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
        } else {
          setError('Failed to fetch positions')
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
