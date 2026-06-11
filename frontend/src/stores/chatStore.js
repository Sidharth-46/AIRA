import { create } from 'zustand'
import { chatService } from '../services'
import { useWorkspaceStore } from './workspaceStore'

export const useChatStore = create((set, get) => ({
  chats: [],
  activeChat: null,
  messages: [],
  streams: {}, // { [chatId]: { isStreaming, content, agent, intent, model, abortController } }
  folders: [],
  isHydrating: true,
  isCreatingChat: false,

  clearActiveChat: () => {
    set({ activeChat: null, messages: [] })
  },

  fetchChats: async () => {
    try {
      const res = await chatService.getChats()
      set({ chats: res.data.chats })
    } catch (err) {
      console.error('Failed to fetch chats:', err)
    }
  },

  initHydration: async () => {
    try {
      console.log('HYDRATION_START: Loading chats')
      await get().fetchChats()
      const activeChatId = localStorage.getItem('aira_active_chat')
      if (activeChatId) {
        console.log('HYDRATION_RESTORE_ACTIVE: ', activeChatId)
        await get().selectChat(activeChatId)
      }
      console.log('HYDRATION_COMPLETE: Chats loaded')
    } catch (err) {
      console.error('HYDRATION_ERROR: ', err)
    } finally {
      set({ isHydrating: false })
    }
  },

  cleanupStream: (chatId) => {
    set((s) => {
      const newStreams = { ...s.streams }
      delete newStreams[chatId]
      return { streams: newStreams }
    })
    console.log(`STREAM_CLEANUP: ${chatId}`)
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
    if (get().isHydrating) return

    let { activeChat } = get()

    // Auto-create chat if we are on the root /chat path
    if (!activeChat || activeChat.id === 'new-chat') {
      console.log('NEW_CHAT_CREATED')
      set({ isCreatingChat: true })
      activeChat = await get().createChat()
      if (!activeChat) {
        console.error('SEND_MESSAGE_FAILURE: Failed to create active chat')
        set({ isCreatingChat: false })
        return
      }
      
      // Navigate *before* sending so Chat component doesn't remount mid-stream
      if (navigate) {
        navigate(`/chat/${activeChat.id}`, { replace: true })
      }
      set({ isCreatingChat: false })
    }

    const chatId = activeChat.id

    if (!chatId || chatId === 'new-chat') {
      throw new Error('No active chat ID exists for sending message')
    }

    if (get().streams[chatId]?.isStreaming) return

    console.log(`SEND_MESSAGE_START: chatId=${chatId}, length=${content.length}`)

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

    let fallbackTimeout = null
    const controller = new AbortController()

    try {
      set((s) => ({
        streams: {
          ...s.streams,
          [chatId]: { ...s.streams[chatId], abortController: controller }
        }
      }))

      console.log(`STREAM_STARTED: ${chatId}`)

      // Emergency Fallback: If no token in 5s, abort and show error
      fallbackTimeout = setTimeout(() => {
        console.warn(`STREAM_TIMEOUT: No stream data received for ${chatId} within 5000ms. Aborting.`)
        controller.abort()
        
        const errorMsg = {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: '**[Error: Response failed to start. Please retry.]**',
          timestamp: new Date().toISOString(),
        }
        
        if (get().activeChat?.id === chatId) {
          set((s) => ({ messages: [...s.messages, errorMsg] }))
        }
        
        get().cleanupStream(chatId)
      }, 5000)

      // const workspaceState = useWorkspaceStore.getState()
      // const workspaceContext = workspaceState.activeProjectId ? {
      //   projectId: workspaceState.activeProjectId,
      //   currentFile: workspaceState.activeFile?.path || null
      // } : null;
      
      const workspaceContext = null;

      console.log('CHAT_REQUEST_VALIDATED')
      const response = await chatService.sendMessage(chatId, content, workspaceContext)
      
      // Clear draft for this chat securely
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
        
        // Clear emergency timeout as soon as we get the first chunk
        if (fallbackTimeout) {
          clearTimeout(fallbackTimeout)
          fallbackTimeout = null
          console.log('CHAT_RESPONSE_STARTED')
        }

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
                      
                      if (get().activeChat?.id === chatId) {
                        set((s) => ({
                          messages: [...s.messages, assistantMsg],
                        }))
                      }
                      set((s) => ({
                        streams: { ...s.streams, [chatId]: { ...s.streams[chatId], isStreaming: false } }
                      }))
                      console.log(`STREAM_COMPLETED: ${chatId}`)
                      console.log(`CHAT_RESPONSE_COMPLETED: length=${finalStream.content.length}`)
                    }
                  } else {
                    const newContent = (currentStream.content || '') + data
                    set((s) => ({
                      streams: { ...s.streams, [chatId]: { ...s.streams[chatId], content: newContent } }
                    }))
                    console.log('STREAM_TOKEN_RECEIVED')
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

      // Refresh chat list
      get().fetchChats()
      console.log('SEND_MESSAGE_SUCCESS')
    } catch (err) {
      if (fallbackTimeout) clearTimeout(fallbackTimeout)
      if (err.name === 'AbortError') {
        console.log(`STREAM_ABORTED: ${chatId}`)
      } else {
        console.error(`STREAM_ERROR: ${chatId}`, err)
        console.error('SEND_MESSAGE_FAILURE')
      }
    } finally {
      if (fallbackTimeout) clearTimeout(fallbackTimeout)
      
      // Fallback commit: If stream ended abruptly without 'done' event but has content
      const finalStream = get().streams[chatId]
      if (finalStream && finalStream.content && finalStream.isStreaming) {
        const assistantMsg = {
          id: 'msg-' + Date.now(),
          role: 'assistant',
          content: finalStream.content,
          agent: finalStream.agent,
          model: finalStream.model,
          timestamp: new Date().toISOString(),
        }
        if (get().activeChat?.id === chatId) {
          set((s) => ({
            messages: [...s.messages, assistantMsg],
          }))
        }
      }
      
      get().cleanupStream(chatId)
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
    
    get().cleanupStream(chatId)
    console.log(`STREAM_ABORTED: ${chatId}`)
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
