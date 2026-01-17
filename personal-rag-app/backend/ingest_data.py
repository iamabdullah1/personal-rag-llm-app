"""
Ingest personal documents into vector database
"""
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vectorstore import vectorstore_service
import shutil
import os

# Clear existing database
chroma_dir = "./chroma_db"
if os.path.exists(chroma_dir):
    print(f"🗑️  Removing old database: {chroma_dir}")
    shutil.rmtree(chroma_dir)

# Reset vectorstore
vectorstore_service._vectorstore = None

# Load documents from personal folder
print("📂 Loading documents from data/personal/...")
loader = DirectoryLoader(
    "data/personal/",
    glob="**/*.txt",
    loader_cls=TextLoader
)
documents = loader.load()
print(f"✅ Loaded {len(documents)} documents")

# Split documents into chunks
print("✂️  Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
splits = text_splitter.split_documents(documents)
print(f"✅ Created {len(splits)} chunks")

# Create new vectorstore with documents
print("💾 Creating vector database...")
from langchain_community.vectorstores import Chroma
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=vectorstore_service.embeddings,
    persist_directory=chroma_dir
)
print(f"✅ Vector database created with {len(splits)} chunks!")
print("\n🎉 SUCCESS! Your RAG system now knows all about Abdullah Akram!")
