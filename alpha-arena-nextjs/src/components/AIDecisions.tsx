import type { AIDecision } from '@/lib/types'

interface AIDecisionsProps {
  decisions: AIDecision[]
}

export function AIDecisions({ decisions }: AIDecisionsProps) {
  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY':
      case 'LONG':
        return 'bg-success/20 text-success border-success/30'
      case 'SELL':
      case 'SHORT':
        return 'bg-danger/20 text-danger border-danger/30'
      case 'HOLD':
        return 'bg-warning/20 text-warning border-warning/30'
      case 'CLOSE':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      default:
        return 'bg-primary/20 text-primary border-primary/30'
    }
  }

  const getConfidenceColor = (confidence: string) => {
    const conf = parseInt(confidence)
    if (conf >= 80) return 'text-success'
    if (conf >= 60) return 'text-warning'
    return 'text-danger'
  }

  if (decisions.length === 0) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-lg font-bold mb-4">🤖 AI实时决策</h2>
        <div className="text-center py-8 text-gray-400">
          等待AI决策...
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card p-6">
      <h2 className="text-lg font-bold mb-4">🤖 AI实时决策</h2>
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {decisions.map((decision, index) => (
          <div
            key={index}
            className="glass-card p-4 border-l-4 border-primary"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">{decision.symbol}</span>
                <span
                  className={`px-2 py-1 rounded-md text-xs font-bold border ${getActionColor(decision.action)}`}
                >
                  {decision.action}
                </span>
              </div>
              <span className={`text-sm font-bold ${getConfidenceColor(decision.confidence)}`}>
                {decision.confidence}%
              </span>
            </div>

            {/* Model */}
            <div className="text-xs text-gray-400 mb-2">
              模型: <span className="text-secondary">{decision.model_used}</span>
            </div>

            {/* Reasoning */}
            <div className="text-sm text-gray-300">
              {decision.reasoning}
            </div>

            {/* Timestamp */}
            {decision.timestamp && (
              <div className="text-xs text-gray-500 mt-2">
                {decision.timestamp}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
