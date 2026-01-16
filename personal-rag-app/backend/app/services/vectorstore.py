from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pinecone import Pinecone
from app.config import get_settings
import os

settings = get_settings()


class VectorStoreService:
    _instance = None
    _vectorstore = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Using FREE HuggingFace embeddings - no API key needed!
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def get_vectorstore(self, use_pinecone: bool = False):
        """Get or create vector store instance."""
        if self._vectorstore is not None:
            return self._vectorstore
        
        if use_pinecone and settings.pinecone_api_key:
            # Production: Use Pinecone
            from langchain_pinecone import PineconeVectorStore
            pc = Pinecone(api_key=settings.pinecone_api_key)
            self._vectorstore = PineconeVectorStore(
                index=pc.Index(settings.pinecone_index_name),
                embedding=self.embeddings,
                text_key="text"
            )
        else:
            # Development: Use Chroma
            self._vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings
            )
        
        return self._vectorstore
    
    def get_retriever(self):
        """Get retriever with configured settings."""
        vectorstore = self.get_vectorstore()
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.retriever_k}
        )


vectorstore_service = VectorStoreService()
