'use client'

import type { Position } from '@/lib/types'

interface PositionsTableProps {
  positions: Position[]
}

export function PositionsTable({ positions }: PositionsTableProps) {
  // 空状态
  if (positions.length === 0) {
    return (
      <div className="glass-card-hover p-6 group">
        {/* 标题 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg group-hover:shadow-glow-cyan transition-all duration-300">
              <span className="text-2xl">📊</span>
            </div>
            <h2 className="text-xl font-bold text-gradient-cyan">当前持仓</h2>
          </div>
          <div className="badge-primary">
            0 持仓
          </div>
        </div>

        {/* 空状态 */}
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-glass-light mb-4">
            <span className="text-4xl opacity-50">💼</span>
          </div>
          <p className="text-gray-400 text-sm">暂无持仓</p>
          <p className="text-gray-500 text-xs mt-2">开始交易后，持仓信息将显示在这里</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card-hover p-6 group">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg group-hover:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📊</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">当前持仓</h2>
        </div>
        <div className="badge-primary">
          {positions.length} 持仓
        </div>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto -mx-2">
        <table className="w-full">
          {/* 表头 */}
          <thead>
            <tr className="border-b border-glass-border">
              <th className="text-left py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                交易对
              </th>
              <th className="text-left py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                方向
              </th>
              <th className="text-right py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                数量
              </th>
              <th className="text-right py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                开仓价
              </th>
              <th className="text-right py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                当前价
              </th>
              <th className="text-right py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                未实现盈亏
              </th>
              <th className="text-right py-4 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                杠杆
              </th>
            </tr>
          </thead>

          {/* 表体 */}
          <tbody>
            {positions.map((position, index) => {
              const isProfit = position.unrealized_pnl >= 0
              const pnlColor = isProfit ? 'text-success' : 'text-danger'
              const pnlBgColor = isProfit ? 'bg-success/10' : 'bg-danger/10'
              const pnlBorderColor = isProfit ? 'border-success/30' : 'border-danger/30'
              const isLong = position.side === 'LONG'

              return (
                <tr
                  key={`${position.symbol}-${index}`}
                  className="border-b border-glass-border/50 hover:bg-glass-light/50 transition-all duration-300 group/row"
                >
                  {/* 交易对 */}
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white group-hover/row:text-primary transition-colors">
                        {position.symbol}
                      </span>
                    </div>
                  </td>

                  {/* 方向徽章 */}
                  <td className="py-4 px-4">
                    {isLong ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-success/20 text-success border border-success/30">
                        <span>↗</span>
                        <span>LONG</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-danger/20 text-danger border border-danger/30">
                        <span>↘</span>
                        <span>SHORT</span>
                      </span>
                    )}
                  </td>

                  {/* 数量 */}
                  <td className="text-right py-4 px-4 text-gray-300 font-medium">
                    {position.size.toFixed(4)}
                  </td>

                  {/* 开仓价 */}
                  <td className="text-right py-4 px-4 text-gray-300 font-medium">
                    <span className="font-mono">${position.entry_price.toLocaleString()}</span>
                  </td>

                  {/* 当前价 */}
                  <td className="text-right py-4 px-4">
                    <span className="font-mono text-white font-semibold">
                      ${position.current_price.toLocaleString()}
                    </span>
                  </td>

                  {/* 未实现盈亏 */}
                  <td className="text-right py-4 px-4">
                    <div className="inline-flex flex-col items-end">
                      <span className={`font-bold text-lg ${pnlColor}`}>
                        {isProfit ? '+' : ''}${Math.abs(position.unrealized_pnl).toFixed(2)}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${pnlColor} ${pnlBgColor} border ${pnlBorderColor} mt-1`}>
                        {isProfit ? '↑' : '↓'}
                        {Math.abs(position.unrealized_pnl_pct).toFixed(2)}%
                      </span>
                    </div>
                  </td>

                  {/* 杠杆 */}
                  <td className="text-right py-4 px-4">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-warning/20 text-warning border border-warning/30">
                      {position.leverage}x
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* 底部统计 */}
      <div className="mt-6 pt-4 border-t border-glass-border flex items-center justify-between text-sm">
        <div className="text-gray-400">
          总持仓: <span className="text-white font-semibold">{positions.length}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-gray-400">
            总盈亏:
            <span className={`ml-2 font-bold ${
              positions.reduce((sum, p) => sum + p.unrealized_pnl, 0) >= 0
                ? 'text-success'
                : 'text-danger'
            }`}>
              ${positions.reduce((sum, p) => sum + p.unrealized_pnl, 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
