# Personal RAG LLM Application

A sophisticated Retrieval-Augmented Generation (RAG) application built with FastAPI, featuring conversation memory, semantic caching, and vector-based document retrieval.

## 🌟 Features

- **RAG (Retrieval-Augmented Generation)**: Intelligent document retrieval and question answering
- **Conversation Memory**: Maintains context across conversations
- **Semantic Caching**: Optimizes response time for similar queries
- **Vector Database**: ChromaDB for efficient similarity search
- **Multiple LLM Support**: Compatible with various language models
- **FastAPI Backend**: High-performance async API

## 📁 Project Structure

```
personal-rag-app/
├── backend/
│   ├── app/
│   │   ├── models/          # Data models and schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Core business logic
│   │   └── utils/           # Utility functions
│   ├── data/personal/       # Personal knowledge base
│   ├── chroma_db/           # Vector database
│   └── scripts/             # Helper scripts
└── frontend/                # (Coming soon)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- pip or uv package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/iamabdullah1/personal-rag-llm-app.git
cd personal-rag-llm-app
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the backend directory with:
```
OPENAI_API_KEY=your_api_key_here
# Or configure other LLM providers
```

### Running the Application

```bash
cd backend
python run.py
```

The API will be available at `http://localhost:8000`

## 📚 Documentation

- [Complete Documentation](backend/COMPLETE_DOCUMENTATION.md)
- [Conversation Memory Guide](backend/CONVERSATION_MEMORY.md)
- [Embedding Options](backend/EMBEDDING_OPTIONS.md)
- [HuggingFace Setup](backend/HUGGINGFACE_SETUP.md)
- [FastAPI Beginner Guide](FastAPI_Beginner_Guide.md)
- [RAG Application Guide](RAG_Application_Guide.md)

## 🔧 Configuration

The application uses ChromaDB for vector storage and supports multiple embedding models:
- OpenAI Embeddings
- HuggingFace Models
- Sentence Transformers

## 📝 API Endpoints

- `POST /chat` - Send messages and get RAG-enhanced responses
- `GET /health` - Health check endpoint
- Additional endpoints documented in the API docs at `/docs`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [ChromaDB](https://www.trychroma.com/)
- [LangChain](https://python.langchain.com/)
- [OpenAI](https://openai.com/)

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Repository**: [https://github.com/iamabdullah1/personal-rag-llm-app](https://github.com/iamabdullah1/personal-rag-llm-app)
