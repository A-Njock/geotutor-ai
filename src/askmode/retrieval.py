"""Hybrid retriever for Ask mode.

Pipeline per query:
1. expand the query with the geotech glossary (su -> undrained shear strength, ...)
2. vector search (Chroma, bge-small) + keyword search (SQLite FTS5, BM25)
3. reciprocal-rank fusion, with a light boost for preferred document types
4. cross-encoder rerank of the fused candidates
5. group winning children under their parent sections and compute each
   parent's contribution weight -> the answer's "strata"
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .glossary import expand_query

BASE = Path(__file__).resolve().parents[2]
# DATA_DIR env overrides for deployments where the index lives on a volume
DATA = Path(os.environ["DATA_DIR"]) if os.environ.get("DATA_DIR") \
    else BASE / "data"
CHROMA_DIR = DATA / "chroma"
SQLITE_PATH = DATA / "tdg_text.sqlite"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
COLLECTION = "tdg_children"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

N_DENSE = 40
N_SPARSE = 40
N_RERANK = 30
RRF_K = 60
TYPE_BOOST = 1.2
EXCLUDED_TYPES = {"exam"}       # never used as evidence (user decision)
MAX_CHILDREN_PER_DOC = 6        # diversity: stop one book from filling every slot

_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "for", "and", "or", "to", "is", "are",
    "what", "how", "why", "when", "which", "does", "do", "can", "with", "under",
    "between", "about", "explain", "define", "describe", "give", "its", "it",
}


@dataclass
class Stratum:
    n: int
    parent_id: int
    doc_id: int
    rel_path: str
    title: str
    doc_type: str
    topic: str
    authors: str | None
    year: int | None
    section_path: str
    weight: float
    excerpt: str
    parent_text: str

    def label(self) -> str:
        bits = [self.title]
        if self.authors and self.year:
            bits.append(f"{self.authors} ({self.year})")
        if self.section_path:
            bits.append(self.section_path)
        return " · ".join(bits)


class HybridRetriever:
    def __init__(self) -> None:
        import chromadb
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBED_MODEL)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"}
        )
        self.con = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        self._reranker = None
        print(f"[askmode] retriever ready: {self.collection.count()} vectors")

    # -- helpers -----------------------------------------------------------

    def _rerank(self, query: str, pairs: list[tuple[int, str]]) -> list[tuple[int, float]]:
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(RERANK_MODEL)
        scores = self._reranker.predict([(query, text) for _, text in pairs])
        ranked = sorted(zip((cid for cid, _ in pairs), scores),
                        key=lambda x: x[1], reverse=True)
        return [(cid, float(s)) for cid, s in ranked]

    def _fts_query(self, query: str, expansions: list[str]) -> str:
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9']+", query)
                 if w.lower() not in _STOPWORDS and len(w) > 1]
        terms = [f'"{w}"' for w in words]
        for phrase in expansions:
            terms.append('"' + phrase.replace('"', "") + '"')
        return " OR ".join(terms) if terms else '""'

    def _sparse(self, query: str, expansions: list[str]) -> list[int]:
        try:
            rows = self.con.execute(
                "SELECT rowid FROM children_fts WHERE children_fts MATCH ? "
                "ORDER BY bm25(children_fts) LIMIT ?",
                (self._fts_query(query, expansions), N_SPARSE),
            ).fetchall()
            return [r[0] for r in rows]
        except sqlite3.OperationalError:
            return []

    def _dense(self, query: str, expansions: list[str]) -> list[int]:
        enriched = query if not expansions else f"{query} ({'; '.join(expansions)})"
        vec = self.model.encode([QUERY_PREFIX + enriched], normalize_embeddings=True)
        res = self.collection.query(query_embeddings=vec.tolist(), n_results=N_DENSE)
        return [int(i) for i in res["ids"][0]] if res["ids"] else []

    # -- main entry --------------------------------------------------------

    def search(self, query: str, k_parents: int = 5,
               preferred_types: list[str] | None = None) -> list[Stratum]:
        expansions = expand_query(query)
        dense = self._dense(query, expansions)
        sparse = self._sparse(query, expansions)
        if not dense and not sparse:
            return []

        # reciprocal-rank fusion
        fused: dict[int, float] = {}
        for rank, cid in enumerate(dense):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank)
        for rank, cid in enumerate(sparse):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank)

        fused_sorted = sorted(fused, key=fused.get, reverse=True)
        rows = self._children(fused_sorted[: N_RERANK * 3])
        if preferred_types:
            for cid, r in rows.items():
                if r["doc_type"] in preferred_types:
                    fused[cid] *= TYPE_BOOST
            fused_sorted = sorted((c for c in fused_sorted if c in rows),
                                  key=fused.get, reverse=True)

        # drop excluded types; cap children per document so several distinct
        # documents reach the reranker instead of one book filling every slot
        candidates: list[int] = []
        per_doc: dict[int, int] = {}
        for cid in fused_sorted:
            r = rows.get(cid)
            if not r or r["doc_type"] in EXCLUDED_TYPES:
                continue
            if per_doc.get(r["doc_id"], 0) >= MAX_CHILDREN_PER_DOC:
                continue
            per_doc[r["doc_id"]] = per_doc.get(r["doc_id"], 0) + 1
            candidates.append(cid)
            if len(candidates) >= N_RERANK:
                break

        pairs = [(cid, rows[cid]["text"]) for cid in candidates]
        reranked = self._rerank(query, pairs)

        # group by parent; a parent's weight = sum of its children's positive scores
        by_parent: dict[int, float] = {}
        best_child: dict[int, tuple[float, str]] = {}
        for cid, score in reranked:
            pid = rows[cid]["parent_id"]
            s = max(score, 0.0) + 0.01  # keep order even when all scores negative
            by_parent[pid] = by_parent.get(pid, 0.0) + s
            if pid not in best_child or score > best_child[pid][0]:
                best_child[pid] = (score, rows[cid]["text"])

        top_parents = sorted(by_parent, key=by_parent.get, reverse=True)[:k_parents]
        total = sum(by_parent[p] for p in top_parents) or 1.0

        strata: list[Stratum] = []
        for n, pid in enumerate(top_parents, 1):
            info = self._parent(pid)
            strata.append(Stratum(
                n=n, parent_id=pid, doc_id=info["doc_id"], rel_path=info["rel_path"],
                title=info["title"], doc_type=info["doc_type"], topic=info["topic"],
                authors=info["authors"], year=info["year"],
                section_path=info["section_path"],
                weight=round(by_parent[pid] / total, 3),
                excerpt=best_child[pid][1][:600],
                parent_text=info["text"],
            ))
        return strata

    # -- sqlite lookups ----------------------------------------------------

    def _children(self, ids: list[int]) -> dict[int, dict]:
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        rows = self.con.execute(
            f"SELECT c.id, c.parent_id, c.text, d.doc_type, c.doc_id FROM children c "
            f"JOIN docs d ON d.id = c.doc_id WHERE c.id IN ({marks})", ids
        ).fetchall()
        return {r[0]: {"parent_id": r[1], "text": r[2], "doc_type": r[3],
                       "doc_id": r[4]} for r in rows}

    def _parent(self, pid: int) -> dict:
        r = self.con.execute(
            "SELECT p.doc_id, p.section_path, p.text, d.rel_path, d.title, "
            "d.doc_type, d.topic, d.authors, d.year "
            "FROM parents p JOIN docs d ON d.id = p.doc_id WHERE p.id = ?", (pid,)
        ).fetchone()
        return {
            "doc_id": r[0], "section_path": r[1], "text": r[2], "rel_path": r[3],
            "title": r[4], "doc_type": r[5], "topic": r[6], "authors": r[7], "year": r[8],
        }


_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    elif _retriever.collection.count() == 0:
        # the index may have arrived after an early empty initialisation
        # (e.g. a query raced the volume download at boot): retry once per
        # call instead of caching emptiness for the process lifetime
        _retriever = HybridRetriever()
    return _retriever
