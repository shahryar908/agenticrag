import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import time


class RAGSystem:
  

    def __init__(self, collection_name: str = "knowledge_base", db_path: str = "./chroma_db"):
        """
        Initialize the RAG system.

        Args:
            collection_name: Name for your document collection
            db_path: Path to store the ChromaDB database
        """
        print(f"Initializing RAG System...")
        start = time.time()

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(path=db_path)

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity for semantic search
        )

        # Load embedding model (cached after first run)
        print("Loading embedding model...")
        self.model = SentenceTransformer("BAAI/bge-base-en-v1.5")

        print(f"RAG System ready in {time.time() - start:.2f}s")
        print(f"Documents in database: {self.collection.count()}\n")

    def add_documents(self, documents: List[str], metadata: List[Dict] = None, batch_size: int = 100):
        """
        Add documents to the RAG system.

        Args:
            documents: List of text documents to add
            metadata: Optional metadata for each document (e.g., source, date, author)
            batch_size: Process documents in batches for memory efficiency
        """
        print(f"Adding {len(documents)} documents...")
        start = time.time()

        # Generate unique IDs
        start_id = self.collection.count()
        ids = [f"doc_{start_id + i}" for i in range(len(documents))]

        # Process in batches to handle large datasets
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_metadata = metadata[i:i + batch_size] if metadata else None

            # Generate embeddings
            embeddings = self.model.encode(
                batch_docs,
                normalize_embeddings=True,
                show_progress_bar=True
            )

            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=batch_docs,
                ids=batch_ids,
                metadatas=batch_metadata
            )

        print(f"Added {len(documents)} documents in {time.time() - start:.2f}s")
        print(f"Total documents: {self.collection.count()}\n")

    def search(self, query: str, n_results: int = 5) -> Dict:
        """
        Search for relevant documents.

        Args:
            query: The search query
            n_results: Number of results to return

        Returns:
            Dictionary with documents, distances, and metadata
        """
        # Add BGE-specific prefix for better search quality
        search_query = f"Represent this sentence for searching relevant passages: {query}"

        # Generate query embedding
        query_embedding = self.model.encode(
            search_query,
            normalize_embeddings=True
        )

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        # Format results
        formatted_results = {
            'query': query,
            'documents': results['documents'][0],
            'distances': results['distances'][0],
            'metadata': results['metadatas'][0] if results['metadatas'][0] else None,
            'ids': results['ids'][0]
        }

        return formatted_results

    def generate_answer(self, query: str, n_results: int = 3) -> str:
        """
        Generate an answer using retrieved context.
        This is where you'd integrate with an LLM (OpenAI, Claude, etc.)

        Args:
            query: User question
            n_results: Number of context documents to use

        Returns:
            Generated answer (currently returns context only - integrate LLM here)
        """
        # Search for relevant documents
        results = self.search(query, n_results)

        # Build context from retrieved documents
        context = "\n\n".join([
            f"[Source {i+1}] {doc}"
            for i, doc in enumerate(results['documents'])
        ])

        # TODO: Integrate with LLM here (OpenAI API, Claude API, etc.)
        # For now, return the context
        return f"""
Query: {query}

Relevant Context:
{context}

---
NOTE: To generate AI answers, integrate with OpenAI/Claude API.
For now, this returns the relevant context documents.
"""

    def clear_database(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
        print("Database cleared")

    def get_stats(self):
        """Get database statistics."""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection.name
        }


# =========================================
# Example Usage
# =========================================

if __name__ == "__main__":
    # Initialize RAG system
    rag = RAGSystem(collection_name="tech_docs")

    # Sample documents (in production, load from files/database)
    documents = [
        "Terraform is an infrastructure as code tool used to manage cloud resources declaratively.",
        "Kubernetes orchestrates containerized applications at scale across multiple servers.",
        "AWS VPC provides isolated virtual networks in the cloud with complete control over networking.",
        "Docker is used to build, ship, and run containers in isolated environments.",
        "Python is a high-level programming language widely used for web development and data science.",
        "React is a JavaScript library for building user interfaces with reusable components.",
        "PostgreSQL is a powerful open-source relational database management system.",
        "Redis is an in-memory data store used for caching and real-time analytics."
    ]

    # Optional metadata for each document
    metadata = [
        {"category": "DevOps", "source": "terraform.io"},
        {"category": "DevOps", "source": "kubernetes.io"},
        {"category": "Cloud", "source": "aws.amazon.com"},
        {"category": "DevOps", "source": "docker.com"},
        {"category": "Programming", "source": "python.org"},
        {"category": "Frontend", "source": "react.dev"},
        {"category": "Database", "source": "postgresql.org"},
        {"category": "Database", "source": "redis.io"}
    ]

    # Add documents (only if not already added)
    if rag.collection.count() == 0:
        rag.add_documents(documents, metadata=metadata)

    # Test queries
    test_queries = [
        "What tools are used for containers?",
        "How do I manage cloud infrastructure?",
        "What database should I use for caching?"
    ]

    print("=" * 60)
    print("RAG SYSTEM DEMO")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)

        # Search for relevant documents
        results = rag.search(query, n_results=3)

        print("Top Results:")
        for i, (doc, distance) in enumerate(zip(results['documents'], results['distances']), 1):
            similarity = 1 - distance
            metadata_info = results['metadata'][i-1] if results['metadata'] else {}
            category = metadata_info.get('category', 'N/A')
            source = metadata_info.get('source', 'N/A')

            print(f"\n{i}. Similarity: {similarity:.4f} | Category: {category}")
            print(f"   {doc}")
            print(f"   Source: {source}")

        print("\n" + "=" * 60)

    # Show stats
    print(f"\nDatabase Stats: {rag.get_stats()}")