"""Build the Ask-mode indexes from data/TDG_GEOTECHNICAL_DATABASE.

Produces:
- data/chroma          vector index (BAAI/bge-small-en-v1.5) of small "child" chunks
- data/tdg_text.sqlite full text: docs, parent sections, child chunks + FTS5 keyword index

Chunking is structure-aware: sections follow the Markdown heading tree, display
equations ($$...$$) are never split, children (~350 tokens) remember their
parent section (~1500 tokens). Child text lives only in SQLite; Chroma stores
just ids + vectors + a little metadata, which keeps the deployable index small.

Resumable: already-ingested files (same path + mtime) are skipped, so the job
can be interrupted and rerun.

Usage:
    python -m src.askmode.ingest --sample     # small validation subset
    python -m src.askmode.ingest              # full corpus
    python -m src.askmode.ingest --reset      # wipe indexes and start over
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
CORPUS = DATA / "TDG_GEOTECHNICAL_DATABASE"
CHROMA_DIR = DATA / "chroma"
SQLITE_PATH = DATA / "tdg_text.sqlite"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION = "tdg_children"

CHILD_TARGET_CHARS = 1400      # ~350 tokens
CHILD_MAX_CHARS = 2000
PARENT_TARGET_CHARS = 6000     # ~1500 tokens
EMBED_BATCH = 128

DOC_TYPE_BY_FOLDER = {
    "Book": "book",
    "Paper": "paper",
    "Thesis_MSc": "thesis",
    "Exams": "exam",
    "Code_Standard": "standard",
}

FILENAME_META = re.compile(r"^\d+__(?P<authors>.+?)_(?P<year>(?:19|20)\d{2})__")


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

@dataclass
class Section:
    path: str                  # e.g. "1. Elasto-plastic relations > 1.1 Hypoelastic mechanism"
    blocks: list[str] = field(default_factory=list)


def split_blocks(text: str) -> list[str]:
    """Split into paragraph blocks, keeping $$...$$ display equations whole."""
    blocks: list[str] = []
    buf: list[str] = []
    in_math = False
    for line in text.splitlines():
        stripped = line.strip()
        delim_count = stripped.count("$$")
        if in_math:
            buf.append(line)
            if delim_count % 2 == 1:
                in_math = False
            continue
        if delim_count % 2 == 1:
            # equation opens and stays open
            buf.append(line)
            in_math = True
            continue
        if not stripped:
            if buf:
                blocks.append("\n".join(buf).strip())
                buf = []
        else:
            buf.append(line)
    if buf:
        blocks.append("\n".join(buf).strip())
    return [b for b in blocks if b]


def parse_sections(text: str) -> tuple[str | None, list[Section]]:
    """Walk the heading tree; return (title, sections)."""
    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    title: str | None = None
    sections: list[Section] = [Section(path="")]
    stack: list[tuple[int, str]] = []  # (level, heading)

    body: list[str] = []

    def flush_body() -> None:
        nonlocal body
        if body:
            sections[-1].blocks.extend(split_blocks("\n".join(body)))
            body = []

    for line in text.splitlines():
        m = heading_re.match(line)
        if not m:
            body.append(line)
            continue
        level, heading = len(m.group(1)), m.group(2).strip()
        if title is None and level == 1:
            title = heading
        flush_body()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))
        sections.append(Section(path=" > ".join(h for _, h in stack)))
    flush_body()
    return title, [s for s in sections if s.blocks]


def pack(blocks: list[str], target: int, hard_max: int | None = None) -> list[str]:
    """Greedily pack blocks into pieces of roughly `target` characters."""
    pieces: list[str] = []
    buf: list[str] = []
    size = 0
    for b in blocks:
        if hard_max and len(b) > hard_max:
            # oversized single block (huge equation/paragraph): keep whole anyway
            if buf:
                pieces.append("\n\n".join(buf))
                buf, size = [], 0
            pieces.append(b)
            continue
        if buf and size + len(b) > target:
            pieces.append("\n\n".join(buf))
            buf, size = [], 0
        buf.append(b)
        size += len(b) + 2
    if buf:
        pieces.append("\n\n".join(buf))
    return pieces


def doc_metadata(md_path: Path) -> dict:
    rel = md_path.relative_to(CORPUS)
    parts = rel.parts
    doc_type = DOC_TYPE_BY_FOLDER.get(parts[0], "other")
    topic = "general"
    if len(parts) > 2:
        topic = parts[1].replace("_", " ").strip().lower()
        if topic in ("unknown", "more papers", "book more"):
            topic = "unclassified"
    authors, year = None, None
    m = FILENAME_META.match(md_path.stem)
    if m:
        authors = m.group("authors").replace("_", " ").strip()
        year = int(m.group("year"))
    return {
        "rel_path": str(rel).replace("\\", "/"),
        "doc_type": doc_type,
        "topic": topic,
        "authors": authors,
        "year": year,
    }


# --------------------------------------------------------------------------
# storage
# --------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    id INTEGER PRIMARY KEY,
    rel_path TEXT UNIQUE NOT NULL,
    mtime REAL NOT NULL,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    topic TEXT NOT NULL,
    authors TEXT,
    year INTEGER
);
CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES docs(id),
    section_path TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS children (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES parents(id),
    doc_id INTEGER NOT NULL REFERENCES docs(id),
    text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_children_parent ON children(parent_id);
CREATE INDEX IF NOT EXISTS idx_parents_doc ON parents(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS children_fts USING fts5(
    text,
    content='children',
    content_rowid='id',
    tokenize='porter unicode61'
);
"""


def connect() -> sqlite3.Connection:
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(SQLITE_PATH)
    con.executescript(SCHEMA)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def ingest_file(con: sqlite3.Connection, md_path: Path) -> list[tuple[int, str]]:
    """Parse one file into the DB. Returns [(child_id, child_text_for_embedding)]."""
    meta = doc_metadata(md_path)
    text = md_path.read_text(encoding="utf-8", errors="replace")
    title, sections = parse_sections(text)
    if not title:
        title = re.sub(r"^\d+_*", "", md_path.stem).replace("_", " ").strip() or md_path.stem
    if not sections:
        blocks = split_blocks(text)
        if not blocks:
            return []
        sections = [Section(path="", blocks=blocks)]

    cur = con.execute(
        "INSERT INTO docs (rel_path, mtime, title, doc_type, topic, authors, year) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (meta["rel_path"], md_path.stat().st_mtime, title, meta["doc_type"],
         meta["topic"], meta["authors"], meta["year"]),
    )
    doc_id = cur.lastrowid

    out: list[tuple[int, str]] = []
    for sec in sections:
        for parent_text in pack(sec.blocks, PARENT_TARGET_CHARS):
            cur = con.execute(
                "INSERT INTO parents (doc_id, section_path, text) VALUES (?, ?, ?)",
                (doc_id, sec.path, parent_text),
            )
            parent_id = cur.lastrowid
            for child_text in pack(split_blocks(parent_text), CHILD_TARGET_CHARS, CHILD_MAX_CHARS):
                cur = con.execute(
                    "INSERT INTO children (parent_id, doc_id, text) VALUES (?, ?, ?)",
                    (parent_id, doc_id, child_text),
                )
                con.execute(
                    "INSERT INTO children_fts (rowid, text) VALUES (?, ?)",
                    (cur.lastrowid, child_text),
                )
                # embedding input: prefix with title + section so the vector
                # carries document context (cheap contextual retrieval)
                prefix = title if not sec.path else f"{title} — {sec.path}"
                out.append((cur.lastrowid, f"{prefix}\n{child_text}"))
    return out


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def select_files(sample: bool, limit: int | None) -> list[Path]:
    if sample:
        files: list[Path] = []
        files += sorted((CORPUS / "Code_Standard").rglob("*.md"))
        files += sorted((CORPUS / "Exams").rglob("*.md"))
        files += sorted((CORPUS / "Book" / "Geotechnical_Engineering").rglob("*.md"))[:8]
        files += sorted((CORPUS / "Paper" / "Soil_Mechanics").rglob("*.md"))[:20]
        return files
    files = sorted(CORPUS.rglob("*.md"))
    return files[:limit] if limit else files


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="small validation subset")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--reset", action="store_true", help="wipe indexes first")
    args = ap.parse_args()

    if args.reset:
        import shutil
        if SQLITE_PATH.exists():
            SQLITE_PATH.unlink()
        for suffix in ("-wal", "-shm"):
            p = Path(str(SQLITE_PATH) + suffix)
            if p.exists():
                p.unlink()
        if CHROMA_DIR.exists():
            for item in CHROMA_DIR.iterdir():
                if item.name == ".gitkeep":
                    continue
                shutil.rmtree(item) if item.is_dir() else item.unlink()
        print("[ingest] indexes wiped")

    import chromadb
    from sentence_transformers import SentenceTransformer

    print(f"[ingest] loading embedding model {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    con = connect()

    done = {row[0] for row in con.execute("SELECT rel_path FROM docs")}
    files = select_files(args.sample, args.limit)
    todo = [f for f in files if str(f.relative_to(CORPUS)).replace("\\", "/") not in done]
    print(f"[ingest] {len(files)} files selected, {len(files) - len(todo)} already done, "
          f"{len(todo)} to ingest")

    pending: list[tuple[int, str]] = []
    t0 = time.time()
    n_children = 0

    def flush() -> None:
        nonlocal pending, n_children
        if not pending:
            return
        ids = [str(cid) for cid, _ in pending]
        texts = [t for _, t in pending]
        vecs = model.encode(texts, batch_size=EMBED_BATCH, normalize_embeddings=True,
                            show_progress_bar=False)
        collection.add(ids=ids, embeddings=vecs.tolist())
        n_children += len(pending)
        pending = []
        con.commit()

    for i, f in enumerate(todo, 1):
        try:
            pending.extend(ingest_file(con, f))
        except Exception as exc:  # keep the job alive on a single bad file
            print(f"[ingest] FAILED {f.name}: {exc}")
            con.rollback()
            continue
        if len(pending) >= 1024:
            flush()
        if i % 100 == 0 or i == len(todo):
            rate = i / max(time.time() - t0, 1)
            eta_min = (len(todo) - i) / max(rate, 0.01) / 60
            print(f"[ingest] {i}/{len(todo)} files | {n_children + len(pending)} chunks | "
                  f"{rate:.1f} files/s | ETA {eta_min:.0f} min", flush=True)
    flush()

    total_children = con.execute("SELECT count(*) FROM children").fetchone()[0]
    total_parents = con.execute("SELECT count(*) FROM parents").fetchone()[0]
    total_docs = con.execute("SELECT count(*) FROM docs").fetchone()[0]
    print(f"[ingest] DONE: {total_docs} docs, {total_parents} parents, "
          f"{total_children} children, chroma count {collection.count()}")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
