"""
=========================================
Complete RAG System with Groq LLM
=========================================

Three-Part Pipeline:
1. QUERY    - User asks a question
2. RETRIEVE - Search vector database for relevant docs
3. ANSWER   - LLM generates answer using retrieved context
"""

import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import time

# Load environment variables
load_dotenv()


class CompleteRAG:
    """
    Full RAG system: Query → Retrieve → Generate
    """

    def __init__(self, collection_name: str = "knowledge_base"):
        """Initialize RAG system with Groq LLM"""
        print("Initializing Complete RAG System...")
        start = time.time()

        # Initialize Groq client
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.llm_model = "llama-3.3-70b-versatile"  # Fast and powerful

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Load embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer("BAAI/bge-base-en-v1.5")

        print(f"System ready in {time.time() - start:.2f}s")
        print(f"Documents in database: {self.collection.count()}\n")

    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """
        Add documents to the knowledge base

        Args:
            documents: List of text documents
            metadata: Optional metadata for each doc
        """
        print(f"Adding {len(documents)} documents...")
        start_id = self.collection.count()
        ids = [f"doc_{start_id + i}" for i in range(len(documents))]

        # Generate embeddings
        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        # Store in database
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

        print(f"Added {len(documents)} documents")
        print(f"Total documents: {self.collection.count()}\n")

    def retrieve(self, query: str, n_results: int = 3) -> Dict:
        """
        STEP 2: Retrieve relevant documents

        Args:
            query: User question
            n_results: Number of documents to retrieve

        Returns:
            Retrieved documents with metadata
        """
        # Add BGE prefix for better retrieval
        search_query = f"Represent this sentence for searching relevant passages: {query}"

        # Generate query embedding
        query_embedding = self.model.encode(
            search_query,
            normalize_embeddings=True
        )

        # Search database
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

    def generate_answer(self, query: str, context_docs: List[str]) -> str:
        """
        STEP 3: Generate answer using LLM

        Args:
            query: User question
            context_docs: Retrieved documents for context

        Returns:
            LLM-generated answer
        """
        # Build context from retrieved docs
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc}"
            for i, doc in enumerate(context_docs)
        ])

        # Create prompt for LLM
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- Answer ONLY based on the context provided
- If the context doesn't contain the answer, say "I don't have enough information to answer that"
- Be concise and accurate
- Cite which document number you're using (e.g., "According to Document 1...")
"""

        user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        # Call Groq LLM
        response = self.groq_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower = more factual
            max_tokens=500
        )

        return response.choices[0].message.content

    def ask(self, query: str, n_results: int = 3, show_sources: bool = True) -> str:
        """
        Complete RAG Pipeline: Query → Retrieve → Answer

        Args:
            query: User question
            n_results: Number of documents to retrieve
            show_sources: Whether to show source documents

        Returns:
            Complete answer with optional sources
        """
        print(f"\nQuery: {query}")
        print("-" * 60)

        # STEP 1: Query (already have it)

        # STEP 2: Retrieve
        print("Retrieving relevant documents...")
        start = time.time()
        results = self.retrieve(query, n_results)
        retrieve_time = time.time() - start
        print(f"Retrieved {len(results['documents'])} documents in {retrieve_time:.2f}s")

        # STEP 3: Generate
        print("Generating answer with LLM...")
        start = time.time()
        answer = self.generate_answer(query, results['documents'])
        generate_time = time.time() - start
        print(f"Generated answer in {generate_time:.2f}s\n")

        # Format output
        output = f"Answer:\n{answer}\n"

        if show_sources:
            output += "\n" + "=" * 60
            output += "\nSources:\n"
            for i, (doc, distance) in enumerate(zip(results['documents'], results['distances']), 1):
                similarity = 1 - distance
                metadata = results['metadatas'][i-1] if results['metadatas'] else {}
                category = metadata.get('category', 'N/A')

                output += f"\n[{i}] Similarity: {similarity:.4f} | Category: {category}\n"
                output += f"    {doc[:150]}...\n"

        return output

    def get_stats(self):
        """Get system statistics"""
        return {
            'total_documents': self.collection.count(),
            'embedding_model': 'BAAI/bge-base-en-v1.5',
            'llm_model': self.llm_model,
            'collection_name': self.collection.name
        }


# =========================================
# Demo Usage
# =========================================

if __name__ == "__main__":
    # Initialize RAG system
    rag = CompleteRAG(collection_name="tech_knowledge")

    # Sample knowledge base
    documents = [
        "Terraform is an infrastructure as code (IaC) tool that allows you to define and provision cloud infrastructure using declarative configuration files. It supports multiple cloud providers like AWS, Azure, and GCP.",
        "Kubernetes is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications across clusters of servers.",
        "AWS VPC (Virtual Private Cloud) provides isolated virtual networks in the cloud with complete control over IP address ranges, subnets, route tables, and network gateways.",
        "Docker is a containerization platform that packages applications and their dependencies into lightweight, portable containers that can run consistently across different environments.",
        "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, machine learning, and automation.",
        "React is a JavaScript library for building user interfaces, particularly single-page applications. It uses a component-based architecture and virtual DOM for efficient rendering.",
        "PostgreSQL is a powerful, open-source relational database management system that supports advanced features like JSONB, full-text search, and complex queries.",
        "Redis is an in-memory data structure store used as a database, cache, and message broker. It's extremely fast and commonly used for session management and real-time analytics.",
        "FastAPI is a modern Python web framework for building APIs with automatic validation, serialization, and interactive documentation using Python type hints.",
        "Git is a distributed version control system that tracks changes in source code during software development. It enables collaboration and maintains project history."
    ]

    metadata = [
        {"category": "DevOps", "difficulty": "Intermediate"},
        {"category": "DevOps", "difficulty": "Advanced"},
        {"category": "Cloud", "difficulty": "Intermediate"},
        {"category": "DevOps", "difficulty": "Beginner"},
        {"category": "Programming", "difficulty": "Beginner"},
        {"category": "Frontend", "difficulty": "Intermediate"},
        {"category": "Database", "difficulty": "Intermediate"},
        {"category": "Database", "difficulty": "Intermediate"},
        {"category": "Backend", "difficulty": "Intermediate"},
        {"category": "DevOps", "difficulty": "Beginner"}
    ]

    # Add documents (only once)
    if rag.collection.count() == 0:
        rag.add_documents(documents, metadata=metadata)

    # Test questions
    print("\n" + "=" * 60)
    print("COMPLETE RAG SYSTEM - DEMO")
    print("=" * 60)

    questions = [
        "What is Docker and how does it work?",
        "How can I manage cloud infrastructure as code?",
        "What's the best database for caching?",
        "Explain the difference between Kubernetes and Docker"
    ]

    for question in questions:
        answer = rag.ask(question, n_results=3, show_sources=True)
        print(answer)
        print("\n" + "=" * 60 + "\n")

    # Show stats
    print(f"System Stats: {rag.get_stats()}")