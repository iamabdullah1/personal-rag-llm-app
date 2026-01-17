import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

const STORAGE_KEY = 'rag_session_id'
// Use environment variable for API URL in production, empty string for local (uses proxy)
const API_BASE = import.meta.env.VITE_API_URL || ''

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [isRestoring, setIsRestoring] = useState(true)
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  // Restore conversation on page load
  useEffect(() => {
    const restoreConversation = async () => {
      const savedSessionId = localStorage.getItem(STORAGE_KEY)
      
      if (savedSessionId) {
        try {
          const response = await fetch(`${API_BASE}/api/conversation/${savedSessionId}`)
          if (response.ok) {
            const data = await response.json()
            if (data.messages && data.messages.length > 0) {
              // Convert backend format to frontend format
              const restoredMessages = data.messages.map(msg => ({
                role: msg.role,
                content: msg.content
              }))
              setMessages(restoredMessages)
              setConversationId(savedSessionId)
              console.log(`✅ Restored ${data.message_count} messages from session ${savedSessionId}`)
            }
          }
        } catch (error) {
          console.log('No previous conversation found:', error)
          localStorage.removeItem(STORAGE_KEY)
        }
      }
      setIsRestoring(false)
    }
    
    restoreConversation()
  }, [])

  // Save session_id to localStorage whenever it changes
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(STORAGE_KEY, conversationId)
    }
  }, [conversationId])

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const sendMessageStreaming = useCallback(async (userMessage) => {
    setLoading(true)
    setStreamingMessage('')
    
    // Create abort controller for this request
    abortControllerRef.current = new AbortController()
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: conversationId
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullMessage = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.token) {
                fullMessage += data.token
                setStreamingMessage(fullMessage)
              }
              
              if (data.done) {
                // Finalize message
                setMessages(prev => [...prev, { 
                  role: 'assistant', 
                  content: fullMessage,
                  sources: data.sources,
                  cacheHit: data.cache_hit
                }])
                setStreamingMessage('')
                
                if (data.session_id) {
                  setConversationId(data.session_id)
                }
              }
              
              if (data.error) {
                throw new Error(data.error)
              }
            } catch (parseError) {
              // Skip invalid JSON
              if (parseError.message !== 'Unexpected end of JSON input') {
                console.warn('Parse error:', parseError)
              }
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request aborted')
        return
      }
      
      console.error('Streaming error:', error)
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: 'Sorry, something went wrong. Please try again.' 
      }])
      setStreamingMessage('')
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }, [conversationId])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    
    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    
    // Use streaming for better UX
    await sendMessageStreaming(userMessage)
  }

  const clearChat = async () => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Clear from backend if session exists
    if (conversationId) {
      try {
        await fetch(`${API_BASE}/api/conversation/${conversationId}`, { method: 'DELETE' })
      } catch (error) {
        console.log('Error clearing backend session:', error)
      }
    }
    
    // Clear localStorage
    localStorage.removeItem(STORAGE_KEY)
    
    // Clear frontend state
    setMessages([])
    setConversationId(null)
    setStreamingMessage('')
    setLoading(false)
  }

  // Show loading state while restoring
  if (isRestoring) {
    return (
      <div className="chat-container">
        <div className="chat-header">
          <h1>💬 Personal RAG Assistant</h1>
        </div>
        <div className="messages-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>💬 Personal RAG Assistant</h1>
        <div className="header-badges">
          <span className="badge streaming">⚡ Streaming</span>
          <span className="badge optimized">🚀 Optimized</span>
        </div>
        <button onClick={clearChat} className="clear-btn">
          Clear Chat
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 && !streamingMessage && (
          <div className="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>Ask me anything about my experience, skills, or projects.</p>
            <div className="suggestions">
              <button onClick={() => { setInput("What are your skills?"); }}>💻 Skills</button>
              <button onClick={() => { setInput("Tell me about your projects"); }}>🚀 Projects</button>
              <button onClick={() => { setInput("What sports do you play?"); }}>🏏 Sports</button>
              <button onClick={() => { setInput("How does this chatbot work?"); }}>🤖 About RAG</button>
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'user' && <span className="avatar">👤</span>}
              {msg.role === 'assistant' && <span className="avatar">🤖</span>}
              {msg.role === 'error' && <span className="avatar">⚠️</span>}
              <div className="text">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
                {msg.cacheHit && <span className="cache-badge">⚡ Cached</span>}
              </div>
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                <small>Sources: {msg.sources.map(s => s.source).join(', ')}</small>
              </div>
            )}
          </div>
        ))}

        {/* Streaming message */}
        {streamingMessage && (
          <div className="message assistant streaming">
            <div className="message-content">
              <span className="avatar">🤖</span>
              <div className="text">
                <ReactMarkdown>{streamingMessage}</ReactMarkdown>
                <span className="cursor">▊</span>
              </div>
            </div>
          </div>
        )}

        {/* Loading indicator (only when not streaming) */}
        {loading && !streamingMessage && (
          <div className="message assistant">
            <div className="message-content">
              <span className="avatar">🤖</span>
              <div className="text typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything..."
          disabled={loading}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {loading ? '⏳' : '🚀'}
        </button>
      </form>
    </div>
  )
}

export default App
