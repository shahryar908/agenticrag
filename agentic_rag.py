

import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv

# LangGraph imports
from langgraph.graph import StateGraph, END

# Vector DB
import chromadb
from sentence_transformers import SentenceTransformer

# Groq for LLM generation
from groq import Groq

# Load environment
load_dotenv()


# =========================================
# STATE DEFINITION
# =========================================

class AgentState(TypedDict):
    """State that flows through the agent workflow"""
    query: str                          # User question
    query_type: str                     # Type: factual, greeting, calculation, general
    needs_retrieval: bool               # Should we retrieve from DB?
    needs_web_search: bool              # Should we search the web?
    retrieved_docs: List[str]           # Documents from vector DB
    web_results: List[str]              # Results from web search
    answer: str                         # Final answer
    confidence: float                   # Confidence in answer (0-1)
    reasoning: str                      # Why agent chose this path
    iteration: int                      # Number of retries


# =========================================
# AGENTIC RAG CLASS
# =========================================

class AgenticRAG:
    """
    Advanced RAG system with autonomous decision-making
    """

    def __init__(self):
        print("Initializing Advanced Agentic RAG System...")

        # Groq for fast LLM
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.llm_model = "llama-3.3-70b-versatile"

        # Vector DB setup
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="agentic_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

        # Embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

        # Build workflow
        self.workflow = self._build_workflow()

        print("Agentic RAG System Ready!")
        print(f"Documents in DB: {self.collection.count()}")

    # =========================================
    # AGENT NODES
    # =========================================

    def analyze_query(self, state: AgentState) -> AgentState:
        """
        NODE 1: Analyze query and classify type
        Decides: What kind of question is this?
        """
        query = state["query"]

        # Use LLM to analyze query
        analysis_prompt = f"""Analyze this query and classify it:

Query: "{query}"

Classify into ONE of these types:
1. greeting - Hi, hello, how are you, etc.
2. factual - Questions starting with "what is", "explain", "describe", "tell me about" specific topics
3. calculation - Math or numerical computation
4. general - Broad general knowledge (history, science facts not in docs)
5. web_current - Needs current/recent information from web (news, today, latest)

IMPORTANT: If the query asks about LangGraph, RAG, ChromaDB, Groq, or agentic systems, classify as "factual" because we have specific docs about these.

Response format (one word only): greeting/factual/calculation/general/web_current
"""

        response = self.groq_client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.1,
            max_tokens=50
        )

        query_type = response.choices[0].message.content.strip().lower()

        # Determine what's needed based on type
        needs_retrieval = query_type in ["factual"]
        needs_web = query_type in ["web_current"]

        reasoning = f"Query classified as '{query_type}'. "
        if needs_retrieval:
            reasoning += "Will retrieve from knowledge base."
        elif needs_web:
            reasoning += "Will search the web for current info."
        else:
            reasoning += "Will generate answer directly."

        return {
            **state,
            "query_type": query_type,
            "needs_retrieval": needs_retrieval,
            "needs_web_search": needs_web,
            "reasoning": reasoning,
            "iteration": state.get("iteration", 0)
        }

    def retrieve_documents(self, state: AgentState) -> AgentState:
        """
        NODE 2: Retrieve relevant documents from vector DB
        """
        query = state["query"]

        if self.collection.count() == 0:
            return {
                **state,
                "retrieved_docs": [],
                "confidence": 0.0
            }

        # Add BGE prefix
        search_query = f"Represent this sentence for searching relevant passages: {query}"

        # Generate embedding
        query_embedding = self.embedding_model.encode(
            search_query,
            normalize_embeddings=True
        )

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )

        docs = results['documents'][0] if results['documents'] else []
        distances = results['distances'][0] if results['distances'] else []

        # Calculate confidence based on similarity
        confidence = 0.0
        if distances:
            avg_similarity = 1 - (sum(distances) / len(distances))
            confidence = avg_similarity

        return {
            **state,
            "retrieved_docs": docs,
            "confidence": confidence
        }

    def web_search(self, state: AgentState) -> AgentState:
        """
        NODE 3: Search web for current information
        (Placeholder - you can integrate Tavily or similar)
        """
        query = state["query"]

        # Placeholder for web search
        # In production, use Tavily or similar:
        # from tavily import TavilyClient
        # tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        # results = tavily.search(query)

        web_results = [
            f"[Web Search Placeholder] Results for: {query}",
            "Integrate Tavily API for real web search"
        ]

        return {
            **state,
            "web_results": web_results,
            "confidence": 0.5
        }

    def check_quality(self, state: AgentState) -> AgentState:
        """
        NODE 4: Check if retrieved documents are relevant
        Self-correction mechanism
        """
        query = state["query"]
        docs = state.get("retrieved_docs", [])
        confidence = state.get("confidence", 0.0)

        # If confidence is too low, mark for retry
        if confidence < 0.3 and docs:
            # Not confident in results
            return {
                **state,
                "needs_retrieval": False,  # Skip retrieval, use LLM directly
                "reasoning": state["reasoning"] + " Low confidence in retrieval. Using LLM directly."
            }

        return state

    def generate_answer(self, state: AgentState) -> AgentState:
        """
        NODE 5: Generate final answer using LLM
        """
        query = state["query"]
        query_type = state.get("query_type", "general")
        docs = state.get("retrieved_docs", [])
        web_results = state.get("web_results", [])

        # Build context
        context_parts = []

        if docs:
            context_parts.append("Knowledge Base Context:")
            for i, doc in enumerate(docs, 1):
                context_parts.append(f"[Doc {i}] {doc}")

        if web_results:
            context_parts.append("\nWeb Search Results:")
            for i, result in enumerate(web_results, 1):
                context_parts.append(f"[Result {i}] {result}")

        context = "\n".join(context_parts) if context_parts else "No specific context available."

        # Create prompt based on query type
        if query_type == "greeting":
            system_prompt = "You are a friendly assistant. Respond to greetings naturally and warmly."
            user_prompt = query
        elif query_type == "calculation":
            system_prompt = "You are a helpful calculator. Solve the math problem accurately."
            user_prompt = query
        else:
            system_prompt = """You are a helpful assistant that answers questions accurately.

Rules:
- Use the provided context if available
- If context doesn't have the answer, say so politely
- Be concise and accurate
- Cite sources when using context (e.g., "According to Doc 1...")
"""
            user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        # Generate answer
        response = self.groq_client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        return {
            **state,
            "answer": answer
        }

    # =========================================
    # ROUTING LOGIC
    # =========================================

    def route_after_analysis(self, state: AgentState) -> str:
        """
        Conditional routing after query analysis
        Decides which node to visit next
        """
        if state["needs_retrieval"]:
            return "retrieve"
        elif state["needs_web_search"]:
            return "web_search"
        else:
            return "generate"

    def route_after_quality_check(self, state: AgentState) -> str:
        """
        Route after quality check
        """
        # If we have good docs, generate
        # Otherwise, might retry or use LLM directly
        return "generate"

    # =========================================
    # WORKFLOW BUILDER
    # =========================================

    def _build_workflow(self) -> StateGraph:
        """
        Build the agentic workflow graph
        """
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze", self.analyze_query)
        workflow.add_node("retrieve", self.retrieve_documents)
        workflow.add_node("web_search", self.web_search)
        workflow.add_node("quality_check", self.check_quality)
        workflow.add_node("generate", self.generate_answer)

        # Set entry point
        workflow.set_entry_point("analyze")

        # Add conditional routing from analyze
        workflow.add_conditional_edges(
            "analyze",
            self.route_after_analysis,
            {
                "retrieve": "retrieve",
                "web_search": "web_search",
                "generate": "generate"
            }
        )

        # From retrieve -> quality check -> generate
        workflow.add_edge("retrieve", "quality_check")
        workflow.add_conditional_edges(
            "quality_check",
            self.route_after_quality_check,
            {
                "generate": "generate"
            }
        )

        # From web_search -> generate
        workflow.add_edge("web_search", "generate")

        # From generate -> END
        workflow.add_edge("generate", END)

        return workflow.compile()

    # =========================================
    # PUBLIC METHODS
    # =========================================

    def add_documents(self, documents: List[str], metadata: List[dict] = None):
        """Add documents to knowledge base"""
        start_id = self.collection.count()
        ids = [f"doc_{start_id + i}" for i in range(len(documents))]

        embeddings = self.embedding_model.encode(
            documents,
            normalize_embeddings=True
        )

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

        print(f"Added {len(documents)} documents. Total: {self.collection.count()}")

    def ask(self, query: str, verbose: bool = True) -> dict:
        """
        Ask a question and get intelligent answer

        Returns full state including reasoning
        """
        # Initial state
        initial_state = {
            "query": query,
            "query_type": "",
            "needs_retrieval": False,
            "needs_web_search": False,
            "retrieved_docs": [],
            "web_results": [],
            "answer": "",
            "confidence": 0.0,
            "reasoning": "",
            "iteration": 0
        }

        # Run workflow
        result = self.workflow.invoke(initial_state)

        if verbose:
            print(f"\nQuery: {query}")
            print(f"Type: {result['query_type']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"\nAnswer: {result['answer']}")

            if result.get('retrieved_docs'):
                print(f"\nUsed {len(result['retrieved_docs'])} documents from knowledge base")

        return result

    def get_stats(self):
        """Get system statistics"""
        return {
            "total_documents": self.collection.count(),
            "embedding_model": "BAAI/bge-base-en-v1.5",
            "llm_model": self.llm_model
        }


# =========================================
# DEMO USAGE
# =========================================

if __name__ == "__main__":
    # Initialize system
    rag = AgenticRAG()

    # Add some knowledge
    knowledge = [
        "LangGraph is a library for building stateful, multi-actor applications with LLMs. It's built on top of LangChain and adds the ability to create cyclical graphs for agent workflows.",
        "Agentic RAG combines retrieval-augmented generation with autonomous agents that make intelligent decisions about when and how to retrieve information.",
        "The difference between simple RAG and agentic RAG is that simple RAG always retrieves from the database, while agentic RAG decides when retrieval is necessary.",
        "Groq provides ultra-fast LLM inference using custom hardware called LPU (Language Processing Unit), achieving speeds up to 500 tokens per second.",
        "ChromaDB is an open-source vector database designed for AI applications, supporting similarity search and metadata filtering."
    ]

    metadata = [
        {"topic": "LangGraph", "category": "Tools"},
        {"topic": "Agentic RAG", "category": "AI Architecture"},
        {"topic": "RAG Comparison", "category": "AI Architecture"},
        {"topic": "Groq", "category": "LLM Infrastructure"},
        {"topic": "ChromaDB", "category": "Vector DB"}
    ]

    if rag.collection.count() == 0:
        rag.add_documents(knowledge, metadata)

    print("\n" + "=" * 60)
    print("AGENTIC RAG SYSTEM - DEMO")
    print("=" * 60)

    # Test different query types
    test_queries = [
        "Hello! How are you today?",                          # Greeting
        "What is LangGraph?",                                 # Factual (needs retrieval)
        "What's the difference between RAG and agentic RAG?", # Factual
        "What is 25 * 17?",                                   # Calculation
        "Tell me about Python programming",                   # General knowledge
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        result = rag.ask(query, verbose=True)
        print("=" * 60)

    # Show stats
    print(f"\nSystem Stats: {rag.get_stats()}")