'use client'

import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import type { ChartDataPoint } from '@/lib/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface PerformanceChartProps {
  data: ChartDataPoint[]
  title?: string
}

export function PerformanceChart({ data, title = '账户价值曲线' }: PerformanceChartProps) {
  // Web3 霓虹渐变颜色
  const createGradient = (ctx: CanvasRenderingContext2D, chartArea: any) => {
    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top)
    gradient.addColorStop(0, 'rgba(6, 182, 212, 0)')
    gradient.addColorStop(0.5, 'rgba(6, 182, 212, 0.15)')
    gradient.addColorStop(1, 'rgba(139, 92, 246, 0.3)')
    return gradient
  }

  const chartData = {
    labels: data.map(d => d.time),
    datasets: [
      {
        label: '账户价值',
        data: data.map(d => d.value),
        // 霓虹蓝紫渐变线条
        borderColor: function(context: any) {
          const chart = context.chart
          const {ctx, chartArea} = chart
          if (!chartArea) return '#06B6D4'

          const gradient = ctx.createLinearGradient(chartArea.left, 0, chartArea.right, 0)
          gradient.addColorStop(0, '#06B6D4')    // Cyan
          gradient.addColorStop(0.5, '#8B5CF6')  // Purple
          gradient.addColorStop(1, '#EC4899')    // Pink
          return gradient
        },
        // 背景渐变填充
        backgroundColor: function(context: any) {
          const chart = context.chart
          const {ctx, chartArea} = chart
          if (!chartArea) return 'rgba(6, 182, 212, 0.1)'
          return createGradient(ctx, chartArea)
        },
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#06B6D4',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 3,
        // 光晕效果
        shadowColor: 'rgba(6, 182, 212, 0.5)',
        shadowBlur: 15,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 750,
      easing: 'easeInOutQuart' as const,
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#fff',
        titleFont: {
          size: 13,
          weight: '600' as const,
        },
        bodyColor: '#06B6D4',
        bodyFont: {
          size: 16,
          weight: 'bold' as const,
        },
        borderColor: 'rgba(6, 182, 212, 0.5)',
        borderWidth: 2,
        padding: 16,
        displayColors: false,
        cornerRadius: 8,
        callbacks: {
          label: function(context: any) {
            return `$${context.parsed.y.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}`
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false,
          lineWidth: 1,
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          font: {
            size: 11,
            weight: '500' as const,
          },
          maxRotation: 0,
          autoSkipPadding: 20,
        },
      },
      y: {
        display: true,
        position: 'right' as const,
        grid: {
          color: 'rgba(148, 163, 184, 0.06)',
          drawBorder: false,
          lineWidth: 1,
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          font: {
            size: 11,
            weight: '500' as const,
          },
          callback: function(value: any) {
            return '$' + value.toLocaleString()
          }
        },
      },
    },
  }

  return (
    <div className="glass-card-hover p-6 group">
      {/* 顶部标题和装饰 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg group-hover:shadow-glow-cyan transition-all duration-300">
            <span className="text-2xl">📈</span>
          </div>
          <h2 className="text-xl font-bold text-gradient-cyan">{title}</h2>
        </div>
        {/* 实时指示器 */}
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
          <span>实时</span>
        </div>
      </div>

      {/* 图表容器 */}
      <div className="h-[320px] relative">
        {/* 背景渐变光晕 */}
        <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative z-10">
          <Line data={chartData} options={options} />
        </div>
      </div>

      {/* 底部装饰线 */}
      <div className="mt-4 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
    </div>
  )
}
