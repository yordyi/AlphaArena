import type { Position } from '@/lib/types'

interface PositionsTableProps {
  positions: Position[]
}

export function PositionsTable({ positions }: PositionsTableProps) {
  if (positions.length === 0) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-lg font-bold mb-4">📊 当前持仓</h2>
        <div className="text-center py-8 text-gray-400">
          暂无持仓
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card p-6">
      <h2 className="text-lg font-bold mb-4">📊 当前持仓</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-glass-border">
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">交易对</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-gray-400 uppercase">方向</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">数量</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">开仓价</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">当前价</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">未实现盈亏</th>
              <th className="text-right py-3 px-4 text-xs font-medium text-gray-400 uppercase">杠杆</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position, index) => {
              const pnlColor = position.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'
              const sideColor = position.side === 'LONG' ? 'text-success' : 'text-danger'

              return (
                <tr
                  key={`${position.symbol}-${index}`}
                  className="border-b border-glass-border hover:bg-white/5 transition-colors"
                >
                  <td className="py-3 px-4 font-medium">{position.symbol}</td>
                  <td className="py-3 px-4">
                    <span className={`font-bold ${sideColor}`}>
                      {position.side}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">{position.size.toFixed(4)}</td>
                  <td className="text-right py-3 px-4">${position.entry_price.toLocaleString()}</td>
                  <td className="text-right py-3 px-4">${position.current_price.toLocaleString()}</td>
                  <td className={`text-right py-3 px-4 font-bold ${pnlColor}`}>
                    ${position.unrealized_pnl.toFixed(2)}
                    <span className="text-xs ml-1">
                      ({position.unrealized_pnl_pct >= 0 ? '+' : ''}{position.unrealized_pnl_pct.toFixed(2)}%)
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">{position.leverage}x</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
