'use client'

import dynamic from 'next/dynamic'

// 动态导入K线图组件，禁用SSR
const CandlestickChart = dynamic(
  () => import('./CandlestickChart').then((mod) => ({ default: mod.CandlestickChart })),
  {
    ssr: false,
    loading: () => (
      <div className="glass-card-hover p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-primary/10 rounded-lg">
            <span className="text-2xl">📈</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">实时K线图</h2>
        </div>
        <div className="relative rounded-lg overflow-hidden border border-glass-border backdrop-blur-sm bg-gradient-to-br from-glass-light/30 to-glass/30 h-[500px] flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-2">⏳</div>
            <div className="text-sm text-gray-400">加载图表组件...</div>
          </div>
        </div>
      </div>
    ),
  }
)

interface CandlestickChartWrapperProps {
  symbol?: string
  initialInterval?: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
}

export function CandlestickChartWrapper(props: CandlestickChartWrapperProps) {
  return <CandlestickChart {...props} />
}
