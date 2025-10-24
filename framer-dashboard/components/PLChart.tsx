'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { motion } from 'framer-motion';

interface PLData {
  time: string;
  value: number;
}

interface PLChartProps {
  data: PLData[];
}

export default function PLChart({ data }: PLChartProps) {
  const chartData = data.length > 0 ? data : [
    { time: '00:00', value: 0 },
    { time: '04:00', value: 0 },
    { time: '08:00', value: 0 },
    { time: '12:00', value: 0 },
    { time: '16:00', value: 0 },
    { time: '20:00', value: 0 },
  ];

  // Determine if overall trend is positive or negative
  const isPositive = chartData.length > 1
    ? chartData[chartData.length - 1].value >= chartData[0].value
    : true;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="h-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorPL" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={isPositive ? '#00ff88' : '#ff3366'}
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor={isPositive ? '#00ff88' : '#ff3366'}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis
            dataKey="time"
            stroke="#6b6b6b"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#6b6b6b"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#141414',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              color: '#ffffff',
            }}
            labelStyle={{ color: '#a1a1a1' }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, '盈亏']}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={isPositive ? '#00ff88' : '#ff3366'}
            strokeWidth={2}
            fill="url(#colorPL)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
