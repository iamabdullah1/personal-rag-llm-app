"""
Document Ingestion Script
Run this to process and embed your personal documents.

Usage:
    python scripts/ingest_documents.py --data-dir ./data/personal --target chroma
    python scripts/ingest_documents.py --data-dir ./data/personal --target pinecone
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import argparse

load_dotenv()


def load_documents(data_dir: str):
    """Load all documents from the data directory."""
    print(f"📂 Loading documents from {data_dir}...")
    
    documents = []
    
    # Load PDFs
    try:
        pdf_loader = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyPDFLoader
        )
        pdf_docs = pdf_loader.load()
        documents.extend(pdf_docs)
        print(f"  ✅ Loaded {len(pdf_docs)} PDF files")
    except Exception as e:
        print(f"  ⚠️ Error loading PDFs: {e}")
    
    # Load text files
    try:
        txt_loader = DirectoryLoader(
            data_dir, glob="**/*.txt", loader_cls=TextLoader
        )
        txt_docs = txt_loader.load()
        documents.extend(txt_docs)
        print(f"  ✅ Loaded {len(txt_docs)} TXT files")
    except Exception as e:
        print(f"  ⚠️ Error loading TXT: {e}")
    
    # Load markdown files
    try:
        md_loader = DirectoryLoader(
            data_dir, glob="**/*.md", loader_cls=TextLoader
        )
        md_docs = md_loader.load()
        documents.extend(md_docs)
        print(f"  ✅ Loaded {len(md_docs)} MD files")
    except Exception as e:
        print(f"  ⚠️ Error loading MD: {e}")
    
    print(f"📄 Total documents loaded: {len(documents)}")
    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into chunks."""
    print(f"✂️ Splitting documents (chunk_size={chunk_size})...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    print(f"📦 Created {len(chunks)} chunks")
    return chunks


def create_embeddings():
    """Create FREE HuggingFace embeddings instance (no API key needed!)."""
    print("📥 Loading HuggingFace embedding model (first time may take a moment)...")
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def ingest_to_chroma(chunks, embeddings, persist_dir="./chroma_db"):
    """Ingest chunks to local Chroma database."""
    print(f"💾 Ingesting to Chroma at {persist_dir}...")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print("✅ Chroma ingestion complete!")
    return vectorstore


def ingest_to_pinecone(chunks, embeddings):
    """Ingest chunks to Pinecone (production)."""
    print("🌲 Ingesting to Pinecone...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "personal-rag")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=api_key)
    
    # Create index if it doesn't exist
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"  Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embedding dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    # Ingest documents
    from langchain_pinecone import PineconeVectorStore
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name
    )
    
    print("✅ Pinecone ingestion complete!")
    return vectorstore


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument(
        "--data-dir",
        default="./data/personal",
        help="Directory containing personal documents"
    )
    parser.add_argument(
        "--target",
        choices=["chroma", "pinecone", "both"],
        default="chroma",
        help="Target vector store"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size for text splitting"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting document ingestion...")
    print("=" * 50)
    
    # Load and process documents
    documents = load_documents(args.data_dir)
    
    if not documents:
        print("❌ No documents found! Please add documents to the data directory.")
        return
    
    chunks = split_documents(documents, chunk_size=args.chunk_size)
    embeddings = create_embeddings()
    
    # Ingest based on target
    if args.target in ["chroma", "both"]:
        ingest_to_chroma(chunks, embeddings)
    
    if args.target in ["pinecone", "both"]:
        ingest_to_pinecone(chunks, embeddings)
    
    print("=" * 50)
    print("🎉 Ingestion complete!")


if __name__ == "__main__":
    main()
