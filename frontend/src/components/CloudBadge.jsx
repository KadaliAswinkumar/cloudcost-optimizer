import { clsx } from 'clsx'

const cloudStyles = {
  aws: {
    bg: 'bg-aws/10',
    border: 'border-aws/30',
    text: 'text-aws',
    icon: '🟠',
    name: 'AWS',
    fullName: 'Amazon Web Services',
  },
  gcp: {
    bg: 'bg-gcp/10',
    border: 'border-gcp/30',
    text: 'text-gcp',
    icon: '🔵',
    name: 'GCP',
    fullName: 'Google Cloud Platform',
  },
  azure: {
    bg: 'bg-azure/10',
    border: 'border-azure/30',
    text: 'text-azure',
    icon: '🔷',
    name: 'Azure',
    fullName: 'Microsoft Azure',
  },
}

export default function CloudBadge({ provider, size = 'md', showIcon = true }) {
  const style = cloudStyles[provider] || cloudStyles.aws
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium rounded-lg border',
        style.bg,
        style.border,
        style.text,
        sizeClasses[size]
      )}
    >
      {showIcon && <span>{style.icon}</span>}
      {style.name}
    </span>
  )
}

