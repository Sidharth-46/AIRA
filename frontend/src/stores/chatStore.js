import { create } from 'zustand'
import { chatService } from '../services'
import { useWorkspaceStore } from './workspaceStore'

export const useChatStore = create((set, get) => ({
  chats: [],
  activeChat: null,
  messages: [],
  streams: {}, // { [chatId]: { isStreaming, content, agent, intent, model, abortController } }
  folders: [],

  fetchChats: async () => {
    try {
      const res = await chatService.getChats()
      set({ chats: res.data.chats })
    } catch (err) {
      console.error('Failed to fetch chats:', err)
    }
  },

  createChat: async () => {
    try {
      const res = await chatService.createChat({ title: 'New Chat' })
      const chat = res.data.chat
      set((s) => ({ chats: [chat, ...s.chats], activeChat: chat, messages: [] }))
      return chat
    } catch (err) {
      console.error('Failed to create chat:', err)
      return null
    }
  },

  selectChat: async (chatId) => {
    try {
      localStorage.setItem('aira_active_chat', chatId)
      const res = await chatService.getChat(chatId)
      set({ 
        activeChat: res.data.chat,
        messages: res.data.chat.messages || [] 
      })
      console.log('CHAT_RESTORE', chatId)
    } catch (err) {
      console.error('Failed to load chat:', err)
      set({ activeChat: null, messages: [] })
      localStorage.removeItem('aira_active_chat')
    }
  },

  sendMessage: async (content, navigate) => {
    let { activeChat } = get()

    // Auto-create chat if we are on the root /chat path
    if (!activeChat) {
      activeChat = await get().createChat()
      if (!activeChat) return
      
      // Update the URL to the new chat
      if (navigate) {
        navigate(`/chat/${activeChat.id}`, { replace: true })
      }
    }

    const chatId = activeChat.id

    if (get().streams[chatId]?.isStreaming) return

    // Add user message immediately if this is the active chat
    const userMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    
    if (get().activeChat?.id === chatId) {
      set((s) => ({
        messages: [...s.messages, userMsg],
      }))
    }

    // Initialize stream state for this chat
    set((s) => ({
      streams: {
        ...s.streams,
        [chatId]: {
          isStreaming: true,
          content: '',
          agent: null,
          intent: null,
          model: null,
          abortController: null
        }
      }
    }))

    try {
      const controller = new AbortController()
      set((s) => ({
        streams: {
          ...s.streams,
          [chatId]: { ...s.streams[chatId], abortController: controller }
        }
      }))

      const workspaceState = useWorkspaceStore.getState()
      const workspaceContext = workspaceState.activeProjectId ? {
        projectId: workspaceState.activeProjectId,
        currentFile: workspaceState.activeFile?.path || null
      } : null;

      const response = await chatService.sendMessage(chatId, content, workspaceContext)
      
      // Clear draft for this chat
      try {
        const drafts = JSON.parse(localStorage.getItem('aira_chat_drafts') || '{}')
        if (drafts[chatId]) {
          delete drafts[chatId]
          localStorage.setItem('aira_chat_drafts', JSON.stringify(drafts))
        }
      } catch (e) {
        console.error('Failed to clear draft:', e)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      let currentEventType = 'message'

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
            continue
          }
          if (line.startsWith('data: ')) {
            const rawData = line.slice(6)
            try {
              const data = JSON.parse(rawData)
              // Determine event type from last event line
              if (typeof data === 'string') {
                  const currentStream = get().streams[chatId] || {}
                  
                  if (currentEventType === 'error') {
                      const newContent = (currentStream.content || '') + `\n\n**[Error: ${data}]**`
                      set((s) => ({
                        streams: { ...s.streams, [chatId]: { ...s.streams[chatId], content: newContent } }
                      }))
                  } else if (['planner', 'research', 'coder', 'reviewer'].includes(data) || currentEventType === 'agent_status') {
                    set((s) => ({
                      streams: { ...s.streams, [chatId]: { ...s.streams[chatId], agent: data } }
                    }))
                  } else if (currentEventType === 'task_intent') {
                    set((s) => ({
                      streams: { ...s.streams, [chatId]: { ...s.streams[chatId], intent: data } }
                    }))
                  } else if (currentEventType === 'model_status') {
                    set((s) => ({
                      streams: { ...s.streams, [chatId]: { ...s.streams[chatId], model: data.model, intent: data.intent } }
                    }))
                  } else if (currentEventType === 'title_update') {
                    const { activeChat, chats } = get()
                    if (activeChat && activeChat.id === chatId) {
                        const updatedChat = { ...activeChat, title: data }
                        set({
                            activeChat: updatedChat,
                            chats: chats.map(c => c.id === updatedChat.id ? updatedChat : c)
                        })
                    } else {
                        // Title update for a chat that isn't active
                        set({
                            chats: chats.map(c => c.id === chatId ? { ...c, title: data } : c)
                        })
                    }
                  } else if (currentEventType === 'done' || data === '') {
                    // done event
                    const finalStream = get().streams[chatId] || {}
                    if (finalStream.content && finalStream.isStreaming) {
                      const assistantMsg = {
                        id: 'msg-' + Date.now(),
                        role: 'assistant',
                        content: finalStream.content,
                        agent: finalStream.agent,
                        model: finalStream.model,
                        timestamp: new Date().toISOString(),
                      }
                      
                      // Append to UI messages only if this is the currently active chat
                      if (get().activeChat?.id === chatId) {
                        set((s) => ({
                          messages: [...s.messages, assistantMsg],
                        }))
                      }
                      
                      // Clear stream state
                      set((s) => {
                        const newStreams = { ...s.streams }
                        delete newStreams[chatId]
                        return { streams: newStreams }
                      })
                    }
                  } else {
                    const newContent = (currentStream.content || '') + data
                    set((s) => ({
                      streams: { ...s.streams, [chatId]: { ...s.streams[chatId], content: newContent } }
                    }))
                  }
                }
            } catch {
              // Try as plain text token
              const text = rawData.replace(/^"|"$/g, '')
              if (text && text !== '""') {
                const currentStream = get().streams[chatId] || {}
                const newContent = (currentStream.content || '') + text
                set((s) => ({
                  streams: { ...s.streams, [chatId]: { ...s.streams[chatId], content: newContent } }
                }))
              }
            }
          }
        }
      }

      // Add assistant message if the stream was aborted or broken abruptly
      const finalStream = get().streams[chatId]
      if (finalStream?.isStreaming) {
        if (finalStream.content) {
          const assistantMsg = {
            id: 'msg-' + Date.now(),
            role: 'assistant',
            content: finalStream.content,
            agent: finalStream.agent,
            model: finalStream.model,
            timestamp: new Date().toISOString(),
          }
          if (get().activeChat?.id === chatId) {
            set((s) => ({ messages: [...s.messages, assistantMsg] }))
          }
        }
        
        set((s) => {
          const newStreams = { ...s.streams }
          delete newStreams[chatId]
          return { streams: newStreams }
        })
      }

      // Refresh chat list
      get().fetchChats()
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Send message error:', err)
      }
      set((s) => {
        const newStreams = { ...s.streams }
        delete newStreams[chatId]
        return { streams: newStreams }
      })
    }
  },

  stopGeneration: (chatId) => {
    const stream = get().streams[chatId]
    if (!stream) return

    if (stream.abortController) {
      stream.abortController.abort()
    }
    
    if (stream.content) {
      const msg = {
        id: 'msg-' + Date.now(),
        role: 'assistant',
        content: stream.content + '\n\n*[Generation stopped]*',
        timestamp: new Date().toISOString(),
      }
      
      if (get().activeChat?.id === chatId) {
        set((s) => ({ messages: [...s.messages, msg] }))
      }
    }
    
    set((s) => {
      const newStreams = { ...s.streams }
      delete newStreams[chatId]
      return { streams: newStreams }
    })
  },

  deleteChat: async (chatId) => {
    try {
      await chatService.deleteChat(chatId)
      set((s) => {
        const nextChats = s.chats.filter((c) => c.id !== chatId)
        let active = s.activeChat
        if (s.activeChat?.id === chatId) {
          active = null
          localStorage.removeItem('aira_active_chat')
        }
        return { chats: nextChats, activeChat: active, messages: active ? s.messages : [] }
      })
    } catch (err) {
      console.error('Failed to delete chat:', err)
    }
  },

  updateChat: async (chatId, data) => {
    try {
      await chatService.updateChat(chatId, data)
      set((s) => ({
        chats: s.chats.map((c) => (c.id === chatId ? { ...c, ...data } : c)),
      }))
    } catch (err) {
      console.error('Failed to update chat:', err)
    }
  },
}))
