# =========================================
# Fast BGE Embedding Demo with ChromaDB
# =========================================

import chromadb
from sentence_transformers import SentenceTransformer
import time

# Start timer
start = time.time()

# 1. Initialize ChromaDB (persistent storage)
client = chromadb.PersistentClient(path="./chroma_db")

# 2. Get or create collection
collection = client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
)

# 3. Load embedding model (cached after first run)
print("Loading model...")
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
print(f"Model loaded in {time.time() - start:.2f}s")

# 4. Sample documents
documents = [
    "Terraform is an infrastructure as code tool used to manage cloud resources.",
    "Kubernetes orchestrates containerized applications at scale.",
    "AWS VPC provides isolated virtual networks in the cloud.",
    "Docker is used to build and run containers."
]

# 5. Add documents to ChromaDB (only if collection is empty)
if collection.count() == 0:
    print("\nAdding documents to ChromaDB...")
    # Generate embeddings
    embeddings = model.encode(documents, normalize_embeddings=True)

    # Store in ChromaDB
    collection.add(
        embeddings=embeddings.tolist(),
        documents=documents,
        ids=[f"doc_{i}" for i in range(len(documents))]
    )
    print(f"Added {len(documents)} documents")
else:
    print(f"\nUsing existing {collection.count()} documents from database")

# 6. User query
query = "What is Terraform used for?"

# 7. Create query embedding with BGE prefix
query_embedding = model.encode(
    "Represent this sentence for searching relevant passages: " + query,
    normalize_embeddings=True
)

# 8. Search ChromaDB
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=4
)

# 9. Print results
print(f"\nQuery: {query}")
print("\nSimilarity Results:\n")

for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
    similarity = 1 - distance  # Convert distance to similarity
    print(f"{similarity:.4f} -> {doc}")

print(f"\nTotal time: {time.time() - start:.2f}s")