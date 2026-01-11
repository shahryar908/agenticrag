# =========================================
# BGE Embedding Demo (Simple & Clear)
# =========================================

from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Load the embedding model
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# 2. Sample documents (what you store in vector DB later)
documents = [
    "Terraform is an infrastructure as code tool used to manage cloud resources.",
    "Kubernetes orchestrates containerized applications at scale.",
    "AWS VPC provides isolated virtual networks in the cloud.",
    "Docker is used to build and run containers."
]

# 3. User query
query = "What is CONTIANER used for?"

# 4. Create embeddings for documents (NO prefix)
doc_embeddings = model.encode(
    documents,
    normalize_embeddings=True
)

# 5. Create embedding for query (PREFIX REQUIRED for BGE)
query_embedding = model.encode(
    "Represent this sentence for searching relevant passages: " + query,
    normalize_embeddings=True
)

# 6. Compute similarity (cosine similarity via dot product)
scores = np.dot(doc_embeddings, query_embedding)

# 7. Sort results by similarity
results = sorted(
    zip(documents, scores),
    key=lambda x: x[1],
    reverse=True
)

# 8. Print results
print("\n🔍 Query:", query)
print("\n📊 Similarity Results:\n")

for doc, score in results:
    print(f"{score:.4f} → {doc}")
