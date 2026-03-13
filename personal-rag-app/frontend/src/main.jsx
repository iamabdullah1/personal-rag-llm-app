import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// --- Keep-alive timer to prevent backend sleep ---
function keepAlivePing() {
  fetch('/api/health').catch(() => {});
}

// Ping every 4 minutes (240,000 ms)
setInterval(keepAlivePing, 240000);
