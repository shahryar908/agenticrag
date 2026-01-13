"""
=========================================
FastAPI Server for RAG System
=========================================

Endpoints:
- POST /upload-pdf     - Upload and process PDF files
- POST /add-document   - Add text document
- POST /ask            - Ask a question (RAG)
- GET  /stats          - Get system statistics
- DELETE /clear        - Clear all documents
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import io
import time

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="RAG API Server",
    description="Production RAG system with PDF upload and LLM generation",
    version="1.0.0"
)

# Add CORS middleware (for web frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Document(BaseModel):
    text: str
    metadata: Optional[dict] = None

class Question(BaseModel):
    query: str
    n_results: int = 3
    show_sources: bool = True

class Answer(BaseModel):
    query: str
    answer: str
    sources: Optional[List[dict]] = None
    retrieval_time: float
    generation_time: float


# =========================================
# RAG System (Global Instance)
# =========================================

class RAGService:
    """Singleton RAG service"""

    def __init__(self):
        print("Initializing RAG Service...")
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.llm_model = "llama-3.3-70b-versatile"

        # ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="api_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

        # Embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        print("RAG Service ready!")

    def add_documents(self, documents: List[str], metadata: List[dict] = None):
        """Add documents to knowledge base"""
        start_id = self.collection.count()
        ids = [f"doc_{start_id + i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True
        )

        # Store in database
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

        return len(documents)

    def retrieve(self, query: str, n_results: int = 3):
        """Retrieve relevant documents"""
        search_query = f"Represent this sentence for searching relevant passages: {query}"

        query_embedding = self.model.encode(
            search_query,
            normalize_embeddings=True
        )

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        return {
            'documents': results['documents'][0],
            'distances': results['distances'][0],
            'metadatas': results['metadatas'][0],
            'ids': results['ids'][0]
        }

    def generate_answer(self, query: str, context_docs: List[str]):
        """Generate answer using LLM"""
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc}"
            for i, doc in enumerate(context_docs)
        ])

        system_prompt = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- Answer ONLY based on the context provided
- If the context doesn't contain the answer, say "I don't have enough information to answer that"
- Be concise and accurate
- Cite which document number you're using"""

        user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        response = self.groq_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        return response.choices[0].message.content

    def process_pdf(self, pdf_file: bytes):
        """Extract text from PDF"""
        pdf_reader = PdfReader(io.BytesIO(pdf_file))
        documents = []
        metadata = []

        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text.strip():  # Only add non-empty pages
                documents.append(text)
                metadata.append({
                    "source": "pdf_upload",
                    "page": i + 1,
                    "total_pages": len(pdf_reader.pages)
                })

        return documents, metadata

    def clear_database(self):
        """Clear all documents"""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name="api_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

    def get_stats(self):
        """Get system statistics"""
        return {
            "total_documents": self.collection.count(),
            "embedding_model": "BAAI/bge-base-en-v1.5",
            "llm_model": self.llm_model,
            "collection_name": self.collection.name
        }


# Initialize RAG service (singleton)
rag_service = RAGService()


# =========================================
# API Endpoints
# =========================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "status": "running",
        "message": "RAG API Server",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    try:
        # Check if RAG service is initialized
        if rag_service is None:
            return {"status": "unhealthy", "error": "RAG service not initialized"}

        # Check if ChromaDB is accessible
        count = rag_service.collection.count()

        return {
            "status": "healthy",
            "documents": count,
            "version": "1.0.0"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file

    Returns number of pages added to knowledge base
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Read file
        contents = await file.read()

        # Process PDF
        documents, metadata = rag_service.process_pdf(contents)

        # Add to knowledge base
        count = rag_service.add_documents(documents, metadata)

        return {
            "status": "success",
            "filename": file.filename,
            "pages_added": count,
            "total_documents": rag_service.collection.count()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-document")
async def add_document(doc: Document):
    """
    Add a text document to knowledge base

    Request body:
    - text: Document text
    - metadata: Optional metadata dict
    """
    try:
        metadata = [doc.metadata] if doc.metadata else None
        count = rag_service.add_documents([doc.text], metadata)

        return {
            "status": "success",
            "documents_added": count,
            "total_documents": rag_service.collection.count()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=Answer)
async def ask_question(question: Question):
    """
    Ask a question (RAG pipeline: Query → Retrieve → Generate)

    Request body:
    - query: The question
    - n_results: Number of documents to retrieve (default: 3)
    - show_sources: Include source documents (default: true)
    """
    try:
        # Check if database has documents
        if rag_service.collection.count() == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents in knowledge base. Please upload documents first."
            )

        # Retrieve
        start = time.time()
        results = rag_service.retrieve(question.query, question.n_results)
        retrieval_time = time.time() - start

        # Generate
        start = time.time()
        answer = rag_service.generate_answer(question.query, results['documents'])
        generation_time = time.time() - start

        # Format sources
        sources = None
        if question.show_sources:
            sources = [
                {
                    "document": doc,
                    "similarity": 1 - distance,
                    "metadata": meta,
                    "id": doc_id
                }
                for doc, distance, meta, doc_id in zip(
                    results['documents'],
                    results['distances'],
                    results['metadatas'],
                    results['ids']
                )
            ]

        return Answer(
            query=question.query,
            answer=answer,
            sources=sources,
            retrieval_time=retrieval_time,
            generation_time=generation_time
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return rag_service.get_stats()


@app.delete("/clear")
async def clear_database():
    """Clear all documents from knowledge base"""
    try:
        rag_service.clear_database()
        return {
            "status": "success",
            "message": "All documents cleared",
            "total_documents": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================
# Run Server
# =========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )