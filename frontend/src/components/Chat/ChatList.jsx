import { useEffect, useRef } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'
import { HiOutlineChatAlt2, HiOutlineTrash } from 'react-icons/hi'

export default function ChatList() {
  const { chats, fetchChats, deleteChat, activeChat } = useChatStore()
  const { chatId } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    fetchChats()
  }, [fetchChats])

  const handleDelete = (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    deleteChat(id)
    if (chatId === id || activeChat?.id === id) {
      navigate('/chat')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {(!chats || chats.length === 0) ? (
        <div style={{ textAlign: 'center', padding: '16px', fontSize: '12px', color: 'var(--color-aira-text-dim)' }}>
          No recent chats
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'auto', paddingBottom: '80px' }}>
          {chats.map((chat) => {
            const isActive = chatId === chat.id
            return (
              <Link
                key={chat.id}
                to={`/chat/${chat.id}`}
                className="group"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  height: '36px',
                  padding: '0 12px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  textDecoration: 'none',
                  color: isActive ? 'var(--color-aira-text)' : 'var(--color-aira-text-muted)',
                  background: isActive ? 'var(--color-aira-surface-3)' : 'transparent',
                  transition: 'background 0.1s ease',
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', flex: 1 }}>
                  <HiOutlineChatAlt2 style={{ flexShrink: 0, fontSize: '14px' }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{chat.title || 'New Chat'}</span>
                </div>
                
                <button
                  onClick={(e) => handleDelete(e, chat.id)}
                  className="opacity-0 group-hover:opacity-100"
                  style={{ padding: '4px', background: 'none', border: 'none', color: 'var(--color-aira-text-dim)', cursor: 'pointer', transition: 'opacity 0.1s ease, color 0.1s ease', flexShrink: 0 }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = '#EF4444' }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-aira-text-dim)' }}
                  title="Delete chat"
                >
                  <HiOutlineTrash style={{ fontSize: '14px' }} />
                </button>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
