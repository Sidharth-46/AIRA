import { useEffect, useRef } from 'react'
import { useThemeStore } from '../../stores/themeStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'

export default function StreamingMessage({ content, agent, intent }) {
  const { theme } = useThemeStore()
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [content])

  const getStatusText = () => {
    if (intent === 'analyze_repo') return 'Analyzing repository...'
    if (intent === 'generate_docs') return 'Processing documents...'
    if (['generate_code', 'refactor', 'debug'].includes(intent)) return 'Generating code...'
    if (agent === 'planner') return 'Planning...'
    if (agent === 'research') return 'Researching...'
    if (agent === 'reviewer') return 'Reviewing...'
    return 'Generating...'
  }

  return (
    <div style={{ display: 'flex', gap: '16px', width: '100%' }}>
      {/* Avatar */}
      <div style={{ flexShrink: 0 }}>
        <img src={theme === 'light' ? '/logo-dark.png' : '/logo.png'} alt="AIRA" style={{ width: '32px', height: '32px', borderRadius: '50%' }} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Role label */}
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-aira-text-muted)', marginBottom: '6px' }}>
          AIRA
          {agent && (
            <span style={{ fontWeight: 400, marginLeft: '8px', color: 'var(--color-aira-text-dim)', textTransform: 'capitalize' }}>
              {agent}
            </span>
          )}
        </div>

        {/* Status */}
        <div className="animate-fade-in" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '13px', color: 'var(--color-aira-text-dim)' }}>
          <div style={{ 
            width: '14px', height: '14px', borderRadius: '50%', 
            border: '2px solid var(--color-aira-border)', 
            borderTopColor: 'var(--color-aira-primary)',
            animation: 'spin 0.8s linear infinite',
          }} />
          {getStatusText()}
        </div>

        {/* Content */}
        {content && (
          <div className="prose prose-invert max-w-none" style={{ fontSize: '15px', lineHeight: '1.7', color: 'var(--color-aira-text)' }}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
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
                },
                p: ({ children }) => (
                  <p>
                    {children}
                  </p>
                )
              }}
            >
              {content}
            </ReactMarkdown>
            <div style={{ marginTop: '4px' }}>
              <span style={{ 
                display: 'inline-block', 
                width: '6px', 
                height: '18px', 
                background: 'var(--color-aira-primary)', 
                animation: 'blink 1s infinite',
              }} />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  )
}
