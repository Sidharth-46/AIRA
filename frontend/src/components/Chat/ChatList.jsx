import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'
import { HiOutlineChatAlt2, HiOutlineTrash, HiOutlineDotsVertical } from 'react-icons/hi'

const ChatItem = ({ chat, isActive, onDelete }) => {
  const [menuOpen, setMenuOpen] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <>
      <Link
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
          position: 'relative',
        }}
        onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
        onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden', flex: 1 }}>
          <HiOutlineChatAlt2 style={{ flexShrink: 0, fontSize: '14px' }} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{chat.title || 'New Chat'}</span>
        </div>
        
        <div ref={menuRef} className={`opacity-0 ${menuOpen ? 'opacity-100' : 'group-hover:opacity-100'}`} style={{ display: 'flex', alignItems: 'center' }}>
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              setMenuOpen(!menuOpen)
            }}
            style={{ padding: '4px', background: 'none', border: 'none', color: 'var(--color-aira-text-dim)', cursor: 'pointer', transition: 'color 0.1s ease', flexShrink: 0, display: 'flex', alignItems: 'center' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-aira-text)' }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-aira-text-dim)' }}
          >
            <HiOutlineDotsVertical style={{ fontSize: '14px' }} />
          </button>
          
          {menuOpen && (
            <div 
              style={{ 
                position: 'absolute', 
                right: '28px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                zIndex: 50,
                background: 'var(--color-aira-surface)',
                border: '1px solid var(--color-aira-border)',
                borderRadius: '6px',
                padding: '4px',
                minWidth: '120px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
              }}
            >
              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  setMenuOpen(false)
                  setShowConfirm(true)
                }}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '6px 12px',
                  background: 'transparent',
                  border: 'none',
                  color: '#EF4444',
                  fontSize: '13px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
              >
                <HiOutlineTrash /> Delete Chat
              </button>
            </div>
          )}
        </div>
      </Link>

      {showConfirm && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.5)' }}>
          <div style={{ background: 'var(--color-aira-surface)', padding: '24px', borderRadius: '12px', width: '320px', border: '1px solid var(--color-aira-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' }}>
            <h3 style={{ margin: '0 0 8px 0', color: 'var(--color-aira-text)', fontSize: '18px', fontWeight: '500' }}>Delete Chat?</h3>
            <p style={{ margin: '0 0 24px 0', color: 'var(--color-aira-text-dim)', fontSize: '14px' }}>This action cannot be undone.</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button 
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowConfirm(false); }} 
                style={{ padding: '8px 16px', background: 'transparent', border: '1px solid var(--color-aira-border)', color: 'var(--color-aira-text)', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', transition: 'background 0.2s' }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-aira-surface-3)' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
              >
                Cancel
              </button>
              <button 
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowConfirm(false); onDelete(chat.id); }} 
                style={{ padding: '8px 16px', background: '#EF4444', border: 'none', color: '#fff', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', transition: 'background 0.2s' }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#DC2626' }}
                onMouseLeave={(e) => { e.currentTarget.style.background = '#EF4444' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default function ChatList() {
  const { chats, fetchChats, deleteChat, activeChat } = useChatStore()
  const { chatId } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    fetchChats()
  }, [fetchChats])

  const handleDelete = (id) => {
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
          {chats.map((chat) => (
            <ChatItem 
              key={chat.id} 
              chat={chat} 
              isActive={chatId === chat.id} 
              onDelete={handleDelete} 
            />
          ))}
        </div>
      )}
    </div>
  )
}
