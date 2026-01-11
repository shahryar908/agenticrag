"""
Test client for RAG API Server

Run the server first: uv run api_server.py
Then run this: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test API health check"""
    print("\n1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_add_document():
    """Test adding a document"""
    print("\n2. Testing Add Document...")

    documents = [
        {
            "text": "Python is a high-level programming language used for web development, data science, and automation.",
            "metadata": {"category": "Programming", "difficulty": "Beginner"}
        },
        {
            "text": "FastAPI is a modern Python web framework for building APIs with automatic validation and documentation.",
            "metadata": {"category": "Backend", "difficulty": "Intermediate"}
        },
        {
            "text": "Docker allows you to package applications into containers that run consistently across environments.",
            "metadata": {"category": "DevOps", "difficulty": "Intermediate"}
        }
    ]

    for doc in documents:
        response = requests.post(f"{BASE_URL}/add-document", json=doc)
        print(f"Added: {doc['text'][:50]}... | Status: {response.status_code}")


def test_upload_pdf():
    """Test PDF upload (if you have a PDF file)"""
    print("\n3. Testing PDF Upload...")
    print("Skipping (no PDF file available)")
    # Uncomment if you have a PDF:
    # with open("sample.pdf", "rb") as f:
    #     files = {"file": ("sample.pdf", f, "application/pdf")}
    #     response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
    #     print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_ask_question():
    """Test asking questions"""
    print("\n4. Testing Questions...")

    questions = [
        "What is Python used for?",
        "Tell me about Docker",
        "What's the best framework for building APIs?"
    ]

    for query in questions:
        print(f"\nQuery: {query}")
        print("-" * 60)

        payload = {
            "query": query,
            "n_results": 3,
            "show_sources": True
        }

        response = requests.post(f"{BASE_URL}/ask", json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data['answer']}")
            print(f"Retrieval Time: {data['retrieval_time']:.3f}s")
            print(f"Generation Time: {data['generation_time']:.3f}s")

            if data['sources']:
                print(f"\nTop Sources:")
                for i, source in enumerate(data['sources'][:2], 1):
                    print(f"  [{i}] Similarity: {source['similarity']:.4f}")
                    print(f"      {source['document'][:100]}...")
        else:
            print(f"Error: {response.status_code} - {response.json()}")


def test_stats():
    """Test getting stats"""
    print("\n5. Testing Stats...")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Stats: {json.dumps(response.json(), indent=2)}")


def main():
    print("=" * 60)
    print("RAG API SERVER - TEST CLIENT")
    print("=" * 60)

    try:
        test_health()
        test_add_document()
        test_upload_pdf()
        test_ask_question()
        test_stats()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server")
        print("Make sure the server is running: uv run api_server.py")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()