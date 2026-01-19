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

export function CloudLogo({ provider, size = 32 }) {
  const logos = {
    aws: (
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
        <rect width="40" height="40" rx="8" fill="#FF9900" fillOpacity="0.1"/>
        <path d="M13.5 20.5c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5" stroke="#FF9900" strokeWidth="2" strokeLinecap="round"/>
        <path d="M22.5 20.5c0-2.5 2-4.5 4.5-4.5" stroke="#FF9900" strokeWidth="2" strokeLinecap="round"/>
        <path d="M10 24h20" stroke="#FF9900" strokeWidth="2" strokeLinecap="round"/>
      </svg>
    ),
    gcp: (
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
        <rect width="40" height="40" rx="8" fill="#4285F4" fillOpacity="0.1"/>
        <circle cx="20" cy="20" r="8" stroke="#4285F4" strokeWidth="2"/>
        <path d="M20 12v-2M20 30v-2M28 20h2M10 20h2" stroke="#4285F4" strokeWidth="2" strokeLinecap="round"/>
      </svg>
    ),
    azure: (
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
        <rect width="40" height="40" rx="8" fill="#0078D4" fillOpacity="0.1"/>
        <path d="M12 28l8-16 4 8-8 8h-4z" fill="#0078D4" fillOpacity="0.5"/>
        <path d="M20 12l8 16h-12l4-8z" stroke="#0078D4" strokeWidth="2"/>
      </svg>
    ),
  }

  return logos[provider] || logos.aws
}

