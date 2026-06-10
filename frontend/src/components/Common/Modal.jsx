import { useEffect } from 'react'
import { HiX } from 'react-icons/hi'

export default function Modal({ isOpen, onClose, title, children, maxWidth = 'md' }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div 
        className={`relative w-full ${maxWidthClasses[maxWidth]} glass shadow-2xl rounded-2xl flex flex-col animate-slide-up`}
        style={{ 
          maxHeight: 'calc(100vh - 2rem)',
          border: '1px solid var(--color-aira-border-light)',
          background: 'var(--color-aira-surface)'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'var(--color-aira-border)' }}>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--color-aira-text)' }}>
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-white/5 transition-colors"
            style={{ color: 'var(--color-aira-text-dim)' }}
          >
            <HiX className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  )
}
