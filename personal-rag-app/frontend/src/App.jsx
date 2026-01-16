import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    
    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await axios.post('/api/chat', {
        message: userMessage,
        conversation_id: conversationId
      })

      // Add assistant response
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response 
      }])

      // Store conversation ID for context
      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id)
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: 'Sorry, something went wrong. Please try again.' 
      }])
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setConversationId(null)
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>💬 Personal RAG Assistant</h1>
        <button onClick={clearChat} className="clear-btn">
          Clear Chat
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>Ask me anything about my experience, skills, or projects.</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'user' && <span className="avatar">👤</span>}
              {msg.role === 'assistant' && <span className="avatar">🤖</span>}
              {msg.role === 'error' && <span className="avatar">⚠️</span>}
              <div className="text">{msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
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
