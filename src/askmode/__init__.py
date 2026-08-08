"""Ask mode (Mode 1): grounded question-answering over the TDG library.

Components:
- ingest.py     one-time index build (vectors + keyword index) from data/TDG_GEOTECHNICAL_DATABASE
- glossary.py   geotechnical symbol/synonym dictionary used for query expansion
- retrieval.py  hybrid retriever (Chroma vectors + SQLite FTS5, fused, reranked)
- brain.py      DeepSeek query analyst + answerer returning the structured answer contract
"""
