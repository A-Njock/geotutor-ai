"""
Enhanced Librarian Agent with Reranking
Features:
- Sentence-transformer embeddings
- Cross-encoder reranking (Cohere-style)
- Rich metadata formatting
- Contextual retrieval with source citations
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional


class SentenceTransformerEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Real embedding function using sentence-transformers."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()


class LibrarianAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use real sentence-transformer embeddings
        self.ef = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        
        # Initialize reranker (lazy load)
        self.reranker = None
        
        try:
            self.collection = self.client.get_collection(name="geotech_docs", embedding_function=self.ef)
            print(f"[Librarian] Connected to collection with {self.collection.count()} documents")
        except Exception as e:
            print(f"[Librarian] Warning: Could not get collection. {e}")
            self.collection = None
    
    def _get_reranker(self):
        """Lazy load reranker to avoid startup delay."""
        if self.reranker is None:
            try:
                from ..tools.reranker import Reranker
                self.reranker = Reranker()
            except Exception as e:
                print(f"[Librarian] Reranker not available: {e}")
        return self.reranker
    
    def _format_context(self, documents: List[str], metadatas: List[dict], scores: Optional[List[float]] = None) -> str:
        """Format retrieved documents with rich metadata for LLM consumption."""
        formatted_parts = []
        
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            # Extract metadata
            source = meta.get("source", "Unknown")
            origin = meta.get("material_origin", "")
            chapter = meta.get("chapter", "")
            section = meta.get("section", "")
            page = meta.get("page_number", "")
            content_type = meta.get("content_type", "")
            topic_tags = meta.get("topic_tags", "")
            
            # Limit source name to 40 chars for readability
            short_source = source[:40] + "..." if len(source) > 40 else source
            
            # Create structured header - source LAST for better readability
            header_parts = []
            if origin:
                header_parts.append(f"Type: {origin}")
            if content_type:
                header_parts.append(f"Content: {content_type}")
            if chapter:
                header_parts.append(f"Chapter: {chapter[:50]}")
            if page:
                header_parts.append(f"Page: {page}")
            # Source last
            header_parts.append(f"Source: {short_source}")
            
            header = "[" + " | ".join(header_parts) + "]"
            
            # Add relevance score if available
            if scores and i < len(scores):
                header += f" (Relevance: {scores[i]:.3f})"
            
            # Add topic tags if present
            if topic_tags:
                header += f"\nTopics: {topic_tags}"
            
            formatted_parts.append(f"{header}\n{doc}")
        
        return "\n\n---\n\n".join(formatted_parts)

    def retrieve(self, query: str, k: int = 5, use_rerank: bool = True) -> str:
        """
        Retrieve relevant documents with optional reranking.
        
        Args:
            query: Search query
            k: Number of final results to return
            use_rerank: Whether to apply cross-encoder reranking
            
        Returns:
            Formatted context string with source citations
        """
        if not self.collection:
            return "No documents available (Collection not found)."
        
        try:
            # Step 1: Initial vector search (get more candidates for reranking)
            n_candidates = k * 4 if use_rerank else k
            results = self.collection.query(
                query_texts=[query],
                n_results=n_candidates
            )
            
            if not results['documents'] or not results['documents'][0]:
                return "No relevant documents found."
            
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
            
            # Step 2: Rerank with cross-encoder (if enabled)
            if use_rerank and len(documents) > k:
                reranker = self._get_reranker()
                if reranker:
                    print(f"[Librarian] Reranking {len(documents)} candidates...")
                    rerank_results = reranker.rerank(query, documents, metadatas, top_k=k)
                    
                    # Extract reranked documents, metadatas, and scores
                    documents = [r.document for r in rerank_results]
                    metadatas = [r.metadata or {} for r in rerank_results]
                    scores = [r.score for r in rerank_results]
                    
                    print(f"[Librarian] Top result score: {scores[0]:.3f}")
                    return self._format_context(documents, metadatas, scores)
            
            # Fallback: use top-k without reranking
            return self._format_context(documents[:k], metadatas[:k])
            
        except Exception as e:
            return f"Error during retrieval: {e}"

    def answer(self, query: str) -> str:
        """Answer a question using retrieved context."""
        context = self.retrieve(query)
        
        template = """You are The Librarian, a geotechnical research assistant.
        Answer the user's question strictly based on the following context.
        If the answer is not in the context, say "I cannot find this information in the available documents."
        Include citations (Source X, Page Y) in your answer.

        Context:
        {context}

        Question: {question}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"context": context, "question": query})


if __name__ == "__main__":
    # Test retrieval
    try:
        lib = LibrarianAgent()
        print("\nTesting retrieval...")
        result = lib.retrieve("bearing capacity of shallow foundation")
        print(result[:1000])
    except Exception as e:
        print(f"Librarian init failed: {e}")
