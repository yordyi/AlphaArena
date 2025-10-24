'use client';

import { motion } from 'framer-motion';

interface Position {
  symbol: string;
  positionAmt: string;
  entryPrice: string;
  currentPrice: string;
  unRealizedProfit: string;
  profitPct: string;
  leverage: string;
}

interface PositionsTableProps {
  positions: Position[];
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-foreground-muted border-b border-border">
            <th className="pb-3 font-medium">币种</th>
            <th className="pb-3 font-medium">数量</th>
            <th className="pb-3 font-medium">杠杆</th>
            <th className="pb-3 font-medium">入场价格</th>
            <th className="pb-3 font-medium">当前价格</th>
            <th className="pb-3 font-medium">未实现盈亏</th>
            <th className="pb-3 font-medium">盈亏率</th>
          </tr>
        </thead>
        <tbody>
          {positions.length === 0 ? (
            <tr>
              <td colSpan={7} className="pt-8 text-center text-foreground-muted">
                暂无持仓
              </td>
            </tr>
          ) : (
            positions.map((position, index) => {
              const profit = parseFloat(position.unRealizedProfit);
              const profitPct = parseFloat(position.profitPct);
              const isProfit = profit >= 0;

              return (
                <motion.tr
                  key={position.symbol}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="border-b border-border/50 hover:bg-background-hover transition-colors"
                >
                  <td className="py-4 font-medium">{position.symbol}</td>
                  <td className="py-4">
                    {parseFloat(position.positionAmt).toFixed(4)}
                  </td>
                  <td className="py-4">
                    <span className="px-2 py-1 rounded bg-background-card text-accent-blue text-sm">
                      {position.leverage}x
                    </span>
                  </td>
                  <td className="py-4 text-foreground-muted">
                    ${parseFloat(position.entryPrice).toFixed(2)}
                  </td>
                  <td className="py-4">${position.currentPrice}</td>
                  <td
                    className={`py-4 font-medium ${
                      isProfit ? 'text-accent-green' : 'text-accent-red'
                    }`}
                  >
                    {isProfit ? '+' : ''}${profit.toFixed(2)}
                  </td>
                  <td
                    className={`py-4 font-medium ${
                      isProfit ? 'text-accent-green' : 'text-accent-red'
                    }`}
                  >
                    {isProfit ? '+' : ''}{profitPct.toFixed(2)}%
                  </td>
                </motion.tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
