import { useState, useRef, useEffect, useCallback, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Plus, Mic, Moon, Sun, Monitor, User, Bot, Trash2 } from 'lucide-react'
import './App.css'

// Memoized message bubble — prevents re-rendering finalized messages during streaming
const MessageBubble = memo(({ msg }) => {
  if (msg.role === 'user') {
    return (
      <div className="flex gap-4 justify-end">
        <div className="max-w-[80%] rounded-2xl px-5 py-3 shadow-sm bg-blue-600 text-white rounded-br-none">
          {msg.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center shrink-0 mt-1">
          <User size={16} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-4 justify-start">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
        <Bot size={16} className="text-white" />
      </div>
      <div className="max-w-[80%] rounded-2xl px-5 py-3 shadow-sm bg-white dark:!bg-[#2f2f2f] dark:!text-[#ececf1] border border-gray-100 dark:border-gray-700/50 rounded-bl-none prose dark:prose-invert prose-sm">
        <ReactMarkdown>{msg.content}</ReactMarkdown>
      </div>
    </div>
  )
})

const STORAGE_KEY = 'rag_session_id'
const THEME_KEY = 'rag_theme'
const API_BASE = import.meta.env.VITE_API_URL || ''

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [toolStatus, setToolStatus] = useState('')
  const [isRestoring, setIsRestoring] = useState(true)
  const [theme, setTheme] = useState('dark') // Default to dark
  const [keyboardBottom, setKeyboardBottom] = useState(0)
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)
  const timeoutRef = useRef(null)
  const msgIdRef = useRef(0)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  // Initialize Theme
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_KEY) || 'dark'
    setTheme(savedTheme)
    document.documentElement.classList.toggle('light', savedTheme === 'light')
    document.documentElement.classList.toggle('dark', savedTheme === 'dark')
  }, [])

  // Handle keyboard on mobile
  useEffect(() => {
    if (window.visualViewport) {
      const handleResize = () => {
        const offset = window.innerHeight - window.visualViewport.height
        setKeyboardBottom(offset)
      }
      window.visualViewport.addEventListener('resize', handleResize)
      return () => window.visualViewport.removeEventListener('resize', handleResize)
    }
  }, [])

  // Background wake-up ping to backend
  useEffect(() => {
    fetch(`${API_BASE}/api/health`, { method: 'GET' })
      .catch((e) => console.log('Wake-up ping failed:', e))
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem(THEME_KEY, newTheme)
    document.documentElement.classList.toggle('light', newTheme === 'light')
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  // Restore conversation
  useEffect(() => {
    const restoreConversation = async () => {
      const savedSessionId = localStorage.getItem(STORAGE_KEY)
      if (savedSessionId) {
        try {
          const response = await fetch(`${API_BASE}/api/conversation/${savedSessionId}`)
          if (response.ok) {
            const data = await response.json()
            if (data.messages && data.messages.length > 0) {
              const restoredMessages = data.messages.map(msg => ({
                id: ++msgIdRef.current,
                role: msg.role,
                content: msg.content
              }))
              setMessages(restoredMessages)
              setConversationId(savedSessionId)
            }
          }
        } catch (error) {
          localStorage.removeItem(STORAGE_KEY)
        }
      }
      setIsRestoring(false)
    }
    restoreConversation()
  }, [])

  // Save conversation ID
  useEffect(() => {
    if (conversationId) localStorage.setItem(STORAGE_KEY, conversationId)
  }, [conversationId])

  // Cleanup abort controller
  useEffect(() => {
    return () => abortControllerRef.current?.abort()
  }, [])

  const sendMessageStreaming = useCallback(async (userMessage) => {
    setLoading(true)
    setStreamingMessage('')
    setToolStatus('')
    abortControllerRef.current = new AbortController()

    // 45-second timeout to prevent infinite loading
    timeoutRef.current = setTimeout(() => {
      abortControllerRef.current?.abort()
      setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'error', content: 'Request timed out. Please try again.' }])
      setStreamingMessage('')
      setToolStatus('')
      setLoading(false)
    }, 45000)

    let receivedDone = false

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, session_id: conversationId }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullMessage = ''
      let sseBuffer = '' // Buffer for incomplete SSE lines across chunks

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Prepend any leftover buffer from the previous chunk
        const chunk = sseBuffer + decoder.decode(value, { stream: true })
        sseBuffer = ''

        const lines = chunk.split('\n')

        // The last element might be an incomplete line — save it for the next chunk
        if (!chunk.endsWith('\n')) {
          sseBuffer = lines.pop()
        }

        for (const line of lines) {
          const trimmedLine = line.trim()
          if (trimmedLine.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmedLine.slice(6))
              if (data.token) {
                fullMessage += data.token
                setStreamingMessage(fullMessage)
                setToolStatus('')
              }
              if (data.tool_call) {
                const toolNames = {
                  'search_personal_knowledge': '🔍 Searching knowledge base...',
                  'search_web': '🌐 Searching the web...',
                  'get_github_stats': '🐙 Fetching GitHub stats...',
                  'fallback_search': '🔍 Gathering context...'
                }
                setToolStatus(toolNames[data.tool_call] || `🔧 Using ${data.tool_call}...`)
              }
              if (data.done) {
                receivedDone = true
                if (fullMessage.trim()) {
                  setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'assistant', content: fullMessage.trim() }])
                }
                setStreamingMessage('')
                setToolStatus('')
                if (data.session_id) setConversationId(data.session_id)
              }
              if (data.error) {
                receivedDone = true
                setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'error', content: data.error }])
                setStreamingMessage('')
                setToolStatus('')
              }
            } catch (e) { /* JSON parse error — line was truly malformed */ }
          }
        }
      }

      // GUARD: If stream ended without a done/error event, finalize the message
      if (!receivedDone && fullMessage.trim()) {
        setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'assistant', content: fullMessage.trim() }])
        setStreamingMessage('')
        setToolStatus('')
      }

    } catch (error) {
      if (error.name !== 'AbortError') {
        setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'error', content: 'Sorry, something went wrong. Please try again.' }])
        setStreamingMessage('')
        setToolStatus('')
      }
    } finally {
      clearTimeout(timeoutRef.current)
      setLoading(false)
      abortControllerRef.current = null
    }
  }, [conversationId])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return
    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { id: ++msgIdRef.current, role: 'user', content: userMessage }])
    await sendMessageStreaming(userMessage)
  }

  const clearChat = async () => {
    if (abortControllerRef.current) abortControllerRef.current.abort()
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (conversationId) {
      try { await fetch(`${API_BASE}/api/conversation/${conversationId}`, { method: 'DELETE' }) } catch (e) { }
    }
    localStorage.removeItem(STORAGE_KEY)
    setMessages([])
    setConversationId(null)
    setStreamingMessage('')
    setToolStatus('')
    setLoading(false)
  }

  if (isRestoring) return <div className="min-h-screen bg-dark-bg dark:bg-dark-bg flex items-center justify-center text-gray-500">Loading...</div>

  return (
    <div className={`h-[100dvh] w-full overflow-hidden flex flex-col transition-colors duration-300 relative ${theme === 'light' ? 'bg-light-bg text-light-text' : 'bg-dark-bg text-dark-text'}`}>

      {/* Header */}
      <header className="flex justify-between items-center p-4 max-w-3xl mx-auto w-full z-10">
        <div className="flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity">
          <Monitor size={18} />
          <span className="font-medium text-sm">RAG Assistant</span>
        </div>
        <div className="flex gap-2">
          <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={clearChat} className="p-2 rounded-full hover:bg-red-100 dark:hover:bg-red-900/20 text-red-500 transition-colors" title="Clear Chat">
            <Trash2 size={18} />
          </button>
        </div>
      </header>

      {/* Quick Question Tabs */}
      <div className="flex flex-wrap justify-center gap-2 p-2 max-w-3xl mx-auto w-full">
        <button onClick={() => setInput("Who are you?")} className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm whitespace-nowrap">Introduction</button>
        <button onClick={() => setInput("What are your skills?")} className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm whitespace-nowrap">Skills</button>
        <button onClick={() => setInput("What are your projects?")} className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm whitespace-nowrap">Projects</button>
        <button onClick={() => setInput("Which sports do you play?")} className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm whitespace-nowrap">Sports</button>
        <button onClick={() => setInput("Explain this RAG project.")} className="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors text-sm whitespace-nowrap">About This Project</button>
      </div>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 w-full max-w-3xl mx-auto space-y-6 pb-32">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center opacity-40 mt-20">
            <div className="w-16 h-16 bg-gray-200 dark:bg-gray-800 rounded-2xl flex items-center justify-center mb-4">
              <Bot size={32} />
            </div>
            <p>Welcome to my personal chatbot. You can ask anything. 😊</p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {streamingMessage && (
          <div className="flex gap-4 justify-start animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
              <Bot size={16} className="text-white" />
            </div>
            <div className="max-w-[80%] rounded-2xl rounded-bl-none px-5 py-3 bg-white dark:bg-[#2f2f2f] border border-gray-100 dark:border-gray-700 shadow-sm prose dark:prose-invert prose-sm">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
              <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse"></span>
            </div>
          </div>
        )}

        {loading && !streamingMessage && (
          <div className="flex gap-4 justify-start">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
              <Bot size={16} className="text-white" />
            </div>
            <div className="flex flex-col gap-1">
              {toolStatus && (
                <div className="text-sm text-blue-400 animate-pulse px-4 py-1">
                  {toolStatus}
                </div>
              )}
              <div className="flex gap-1 items-center bg-white dark:bg-[#2f2f2f] px-4 py-3 rounded-2xl rounded-bl-none border border-gray-100 dark:border-gray-700">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white to-transparent dark:from-[#212121] dark:via-[#212121] pb-8" style={{ bottom: `${keyboardBottom}px` }}>
        <div className="max-w-3xl mx-auto">
          <form onSubmit={sendMessage} className="relative flex items-center gap-2 bg-[#f4f4f4] dark:bg-[#2f2f2f] p-2 rounded-full border border-transparent focus-within:border-gray-300 dark:focus-within:border-gray-600 transition-all shadow-lg">


            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything..."
              disabled={loading}
              className="flex-1 bg-transparent outline-none text-base text-gray-800 dark:text-[#ececf1] placeholder-gray-500"
            />


            <button type="submit" disabled={loading} className="p-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-md">
              <Send size={20} />
            </button>

          </form>

        </div>
      </div>
    </div>
  )
}

export default App
