import { useState, useRef, useEffect } from 'react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { workspaceService } from '../../services'
import {
  HiOutlineLightBulb,
  HiOutlineCode,
  HiOutlineExclamation,
  HiOutlineRefresh,
  HiOutlineBeaker,
  HiOutlineDocumentText,
  HiOutlineChat,
  HiOutlineX,
  HiOutlineChevronRight,
} from 'react-icons/hi'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '../Chat/CodeBlock'

const QUICK_ACTIONS = [
  { id: 'explain', label: 'Explain File', icon: HiOutlineLightBulb, prompt: 'Explain what this file does in detail.' },
  { id: 'fix', label: 'Fix Error', icon: HiOutlineExclamation, prompt: 'Find and fix any bugs or errors in this file.' },
  { id: 'refactor', label: 'Refactor', icon: HiOutlineRefresh, prompt: 'Suggest refactoring improvements for this file.' },
  { id: 'tests', label: 'Generate Tests', icon: HiOutlineBeaker, prompt: 'Generate comprehensive unit tests for this file.' },
  { id: 'docs', label: 'Add Documentation', icon: HiOutlineDocumentText, prompt: 'Add detailed docstrings and comments to this file.' },
  { id: 'ask', label: 'Ask About Project', icon: HiOutlineChat, prompt: '' },
]

export default function CopilotPanel() {
  const {
    activeFile,
    activeProjectName,
    activeProjectId,
    openFiles,
    copilotOpen,
    toggleCopilot,
  } = useWorkspaceStore()

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const messagesEndRef = useRef(null)

  // Fetch chat history when project changes or panel opens
  useEffect(() => {
    if (copilotOpen && activeProjectId) {
      loadHistory()
    }
  }, [copilotOpen, activeProjectId])

  const loadHistory = async () => {
    try {
      const res = await workspaceService.getChat(activeProjectId)
      if (res.data?.chat?.messages) {
        setMessages(res.data.chat.messages)
        setTimeout(scrollToBottom, 100)
      } else {
        setMessages([])
      }
    } catch (err) {
      console.error('Failed to load copilot history', err)
      setMessages([])
    }
  }

  const handleClearChat = async () => {
    if (!activeProjectId) return
    try {
      await workspaceService.clearChat(activeProjectId)
      setMessages([])
    } catch (err) {
      console.error('Failed to clear chat', err)
    }
  }

  if (!copilotOpen) return null

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendMessage = async (content) => {
    if (!content.trim() || loading) return

    // Backend workspaceContextBuilder handles context injection automatically now.
    // We do NOT need to prepend context text manually!
    
    // Just send the user's raw message to the workspace chat.

    setMessages((prev) => [...prev, { role: 'user', content }])
    setInput('')
    setLoading(true)
    setStreamingContent('')

    try {
      if (!activeProjectId) {
        setMessages((prev) => [...prev, { role: 'assistant', content: 'No active project selected.' }])
        setLoading(false)
        return
      }

      const response = await workspaceService.sendMessage(activeProjectId, content, activeFile?.path)
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              if (parsed.event === 'token') {
                accumulated += parsed.data
                setStreamingContent(accumulated)
              } else if (parsed.event === 'done') {
                setMessages((prev) => [...prev, { role: 'assistant', content: accumulated }])
                setStreamingContent('')
                accumulated = ''
              }
            } catch {
              // not JSON, try raw token
              if (data && data !== '[DONE]') {
                accumulated += data
                setStreamingContent(accumulated)
              }
            }
          }
        }
      }

      if (accumulated) {
        setMessages((prev) => [...prev, { role: 'assistant', content: accumulated }])
        setStreamingContent('')
      }
    } catch (err) {
      console.error('Copilot error', err)
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Failed to get response.' }])
    } finally {
      setLoading(false)
      setTimeout(scrollToBottom, 100)
    }
  }

  const handleQuickAction = (action) => {
    if (action.id === 'ask') return // Just focus input
    sendMessage(action.prompt)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const markdownComponents = {
    code({ children, className, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      const codeString = String(children).replace(/\n$/, '')
      if (codeString.includes('\n') || match) {
        return <CodeBlock language={match?.[1] || ''} children={codeString} />
      }
      return <code className="inline-code" {...props}>{children}</code>
    },
  }

  return (
    <div className="copilot-panel flex flex-col h-full bg-aira-surface">
      {/* Header */}
      <div className="copilot-header flex items-center justify-between p-4 border-b border-aira-border">
        <div className="copilot-header-title flex items-center gap-2 font-medium text-aira-text">
          <svg className="w-5 h-5 text-aira-primary" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
          <span>AIRA Copilot</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleClearChat} className="p-1.5 text-aira-text-dim hover:text-aira-text rounded transition-colors" title="Clear Chat">
            <HiOutlineRefresh className="w-4 h-4" />
          </button>
          <button onClick={toggleCopilot} className="p-1.5 text-aira-text-dim hover:text-aira-text rounded transition-colors" title="Close Panel">
            <HiOutlineX className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Context badge */}
      {activeFile && (
        <div className="copilot-context">
          <HiOutlineCode className="w-3.5 h-3.5" />
          <span className="truncate">{activeFile.name}</span>
        </div>
      )}

      {/* Quick actions */}
      {messages.length === 0 && (
        <div className="copilot-actions">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.id}
              className="copilot-action-btn"
              onClick={() => handleQuickAction(action)}
              disabled={loading || (action.id !== 'ask' && !activeFile)}
            >
              <action.icon className="w-4 h-4" />
              <span>{action.label}</span>
              <HiOutlineChevronRight className="w-3 h-3 ml-auto opacity-50" />
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="copilot-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`copilot-message copilot-message-${msg.role}`}>
            {msg.role === 'user' ? (
              <p className="text-sm">{msg.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {msg.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        ))}

        {streamingContent && (
          <div className="copilot-message copilot-message-assistant">
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {streamingContent}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {loading && !streamingContent && (
          <div className="copilot-message copilot-message-assistant">
            <div className="flex items-center gap-2 text-aira-text-dim text-sm">
              <div className="w-4 h-4 border-2 border-aira-border border-t-aira-primary rounded-full animate-spin" />
              Thinking...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-aira-border bg-aira-surface-3">
        <div className="relative flex items-center bg-aira-surface border border-aira-border focus-within:border-aira-primary rounded-lg transition-colors overflow-hidden">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={activeFile ? `Ask about ${activeFile.name}...` : 'Ask AIRA anything...'}
            disabled={loading}
            className="w-full bg-transparent border-none text-aira-text text-sm px-4 py-3 focus:outline-none placeholder-aira-text-dim"
          />
          <button 
            type="submit" 
            disabled={loading || !input.trim()} 
            className={`p-2 mr-2 rounded-md transition-colors ${input.trim() ? 'text-aira-primary hover:bg-aira-primary/10' : 'text-aira-text-dim'}`}
          >
            <HiOutlineChevronRight className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}
