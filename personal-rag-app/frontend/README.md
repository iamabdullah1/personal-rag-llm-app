# Personal RAG Frontend

A beautiful, modern chat interface for your Personal RAG Assistant.

## 🚀 Quick Start

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

The app will be available at: http://localhost:3000

### Build for Production
```bash
npm run build
```

## ⚙️ Configuration

The frontend connects to your FastAPI backend through a proxy configured in `vite.config.js`.

- **Backend URL**: http://localhost:8000
- **Frontend URL**: http://localhost:3000

## 🎨 Features

- ✅ Real-time chat interface
- ✅ Conversation history
- ✅ Beautiful gradient design
- ✅ Responsive layout (mobile-friendly)
- ✅ Loading states & error handling
- ✅ Auto-scroll to latest message
- ✅ Clear chat functionality

## 🔧 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Axios** - HTTP client
- **CSS3** - Styling with gradients & animations

## 📝 Usage

1. Make sure your backend is running on port 8000
2. Start the frontend with `npm run dev`
3. Open http://localhost:3000
4. Start chatting with your RAG assistant!

## 🤝 API Integration

The frontend expects these backend endpoints:

- `POST /chat` - Send messages and receive responses
  ```json
  {
    "message": "your question",
    "conversation_id": "optional-id"
  }
  ```

Response format:
```json
{
  "response": "assistant's answer",
  "conversation_id": "conversation-id",
  "sources": ["source1", "source2"]
}
```
