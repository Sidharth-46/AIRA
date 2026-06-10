import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { HiOutlineClipboardCopy, HiCheck } from 'react-icons/hi'

export default function CodeBlock({ language = 'text', children, ...props }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).replace(/\n$/, ''))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ 
      borderRadius: '8px', 
      overflow: 'hidden', 
      border: '1px solid var(--color-aira-border)',
      margin: '12px 0',
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        padding: '8px 16px',
        background: 'var(--color-aira-surface-3)',
        borderBottom: '1px solid var(--color-aira-border)',
      }}>
        <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-aira-text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {language}
        </span>
        <button
          onClick={handleCopy}
          style={{ 
            display: 'flex', alignItems: 'center', gap: '4px',
            fontSize: '12px', color: copied ? '#22C55E' : 'var(--color-aira-text-dim)',
            background: 'transparent', border: 'none', cursor: 'pointer',
            transition: 'color 0.15s ease',
          }}
          onMouseEnter={(e) => { if (!copied) e.currentTarget.style.color = 'var(--color-aira-text)' }}
          onMouseLeave={(e) => { if (!copied) e.currentTarget.style.color = 'var(--color-aira-text-dim)' }}
        >
          {copied ? <HiCheck /> : <HiOutlineClipboardCopy />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      {/* Code */}
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          padding: '16px',
          background: 'var(--color-aira-surface)',
          fontSize: '13px',
          lineHeight: '1.6',
          borderRadius: 0,
        }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    </div>
  )
}
