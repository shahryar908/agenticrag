"""
Upload PDF to RAG API and ask questions
"""

import requests
import json

BASE_URL = "http://localhost:8000"
PDF_PATH = r"C:\Users\shahr\Downloads\eng.pdf"


def upload_pdf(file_path):
    """Upload PDF to the API"""
    print(f"Uploading PDF: {file_path}")
    print("-" * 60)

    try:
        with open(file_path, "rb") as f:
            files = {"file": ("eng.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/upload-pdf", files=files)

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Upload successful!")
            print(f"  Filename: {data['filename']}")
            print(f"  Pages added: {data['pages_added']}")
            print(f"  Total documents: {data['total_documents']}")
            return True
        else:
            print(f"[ERROR] Upload failed: {response.status_code}")
            print(f"  Error: {response.json()}")
            return False

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def ask_question(query):
    """Ask a question about the uploaded PDF"""
    print(f"\nQuestion: {query}")
    print("-" * 60)

    payload = {
        "query": query,
        "n_results": 3,
        "show_sources": True
    }

    response = requests.post(f"{BASE_URL}/ask", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer:")
        print(data['answer'])
        print(f"\nRetrieval Time: {data['retrieval_time']:.3f}s")
        print(f"Generation Time: {data['generation_time']:.3f}s")

        if data['sources']:
            print(f"\nTop {len(data['sources'])} Source Documents:")
            for i, source in enumerate(data['sources'], 1):
                print(f"\n[{i}] Similarity: {source['similarity']:.4f}")
                metadata = source.get('metadata', {})
                if metadata:
                    print(f"    Page: {metadata.get('page', 'N/A')} of {metadata.get('total_pages', 'N/A')}")
                print(f"    Preview: {source['document'][:200]}...")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())


def main():
    print("=" * 60)
    print("PDF UPLOAD & QUESTION ANSWERING")
    print("=" * 60)
    print()

    # Upload PDF
    success = upload_pdf(PDF_PATH)

    if not success:
        print("\nCannot proceed without PDF. Exiting.")
        return

    print("\n" + "=" * 60)

    # Ask questions about the PDF
    questions = [
        "What is this document about?",
        "Summarize the main points",
        "What are the key topics covered?"
    ]

    for question in questions:
        ask_question(question)
        print("\n" + "=" * 60)

    # Interactive mode
    print("\nInteractive Mode - Ask your own questions!")
    print("(Type 'quit' to exit)")
    print("-" * 60)

    while True:
        user_query = input("\nYour question: ").strip()

        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if user_query:
            ask_question(user_query)
            print("-" * 60)


if __name__ == "__main__":
    main()