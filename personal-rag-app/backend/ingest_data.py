"""
Ingest personal documents into vector database
Adds rich metadata (category, topic, document_title, chunk_index, etc.)
to each chunk for better retrieval and LLM context.
"""
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vectorstore import vectorstore_service
import shutil
import os
from datetime import datetime
from pathlib import Path

# ============================================
# METADATA MAPPING: filename → category & topic
# ============================================
FILE_METADATA_MAP = {
    "about_me.txt":         {"category": "personal",    "topic": "bio & background",        "document_title": "About Me"},
    "contact.txt":          {"category": "personal",    "topic": "contact information",      "document_title": "Contact Info"},
    "education.txt":        {"category": "education",   "topic": "academic background",      "document_title": "Education"},
    "hobbies_sports.txt":   {"category": "personal",    "topic": "hobbies & sports",         "document_title": "Hobbies & Sports"},
    "projects.txt":         {"category": "professional","topic": "projects & portfolio",      "document_title": "Projects"},
    "skills.txt":           {"category": "professional","topic": "technical skills",          "document_title": "Skills"},
    "testimonials.txt":     {"category": "professional","topic": "testimonials & references", "document_title": "Testimonials"},
    "this_rag_project.txt": {"category": "professional","topic": "RAG project details",      "document_title": "This RAG Project"},
    "work_experience.txt":  {"category": "professional","topic": "work experience",           "document_title": "Work Experience"},
}


def get_metadata_for_source(source_path: str) -> dict:
    """Extract rich metadata from the source file path."""
    filename = Path(source_path).name
    meta = FILE_METADATA_MAP.get(filename, {
        "category": "general",
        "topic": "unknown",
        "document_title": filename.replace(".txt", "").replace("_", " ").title(),
    })
    return {
        **meta,
        "file_name": filename,
        "ingested_at": datetime.now().isoformat(),
        "author": "Abdullah Akram",
    }


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

# Enrich each chunk with metadata
print("🏷️  Enriching chunks with metadata...")
for i, chunk in enumerate(splits):
    source = chunk.metadata.get("source", "")
    rich_meta = get_metadata_for_source(source)
    chunk.metadata.update(rich_meta)
    chunk.metadata["chunk_index"] = i
    chunk.metadata["total_chunks"] = len(splits)

# Print metadata summary
print("\n📋 Metadata summary per chunk:")
for i, chunk in enumerate(splits):
    m = chunk.metadata
    print(f"  Chunk {i}: [{m.get('category')}] {m.get('document_title')} — {m.get('topic')}")

# Create new vectorstore with documents
print("\n💾 Creating vector database...")
from langchain_community.vectorstores import Chroma
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=vectorstore_service.embeddings,
    persist_directory=chroma_dir
)
print(f"✅ Vector database created with {len(splits)} chunks (with rich metadata)!")
print("\n🎉 SUCCESS! Your RAG system now knows all about Abdullah Akram!")
