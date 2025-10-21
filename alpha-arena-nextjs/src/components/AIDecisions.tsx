'use client'

import type { AIDecision } from '@/lib/types'

interface AIDecisionsProps {
  decisions: AIDecision[]
}

export function AIDecisions({ decisions }: AIDecisionsProps) {
  const getActionConfig = (action: string) => {
    switch (action) {
      case 'BUY':
      case 'LONG':
        return {
          color: 'bg-success/20 text-success border-success/30',
          icon: '↗',
          glow: 'group-hover:shadow-glow-green',
        }
      case 'SELL':
      case 'SHORT':
        return {
          color: 'bg-danger/20 text-danger border-danger/30',
          icon: '↘',
          glow: 'group-hover:shadow-glow-pink',
        }
      case 'HOLD':
        return {
          color: 'bg-warning/20 text-warning border-warning/30',
          icon: '⏸',
          glow: 'group-hover:shadow-glow-cyan',
        }
      case 'CLOSE':
        return {
          color: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
          icon: '✕',
          glow: '',
        }
      default:
        return {
          color: 'bg-primary/20 text-primary border-primary/30',
          icon: '•',
          glow: 'group-hover:shadow-glow-cyan',
        }
    }
  }

  const getConfidenceConfig = (confidence: string) => {
    const conf = parseInt(confidence)
    if (conf >= 80) {
      return { color: 'text-success', bg: 'bg-success/10', border: 'border-success/30', label: '高' }
    }
    if (conf >= 60) {
      return { color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/30', label: '中' }
    }
    return { color: 'text-danger', bg: 'bg-danger/10', border: 'border-danger/30', label: '低' }
  }

  // 空状态
  if (decisions.length === 0) {
    return (
      <div className="glass-card-hover p-6 group">
        {/* 标题 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-secondary/10 rounded-lg group-hover:shadow-glow-purple transition-all duration-300">
              <span className="text-2xl">🤖</span>
            </div>
            <h2 className="text-xl font-bold text-gradient-purple">AI实时决策</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <div className="w-2 h-2 bg-warning rounded-full animate-pulse" />
            <span>待命中</span>
          </div>
        </div>

        {/* 空状态 */}
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-glass-light mb-4">
            <span className="text-4xl opacity-50">🧠</span>
          </div>
          <p className="text-gray-400 text-sm">AI正在分析市场...</p>
          <p className="text-gray-500 text-xs mt-2">决策将实时显示在这里</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card-hover p-6 group/container">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-secondary/10 rounded-lg group-hover/container:shadow-glow-purple transition-all duration-300">
            <span className="text-2xl">🤖</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-purple">AI实时决策</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
            <span>实时</span>
          </div>
          <div className="badge-primary">
            {decisions.length}
          </div>
        </div>
      </div>

      {/* 决策列表 */}
      <div className="space-y-3 max-h-[700px] overflow-y-auto pr-2 custom-scrollbar">
        {decisions.map((decision, index) => {
          const actionConfig = getActionConfig(decision.action)
          const confidenceConfig = getConfidenceConfig(decision.confidence)

          return (
            <div
              key={index}
              className={`
                group relative
                backdrop-blur-sm
                bg-gradient-to-br from-glass-light/50 to-glass/50
                border-2 border-glass-border
                rounded-xl p-4
                transition-all duration-300
                hover:border-primary/30
                ${actionConfig.glow}
              `}
            >
              {/* 侧边装饰条 */}
              <div className={`
                absolute left-0 top-0 bottom-0 w-1 rounded-l-xl
                ${decision.action === 'BUY' || decision.action === 'LONG' ? 'bg-success' : ''}
                ${decision.action === 'SELL' || decision.action === 'SHORT' ? 'bg-danger' : ''}
                ${decision.action === 'HOLD' ? 'bg-warning' : ''}
                ${decision.action === 'CLOSE' ? 'bg-gray-500' : ''}
              `} />

              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-lg text-white group-hover:text-primary transition-colors">
                    {decision.symbol}
                  </span>
                  <span className={`
                    inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                    text-sm font-bold border-2
                    ${actionConfig.color}
                    transition-all duration-300
                    group-hover:scale-105
                  `}>
                    <span className="text-base">{actionConfig.icon}</span>
                    <span>{decision.action}</span>
                  </span>
                </div>

                {/* 信心度指示器 */}
                <div className="flex items-center gap-2">
                  <div className={`
                    px-2.5 py-1 rounded-lg text-xs font-semibold
                    ${confidenceConfig.color} ${confidenceConfig.bg}
                    border ${confidenceConfig.border}
                  `}>
                    {confidenceConfig.label}
                  </div>
                  <div className={`text-lg font-bold ${confidenceConfig.color}`}>
                    {decision.confidence}%
                  </div>
                </div>
              </div>

              {/* Model Badge */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs text-gray-500">模型:</span>
                <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-secondary/20 text-secondary-light border border-secondary/30">
                  {decision.model_used}
                </span>
              </div>

              {/* Reasoning */}
              <div className="text-sm text-gray-300 leading-relaxed mb-3 pl-4 border-l-2 border-glass-border">
                {decision.reasoning}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-glass-border/50">
                {decision.timestamp && (
                  <div className="flex items-center gap-1.5">
                    <span>🕐</span>
                    <span>{decision.timestamp}</span>
                  </div>
                )}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                  <span className="text-primary">活跃</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* 底部装饰 */}
      <div className="mt-6 pt-4 border-t border-glass-border text-center text-xs text-gray-500">
        <div className="flex items-center justify-center gap-2">
          <span className="opacity-50">🧠</span>
          <span>AI模型持续监控市场动态</span>
        </div>
      </div>
    </div>
  )
}
