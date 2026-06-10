import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'
import { useThemeStore } from '../../stores/themeStore'

export default function MessageBubble({ message, isLast, onRegenerate }) {
  const { theme } = useThemeStore()
  const isUser = message.role === 'user'

  return (
    <div style={{ display: 'flex', gap: '16px', width: '100%', flexDirection: isUser ? 'row-reverse' : 'row' }}>
      
      {/* Avatar */}
      <div style={{ flexShrink: 0 }}>
        {isUser ? (
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '13px',
            fontWeight: 600,
            background: 'var(--color-aira-surface-3)',
            color: '#FFFFFF',
            border: '1px solid var(--color-aira-border)',
          }}>
            U
          </div>
        ) : (
          <img src={theme === 'light' ? '/logo-dark.png' : '/logo.png'} alt="AIRA" style={{ width: '32px', height: '32px', borderRadius: '50%' }} />
        )}
      </div>

      {/* Content */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        maxWidth: isUser ? '80%' : '100%',
        alignItems: isUser ? 'flex-end' : 'flex-start',
      }}>
        {/* Role label */}
        <div style={{ 
          fontSize: '13px', 
          fontWeight: 600, 
          color: 'var(--color-aira-text-muted)', 
          marginBottom: '6px' 
        }}>
          {isUser ? 'You' : 'AIRA'}
          {message.agent && !isUser && (
            <span style={{ fontWeight: 400, marginLeft: '8px', color: 'var(--color-aira-text-dim)', textTransform: 'capitalize' }}>
              {message.agent}
            </span>
          )}
        </div>

        <div style={{
          padding: isUser ? '14px' : '0',
          borderRadius: '16px',
          background: isUser ? 'var(--color-aira-surface-3)' : 'transparent',
          border: isUser ? '1px solid var(--color-aira-border)' : 'none',
          color: 'var(--color-aira-text)',
        }}>
          <div className="prose prose-invert max-w-none" style={{ fontSize: '15px', lineHeight: '1.7' }}>
            {isUser ? (
              <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    // In react-markdown v9+, we check for a match or newlines to determine if it's a block
                    const isBlock = match || String(children).includes('\n')
                    if (isBlock) {
                      return (
                        <CodeBlock
                          language={match ? match[1] : 'text'}
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </CodeBlock>
                      )
                    }
                    return (
                      <code style={{ 
                        background: 'var(--color-aira-surface-3)', 
                        padding: '2px 6px', 
                        borderRadius: '4px', 
                        fontSize: '0.85em', 
                        color: 'var(--color-aira-accent-2)',
                        fontFamily: 'var(--font-mono)'
                      }} className={className} {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
