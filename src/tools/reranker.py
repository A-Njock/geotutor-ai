"""
Cohere-style Reranker using Cross-Encoder
Improves retrieval by rescoring initial search results with a more powerful model.
"""
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RerankResult:
    """Result from reranking operation."""
    document: str
    score: float
    original_index: int
    metadata: Optional[dict] = None


class Reranker:
    """
    Cross-encoder reranker for improving retrieval quality.
    Uses ms-marco-MiniLM-L-6-v2 which is optimized for passage ranking.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the reranker with a cross-encoder model.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        from sentence_transformers import CrossEncoder
        print(f"[Reranker] Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        self.model_name = model_name
        print("[Reranker] Model loaded successfully.")
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        metadatas: Optional[List[dict]] = None,
        top_k: int = 5
    ) -> List[RerankResult]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to rerank
            metadatas: Optional list of metadata dicts for each document
            top_k: Number of top results to return
            
        Returns:
            List of RerankResult sorted by relevance score (descending)
        """
        if not documents:
            return []
        
        # Create (query, document) pairs for the cross-encoder
        pairs = [[query, doc] for doc in documents]
        
        # Score all pairs
        scores = self.model.predict(pairs)
        
        # Create results with scores and original indices
        results = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else None
            results.append(RerankResult(
                document=doc,
                score=float(score),
                original_index=i,
                metadata=metadata
            ))
        
        # Sort by score (descending) and take top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def rerank_with_threshold(
        self, 
        query: str, 
        documents: List[str],
        metadatas: Optional[List[dict]] = None,
        threshold: float = 0.0,
        top_k: int = 10
    ) -> List[RerankResult]:
        """
        Rerank and filter by minimum relevance threshold.
        
        Args:
            query: The search query
            documents: List of document texts
            metadatas: Optional metadata list
            threshold: Minimum score to include in results
            top_k: Maximum number of results
            
        Returns:
            List of RerankResult above threshold
        """
        results = self.rerank(query, documents, metadatas, top_k=len(documents))
        return [r for r in results[:top_k] if r.score >= threshold]


# Singleton instance for lazy loading
_reranker_instance: Optional[Reranker] = None

def get_reranker() -> Optional[Reranker]:
    """Get or create the global reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        try:
            _reranker_instance = Reranker()
        except Exception as e:
            print(f"[WARN] Failed to initialize reranker: {e}")
            return None
    return _reranker_instance


if __name__ == "__main__":
    # Test the reranker
    reranker = Reranker()
    
    query = "What is the bearing capacity of a shallow foundation?"
    
    documents = [
        "The bearing capacity of soil refers to the ability of soil to support loads without failure.",
        "Chapter 5 discusses consolidation theory and time-dependent settlement.",
        "Terzaghi's bearing capacity equation: qu = cNc + qNq + 0.5γBNγ",
        "Slope stability analysis using Bishop's simplified method.",
        "For shallow foundations, Meyerhof's equation provides bearing capacity factors.",
    ]
    
    results = reranker.rerank(query, documents, top_k=3)
    
    print("\nReranking Results:")
    print("-" * 60)
    for i, result in enumerate(results):
        print(f"{i+1}. Score: {result.score:.4f}")
        print(f"   {result.document[:80]}...")
        print()
