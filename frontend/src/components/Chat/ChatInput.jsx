import { useState, useRef, useEffect } from 'react'
import { HiOutlineArrowUp, HiStop } from 'react-icons/hi'
import { useChatStore } from '../../stores/chatStore'

export default function ChatInput({ chatId, onSend, isStreaming, onStop }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef(null)
  const debounceRef = useRef(null)

  const { isHydrating } = useChatStore()

  // Load draft on mount or chat change
  useEffect(() => {
    try {
      if (!chatId || chatId === 'new-chat') {
        // Explicit zero-state for new chats
        setInput('')
        
        // Also cleanup any ghost drafts that somehow made it to localStorage
        const drafts = JSON.parse(localStorage.getItem('aira_chat_drafts') || '{}')
        if (drafts['new-chat']) {
          delete drafts['new-chat']
          localStorage.setItem('aira_chat_drafts', JSON.stringify(drafts))
        }
        return
      }

      const drafts = JSON.parse(localStorage.getItem('aira_chat_drafts') || '{}')
      if (drafts[chatId]) {
        setInput(drafts[chatId])
      } else {
        setInput('')
      }
    } catch (e) {
      console.error('Failed to load draft:', e)
      setInput('')
    }
  }, [chatId])

  // Save draft with debounce
  useEffect(() => {
    if (!chatId || chatId === 'new-chat') return

    if (debounceRef.current) clearTimeout(debounceRef.current)
    
    debounceRef.current = setTimeout(() => {
      try {
        const drafts = JSON.parse(localStorage.getItem('aira_chat_drafts') || '{}')
        if (input.trim()) {
          drafts[chatId] = input
        } else {
          delete drafts[chatId]
        }
        localStorage.setItem('aira_chat_drafts', JSON.stringify(drafts))
      } catch (e) {
        console.error('Failed to save draft:', e)
      }
    }, 500)

    return () => clearTimeout(debounceRef.current)
  }, [input, chatId])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`
    }
  }, [input])

  // Focus management
  useEffect(() => {
    const focusInput = () => {
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus()
          // Move cursor to end
          const length = textareaRef.current.value.length
          textareaRef.current.setSelectionRange(length, length)
        }
      }, 10)
    }

    focusInput()
    if (!isStreaming) focusInput()

    const handleGlobalFocus = () => focusInput()
    const handleGlobalKeyDown = (e) => {
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        focusInput()
      }
    }

    window.addEventListener('focus-chat-input', handleGlobalFocus)
    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => {
      window.removeEventListener('focus-chat-input', handleGlobalFocus)
      window.removeEventListener('keydown', handleGlobalKeyDown)
    }
  }, [isStreaming])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    if (input.trim() && !isStreaming) {
      onSend(input.trim())
      setInput('')
    }
  }

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', width: '100%' }}>
      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'flex-end', 
          gap: '8px',
          padding: '12px 16px',
          borderRadius: '16px',
          border: '1px solid var(--color-aira-border)',
          background: 'var(--color-aira-surface-3)',
          transition: 'border-color 0.15s ease',
        }}
        onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-aira-border-light)' }}
        onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-aira-border)' }}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isHydrating ? "Initializing AIRA..." : "Message AIRA..."}
          disabled={isHydrating}
          rows={1}
          style={{
            flex: 1,
            maxHeight: '220px',
            minHeight: '32px',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'none',
            padding: '4px 0',
            fontSize: '15px',
            lineHeight: '1.5',
            color: 'var(--color-aira-text)',
            fontFamily: 'var(--font-sans)',
          }}
        />

        {isStreaming ? (
          <button 
            onClick={onStop}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: '#EF4444',
              border: 'none',
              color: '#FFFFFF',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'opacity 0.15s ease',
            }}
            title="Stop generation"
          >
            <HiStop style={{ fontSize: '16px' }} />
          </button>
        ) : (
          <button 
            onClick={handleSend}
            disabled={!input.trim() || isHydrating}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: input.trim() ? 'var(--color-aira-primary)' : 'var(--color-aira-surface)',
              border: input.trim() ? 'none' : '1px solid var(--color-aira-border)',
              color: input.trim() ? '#FFFFFF' : 'var(--color-aira-text-dim)',
              cursor: input.trim() ? 'pointer' : 'default',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'all 0.15s ease',
            }}
            title="Send message"
          >
            <HiOutlineArrowUp style={{ fontSize: '16px' }} />
          </button>
        )}
      </div>
      <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '12px', color: 'var(--color-aira-text-dim)' }}>
        AIRA can make mistakes. Verify important information.
      </div>
    </div>
  )
}
