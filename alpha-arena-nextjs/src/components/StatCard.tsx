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
  const colorClasses = {
    primary: 'text-primary',
    success: 'text-success',
    danger: 'text-danger',
    warning: 'text-warning',
    white: 'text-white',
  }

  const changeColor = change && change >= 0 ? 'text-success' : 'text-danger'
  const changeSymbol = change && change >= 0 ? '↑' : '↓'

  return (
    <div className="stat-card group">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs text-gray-400 font-medium uppercase tracking-wide">
          {icon} {title}
        </h3>
        {change !== undefined && (
          <span className={`text-xs font-bold ${changeColor}`}>
            {changeSymbol} {Math.abs(change)}%
          </span>
        )}
      </div>
      <div className={`text-2xl font-bold ${colorClasses[valueColor]} transition-colors`}>
        {prefix}
        {typeof value === 'number' ? value.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }) : value}
        {suffix}
      </div>
    </div>
  )
}
