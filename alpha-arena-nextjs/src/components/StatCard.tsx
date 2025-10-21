'use client'

import { useState, useEffect } from 'react'

interface StatCardProps {
  icon: string
  title: string
  value: string | number
  change?: number
  prefix?: string
  suffix?: string
  valueColor?: 'primary' | 'success' | 'danger' | 'warning' | 'white'
}

export function StatCard({
  icon,
  title,
  value,
  change,
  prefix = '',
  suffix = '',
  valueColor = 'white',
}: StatCardProps) {
  const [prevValue, setPrevValue] = useState(value)
  const [flash, setFlash] = useState<'green' | 'red' | null>(null)

  // 数字变化闪烁效果
  useEffect(() => {
    if (typeof value === 'number' && typeof prevValue === 'number' && value !== prevValue) {
      setFlash(value > prevValue ? 'green' : 'red')
      const timer = setTimeout(() => setFlash(null), 500)
      setPrevValue(value)
      return () => clearTimeout(timer)
    }
  }, [value, prevValue])

  // 颜色配置 - Web3霓虹风格
  const colorClasses = {
    primary: 'text-primary-light',
    success: 'text-success',
    danger: 'text-danger',
    warning: 'text-warning',
    white: 'text-white',
  }

  const glowClasses = {
    primary: 'group-hover:shadow-glow-cyan',
    success: 'group-hover:shadow-glow-green',
    danger: 'group-hover:shadow-glow-pink',
    warning: 'group-hover:shadow-glow-cyan',
    white: 'group-hover:shadow-glow-cyan',
  }

  const borderGlowClasses = {
    primary: 'group-hover:border-primary/50',
    success: 'group-hover:border-success/50',
    danger: 'group-hover:border-danger/50',
    warning: 'group-hover:border-warning/50',
    white: 'group-hover:border-primary/50',
  }

  const changeColor = change && change >= 0 ? 'text-success' : 'text-danger'
  const changeSymbol = change && change >= 0 ? '↑' : '↓'
  const changeBgColor = change && change >= 0 ? 'bg-success/10' : 'bg-danger/10'
  const changeBorderColor = change && change >= 0 ? 'border-success/30' : 'border-danger/30'

  // 为不同颜色生成背景渐变
  const getBackgroundGradient = () => {
    const gradients = {
      primary: 'bg-gradient-to-br from-primary/5 to-transparent',
      success: 'bg-gradient-to-br from-success/5 to-transparent',
      danger: 'bg-gradient-to-br from-danger/5 to-transparent',
      warning: 'bg-gradient-to-br from-warning/5 to-transparent',
      white: 'bg-gradient-to-br from-primary/5 to-transparent',
    }
    return gradients[valueColor]
  }

  // 顶部光条渐变
  const getTopBarGradient = () => {
    const gradients = {
      primary: 'bg-gradient-to-r from-transparent via-primary to-transparent',
      success: 'bg-gradient-to-r from-transparent via-success to-transparent',
      danger: 'bg-gradient-to-r from-transparent via-danger to-transparent',
      warning: 'bg-gradient-to-r from-transparent via-warning to-transparent',
      white: 'bg-gradient-to-r from-transparent via-primary to-transparent',
    }
    return gradients[valueColor]
  }

  // 装饰光点颜色
  const getGlowBg = () => {
    const glows = {
      primary: 'bg-primary',
      success: 'bg-success',
      danger: 'bg-danger',
      warning: 'bg-warning',
      white: 'bg-primary',
    }
    return glows[valueColor]
  }

  return (
    <div className={`
      stat-card group relative overflow-hidden
      border-2 transition-all duration-500
      ${borderGlowClasses[valueColor]}
      ${glowClasses[valueColor]}
    `}>
      {/* 背景渐变效果 */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className={`absolute inset-0 ${getBackgroundGradient()}`} />
      </div>

      {/* 顶部光条 */}
      <div className={`
        absolute top-0 left-0 right-0 h-[2px]
        ${getTopBarGradient()}
        opacity-0 group-hover:opacity-100 transition-opacity duration-300
      `} />

      {/* 内容 */}
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl group-hover:scale-110 transition-transform duration-300 drop-shadow-lg">
              {icon}
            </span>
            <h3 className="text-xs text-gray-400 font-semibold uppercase tracking-wider group-hover:text-gray-300 transition-colors">
              {title}
            </h3>
          </div>
          {change !== undefined && (
            <span className={`
              text-xs font-bold px-2 py-1 rounded-full
              ${changeColor} ${changeBgColor}
              border ${changeBorderColor}
              transition-all duration-300
              group-hover:scale-110
            `}>
              {changeSymbol} {Math.abs(change).toFixed(2)}%
            </span>
          )}
        </div>

        {/* 数值显示 */}
        <div className={`
          text-3xl font-bold tracking-tight
          ${colorClasses[valueColor]}
          number-highlight
          ${flash === 'green' ? 'flash-green' : ''}
          ${flash === 'red' ? 'flash-red' : ''}
          transition-all duration-300
          group-hover:text-shadow
        `}>
          <span className="inline-block group-hover:scale-105 transition-transform duration-300">
            {prefix}
            {typeof value === 'number' ? value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) : value}
            {suffix}
          </span>
        </div>
      </div>

      {/* 右下角装饰光点 */}
      <div className={`
        absolute -right-4 -bottom-4 w-24 h-24 rounded-full
        ${getGlowBg()} opacity-0 group-hover:opacity-10
        blur-2xl transition-opacity duration-500
      `} />
    </div>
  )
}
