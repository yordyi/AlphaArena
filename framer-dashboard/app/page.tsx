'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import PortfolioChart from '@/components/PortfolioChart';
import PLChart from '@/components/PLChart';
import PositionsTable from '@/components/PositionsTable';

interface AccountData {
  account: {
    totalWalletBalance: string;
    totalUnrealizedProfit: string;
    totalMarginBalance: string;
    availableBalance: string;
  };
  balances: Array<{
    asset: string;
    free: string;
    locked: string;
  }>;
  positions: Array<any>;
}

export default function Home() {
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch account data
  const fetchAccountData = async () => {
    try {
      const response = await fetch('/api/binance/account');
      if (!response.ok) {
        throw new Error('Failed to fetch account data');
      }
      const data = await response.json();
      setAccountData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      console.error('Error fetching account data:', err);
    }
  };

  // Fetch positions
  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/binance/positions');
      if (!response.ok) {
        throw new Error('Failed to fetch positions');
      }
      const data = await response.json();
      setPositions(data.positions || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      console.error('Error fetching positions:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch and polling
  useEffect(() => {
    const fetchData = async () => {
      await Promise.all([fetchAccountData(), fetchPositions()]);
    };

    fetchData();

    // Poll every 10 seconds
    const interval = setInterval(fetchData, 10000);

    return () => clearInterval(interval);
  }, []);

  // Calculate stats
  const totalBalance = accountData
    ? parseFloat(accountData.account.totalWalletBalance)
    : 0;
  const unrealizedPnL = accountData
    ? parseFloat(accountData.account.totalUnrealizedProfit)
    : 0;
  const pnlPct = totalBalance > 0 ? (unrealizedPnL / totalBalance) * 100 : 0;

  // Prepare portfolio chart data
  const portfolioData = accountData
    ? accountData.balances.map((balance, index) => ({
        name: balance.asset,
        value: parseFloat(balance.free),
        color: ['#00ff88', '#0099ff', '#9945ff', '#ff3366', '#00ffff'][
          index % 5
        ],
      }))
    : [];

  // Mock P&L curve data (will be replaced with real data from performance tracker)
  const plData = [
    { time: '00:00', value: totalBalance * 0.98 },
    { time: '04:00', value: totalBalance * 0.99 },
    { time: '08:00', value: totalBalance * 0.97 },
    { time: '12:00', value: totalBalance * 1.01 },
    { time: '16:00', value: totalBalance * 1.02 },
    { time: '20:00', value: totalBalance },
  ];

  if (error && !accountData) {
    return (
      <main className="min-h-screen p-8 flex items-center justify-center">
        <div className="glass-hover rounded-2xl p-8 max-w-md text-center">
          <h2 className="text-2xl font-bold text-accent-red mb-4">连接错误</h2>
          <p className="text-foreground-muted mb-4">{error}</p>
          <p className="text-sm text-foreground-subtle">
            请检查 .env.local 配置并确保 Binance API 密钥正确
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8 flex justify-between items-center"
      >
        <div>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-accent-green to-accent-blue bg-clip-text text-transparent">
            Alpha Arena
          </h1>
          <p className="text-foreground-muted">AI-Powered Trading Dashboard</p>
        </div>
        {loading && (
          <div className="text-foreground-muted text-sm">加载中...</div>
        )}
      </motion.div>

      {/* Account Overview Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">账户概览</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="账户价值"
            value={`$${totalBalance.toFixed(2)}`}
            change={`${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`}
            changeType={pnlPct >= 0 ? 'positive' : 'negative'}
            delay={0}
          />
          <StatCard
            title="未实现盈亏"
            value={`$${unrealizedPnL.toFixed(2)}`}
            change={`${unrealizedPnL >= 0 ? '+' : ''}${Math.abs(unrealizedPnL).toFixed(2)}`}
            changeType={unrealizedPnL >= 0 ? 'positive' : 'negative'}
            delay={0.05}
          />
          <StatCard
            title="持仓数量"
            value={positions.length.toString()}
            change="个仓位"
            changeType="neutral"
            delay={0.1}
          />
          <StatCard
            title="可用余额"
            value={`$${accountData ? parseFloat(accountData.account.availableBalance).toFixed(2) : '0.00'}`}
            delay={0.15}
          />
        </div>
      </div>

      {/* Charts Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
      >
        {/* Portfolio Allocation */}
        <div className="glass-hover rounded-2xl p-6">
          <h3 className="text-xl font-semibold mb-4">资产分配</h3>
          <div className="h-64">
            <PortfolioChart data={portfolioData} />
          </div>
        </div>

        {/* P&L Curve */}
        <div className="glass-hover rounded-2xl p-6">
          <h3 className="text-xl font-semibold mb-4">盈亏曲线</h3>
          <div className="h-64">
            <PLChart data={plData} />
          </div>
        </div>
      </motion.div>

      {/* Positions Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="glass-hover rounded-2xl p-6"
      >
        <h3 className="text-xl font-semibold mb-4">当前持仓</h3>
        <PositionsTable positions={positions} />
      </motion.div>
    </main>
  );
}
