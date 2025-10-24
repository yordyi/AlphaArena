'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { motion } from 'framer-motion';

interface PortfolioData {
  name: string;
  value: number;
  color: string;
}

interface PortfolioChartProps {
  data: PortfolioData[];
}

export default function PortfolioChart({ data }: PortfolioChartProps) {
  const COLORS = ['#00ff88', '#0099ff', '#9945ff', '#ff3366', '#00ffff'];

  const chartData = data.length > 0 ? data : [
    { name: 'USDT', value: 100, color: COLORS[0] },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="h-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || COLORS[index % COLORS.length]}
                stroke="none"
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#141414',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              color: '#ffffff',
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, '价值']}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            wrapperStyle={{
              color: '#a1a1a1',
              fontSize: '12px',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
