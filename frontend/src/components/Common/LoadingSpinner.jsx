export default function LoadingSpinner({ size = 'md', text = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div 
        className={`${sizeClasses[size]} rounded-full animate-spin`}
        style={{ 
          borderColor: 'var(--color-aira-border-light)', 
          borderTopColor: 'var(--color-aira-primary)' 
        }}
      />
      {text && (
        <p className="text-sm animate-pulse" style={{ color: 'var(--color-aira-text-dim)' }}>
          {text}
        </p>
      )}
    </div>
  )
}
