import { useEffect, useRef, Component } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'
import MessageBubble from '../components/Chat/MessageBubble'
import StreamingMessage from '../components/Chat/StreamingMessage'
import ChatInput from '../components/Chat/ChatInput'

class ChatErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("CHAT_RENDER_ERROR", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '32px', color: 'red', background: '#222', minHeight: '100vh' }}>
          <h2>Something went wrong in Chat.</h2>
          <pre style={{ fontSize: '12px', marginTop: '16px' }}>{this.state.error?.toString()}</pre>
          <button 
            onClick={() => {
              localStorage.removeItem('aira_active_chat');
              localStorage.removeItem('aira_chat_drafts');
              localStorage.removeItem('aira_workspace_state');
              localStorage.removeItem('aira_sidebar_collapsed');
              window.location.reload();
            }}
            style={{ marginTop: '16px', padding: '8px 16px', background: 'red', color: 'white', borderRadius: '4px' }}
          >
            Clear LocalStorage & Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

console.log("CHAT_PAGE_MOUNT")

function ChatContent() {
  const { chatId } = useParams()
  const navigate = useNavigate()
  
  const { messages, streams, sendMessage, stopGeneration, selectChat, activeChat, clearActiveChat } = useChatStore()
  
  const streamState = chatId ? streams[chatId] : null
  const isStreaming = !!streamState?.isStreaming
  const streamingContent = streamState?.content || ''
  const streamingAgent = streamState?.agent || null
  const streamingIntent = streamState?.intent || null
  const streamingModel = streamState?.model || null
  
  const messagesEndRef = useRef(null)

  console.log("CHAT_PAGE_RENDER", { chatId, messagesCount: messages?.length || 0 })

  useEffect(() => {
    if (chatId) {
      if (activeChat?.id !== chatId) {
        selectChat(chatId)
      }
    } else {
      const active = localStorage.getItem('aira_active_chat')
      if (active) {
        console.log('CHAT_LOAD (from refresh recovery)')
        navigate(`/chat/${active}`, { replace: true })
      } else {
        const { isCreatingChat } = useChatStore.getState()
        if (clearActiveChat && !isCreatingChat) {
          clearActiveChat()
        }
      }
    }
  }, [chatId, selectChat, navigate, activeChat?.id, clearActiveChat])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="flex flex-col h-full relative" style={{ background: 'var(--color-aira-bg)' }}>
      {/* Header / Model Indicator */}
      {isStreaming && streamingModel && (
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10,
          background: 'var(--color-aira-border)',
          padding: '4px 12px',
          borderRadius: '16px',
          fontSize: '12px',
          color: 'var(--color-aira-text-dim)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
        }} className="animate-fade-in">
          <span style={{ 
            width: '6px', height: '6px', borderRadius: '50%', 
            background: 'var(--color-aira-primary)' 
          }} />
          {streamingModel}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 32px 16px' }}>
          
          {messages.length === 0 && !isStreaming ? (
            <div className="flex flex-col items-center justify-center text-center animate-fade-in" style={{ minHeight: '60vh' }}>
              <h1 style={{ fontSize: '36px', fontWeight: 700, color: 'var(--color-aira-text)', marginBottom: '8px' }}>
                How can I help you?
              </h1>
              <p style={{ fontSize: '15px', color: 'var(--color-aira-text-dim)', maxWidth: '400px', lineHeight: '1.6' }}>
                AIRA is your autonomous software engineering agent. Ask me anything about code, architecture, or development.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {messages.map((msg, idx) => (
                <MessageBubble 
                  key={msg.id || idx} 
                  message={msg} 
                  isLast={idx === messages.length - 1} 
                />
              ))}

              {isStreaming && (
                <StreamingMessage content={streamingContent} agent={streamingAgent} intent={streamingIntent} />
              )}
            </div>
          )}
          
          <div ref={messagesEndRef} style={{ height: '16px' }} />
        </div>
      </div>

      {/* Input */}
      <div style={{ padding: '16px 32px 24px' }}>
        <ChatInput 
          key={chatId || 'new-chat'}
          chatId={chatId || 'new-chat'}
          onSend={(content) => sendMessage(content, navigate)} 
          isStreaming={isStreaming} 
          onStop={() => stopGeneration(chatId)} 
        />
      </div>
    </div>
  )
}

export default function Chat() {
  return (
    <ChatErrorBoundary>
      <ChatContent />
    </ChatErrorBoundary>
  )
}
