'use client'

import { useState, useEffect } from 'react'
import type { PerformanceData } from '@/lib/types'

export function usePerformance(refreshInterval: number = 5000) {
  const [data, setData] = useState<PerformanceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/performance')
        const result = await response.json()

        if (result.success && result.data) {
          setData(result.data)
          setError(null)
        } else {
          setError('Failed to fetch performance data')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    // Initial fetch
    fetchData()

    // Set up polling
    const interval = setInterval(fetchData, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  return { data, loading, error }
}
