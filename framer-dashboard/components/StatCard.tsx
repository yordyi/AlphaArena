'use client';

import { motion } from 'framer-motion';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  delay?: number;
}

export default function StatCard({
  title,
  value,
  change,
  changeType = 'neutral',
  delay = 0,
}: StatCardProps) {
  const changeColor = {
    positive: 'text-accent-green',
    negative: 'text-accent-red',
    neutral: 'text-foreground-muted',
  }[changeType];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="stat-card"
    >
      <p className="text-foreground-muted text-sm mb-2">{title}</p>
      <p className="text-3xl font-bold text-foreground">{value}</p>
      {change && (
        <p className={`${changeColor} text-sm mt-2`}>
          {changeType === 'positive' && '+'}
          {change}
        </p>
      )}
    </motion.div>
  );
}
