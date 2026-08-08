"""
Enhanced PDF Ingestion Pipeline for GeoTutor
Features:
- OCR support for scanned PDFs
- Parasite content filtering (references, index, etc.)
- Rich metadata extraction
- Sentence-aware chunking
"""
import os
import re
import glob
import uuid
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Files that require OCR (scanned documents)
OCR_REQUIRED_FILES = [
    "448254647-Six-minute-Solutions",
    "Problem Solving In Soil Mechanics -- A. Aysen",
    "Engineer Bristish columbia",
    "Engineer British columbia",
    "Engineering British Columbia",
]

# Patterns to skip (parasite content)
SKIP_PATTERNS = [
    # Table of contents, index
    r"^(table of contents|contents|index)\s*$",
    r"^\s*contents\s*$",
    r"^index\s*\d*\s*$",
    # References, bibliography
    r"^(references|bibliography|further reading)\s*$",
    r"^\d+\s*(references|bibliography)\s*$",
    # Front matter
    r"^(foreword|preface|acknowledgments?|about the author)\s*$",
    r"^(dedication|copyright|isbn)\s*",
    # Appendix indexes
    r"^appendix\s+[a-z]?\s*[-:]?\s*(index|references)",
    # Page numbers only
    r"^\s*\d+\s*$",
    # Blank or whitespace
    r"^\s*$",
]

# Patterns for chapter/section detection
CHAPTER_PATTERN = r"(?i)^(chapter\s+\d+|ch\.\s*\d+)[:\.\s]*(.*)"
SECTION_PATTERN = r"(?i)^(\d+\.\d+[\.\d]*)[:\.\s]*(.*)"

# Topic keywords for automatic tagging
TOPIC_KEYWORDS = {
    "bearing capacity": ["bearing capacity", "terzaghi", "meyerhof", "vesic", "hansen"],
    "settlement": ["settlement", "consolidation", "compression", "cv", "cc", "creep"],
    "shear strength": ["shear strength", "mohr-coulomb", "triaxial", "direct shear", "cohesion", "friction angle"],
    "lateral earth pressure": ["lateral earth", "rankine", "coulomb", "active pressure", "passive pressure", "retaining wall"],
    "slope stability": ["slope stability", "factor of safety", "bishop", "fellenius", "slip circle", "landslide"],
    "pile foundations": ["pile", "driven pile", "bored pile", "axial capacity", "lateral load"],
    "soil classification": ["uscs", "aashto", "atterberg", "liquid limit", "plastic limit", "grain size"],
    "seepage": ["seepage", "flow net", "permeability", "hydraulic gradient", "piping"],
    "compaction": ["compaction", "proctor", "optimum moisture", "dry density"],
    "effective stress": ["effective stress", "pore pressure", "total stress", "terzaghi"],
    "site investigation": ["borehole", "cpt", "spt", "site investigation", "ground investigation"],
}

@dataclass
class ChunkMetadata:
    source: str
    material_origin: str
    chapter: Optional[str]
    section: Optional[str]
    page_number: int
    topic_tags: List[str]
    content_type: str  # theory, solved_example, code_reference, exercise
    chunk_index: int


def needs_ocr(filename: str) -> bool:
    """Check if file requires OCR based on known scanned documents."""
    return any(pattern.lower() in filename.lower() for pattern in OCR_REQUIRED_FILES)


def extract_text_with_ocr(pdf_path: str) -> str:
    """Extract text using OCR for scanned PDFs."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
        
        print(f"    [OCR] Processing {os.path.basename(pdf_path)}...")
        pages = convert_from_path(pdf_path, dpi=200)
        
        full_text = ""
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page, lang='eng')
            full_text += f"\n--- Page {i+1} ---\n{text}"
            if (i + 1) % 10 == 0:
                print(f"    [OCR] Processed {i+1}/{len(pages)} pages...")
        
        return full_text
    except ImportError as e:
        print(f"    [WARN] OCR dependencies not installed: {e}")
        print(f"    [WARN] Falling back to standard extraction...")
        return extract_text_standard(pdf_path)
    except Exception as e:
        print(f"    [ERROR] OCR failed: {e}")
        return extract_text_standard(pdf_path)


def extract_text_standard(pdf_path: str) -> str:
    """Standard text extraction using PyMuPDF."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n--- Page {page_num + 1} ---\n{text}"
    return full_text


def is_parasite_content(text: str) -> bool:
    """Check if text chunk is parasite content to skip."""
    text_lower = text.strip().lower()
    
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
            return True
    
    # Skip if mostly numbers or too short
    if len(text.strip()) < 50:
        return True
    
    # Skip if high ratio of numbers/special chars (likely index or TOC)
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count < len(text) * 0.3:
        return True
    
    return False


def infer_origin(filename: str) -> str:
    """Infers the material origin type from the filename."""
    fn = filename.lower()
    
    if any(x in fn for x in ["eurocode", "astm", "bs en", "code", "standard", "as 1726"]):
        return "Design Code"
    if any(x in fn for x in ["solved", "problem", "exercise", "100 solved", "300 solved"]):
        return "Solved Problems"
    if any(x in fn for x in ["exam", "cse", "pe exam", "ncees", "british columbia", "engineer"]):
        return "Exam/Exercise"
    if any(x in fn for x in ["book", "textbook", "manual", "handbook", "mechanics", "edition", "'s_"]):
        return "Book/Textbook"
    if any(x in fn for x in ["borelog", "cpt", "report", "project", "investigation"]):
        return "Project Data"
    if any(x in fn for x in ["glossary", "terms", "symbols"]):
        return "Reference/Glossary"
    
    return "General Reference"


def detect_content_type(text: str) -> str:
    """Detect if content is theory, example, code reference, or exercise."""
    text_lower = text.lower()
    
    if any(x in text_lower for x in ["example", "solution:", "solve:", "calculate:", "given:", "find:"]):
        return "solved_example"
    if any(x in text_lower for x in ["exercise", "problem", "question", "quiz"]):
        return "exercise"
    if any(x in text_lower for x in ["shall", "must", "clause", "section", "accordance with"]):
        return "code_reference"
    
    return "theory"


def extract_topic_tags(text: str) -> List[str]:
    """Extract topic tags based on keyword matching."""
    text_lower = text.lower()
    tags = []
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(topic)
    
    return tags[:5]  # Max 5 tags


def extract_chapter_section(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract chapter and section from text."""
    chapter = None
    section = None
    
    # Check first few lines for chapter/section headers
    lines = text.split('\n')[:10]
    for line in lines:
        chapter_match = re.match(CHAPTER_PATTERN, line.strip())
        if chapter_match:
            chapter = chapter_match.group(0)[:100]  # Limit length
        
        section_match = re.match(SECTION_PATTERN, line.strip())
        if section_match:
            section = section_match.group(0)[:100]
    
    return chapter, section


def extract_page_number(text: str) -> int:
    """Extract page number from text if present."""
    match = re.search(r"--- Page (\d+) ---", text)
    if match:
        return int(match.group(1))
    return 0


def smart_chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Tuple[str, int]]:
    """
    Smart chunking that respects sentence boundaries and tracks page numbers.
    Returns list of (chunk_text, page_number) tuples.
    """
    chunks = []
    
    # Split by page markers first
    pages = re.split(r"--- Page (\d+) ---", text)
    
    current_page = 1
    accumulated_text = ""
    
    for i, segment in enumerate(pages):
        # Even indices are text, odd indices are page numbers
        if i % 2 == 1:
            current_page = int(segment)
            continue
        
        if not segment.strip():
            continue
        
        accumulated_text += segment
        
        # Chunk when we have enough text
        while len(accumulated_text) >= chunk_size:
            # Find a good break point (sentence end or paragraph)
            break_point = chunk_size
            
            # Look for sentence end
            for end_marker in ['. ', '.\n', '? ', '!\n', '\n\n']:
                pos = accumulated_text.rfind(end_marker, chunk_size // 2, chunk_size + 100)
                if pos != -1:
                    break_point = pos + len(end_marker)
                    break
            
            chunk = accumulated_text[:break_point].strip()
            if chunk and not is_parasite_content(chunk):
                chunks.append((chunk, current_page))
            
            accumulated_text = accumulated_text[break_point - overlap:]
    
    # Don't forget remaining text
    if accumulated_text.strip() and not is_parasite_content(accumulated_text):
        chunks.append((accumulated_text.strip(), current_page))
    
    return chunks


class SentenceTransformerEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Real embedding function using sentence-transformers."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()


def main():
    pdf_dir = "PDF_database"
    
    if not os.path.exists(pdf_dir):
        if os.path.exists("../PDF_database"):
            pdf_dir = "../PDF_database"
        else:
            print(f"Directory {pdf_dir} not found.")
            return

    print("=" * 60)
    print("GeoTutor Enhanced Ingestion Pipeline")
    print("=" * 60)
    
    # Clear old database
    db_path = "./chroma_db"
    if os.path.exists(db_path):
        import shutil
        print(f"Clearing old database at {db_path}...")
        shutil.rmtree(db_path)
    
    print("Initializing ChromaDB client...")
    client = chromadb.PersistentClient(path=db_path)
    
    print("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
    ef = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
    print("✓ Embedding model loaded successfully.")
    
    collection = client.get_or_create_collection(name="geotech_docs", embedding_function=ef)
    
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files to process.")
    print("-" * 60)
    
    all_ids = []
    all_docs = []
    all_metadatas = []
    
    total_chunks = 0
    skipped_chunks = 0
    
    for pdf_idx, pdf_path in enumerate(pdf_files):
        filename = os.path.basename(pdf_path)
        print(f"\n[{pdf_idx + 1}/{len(pdf_files)}] Processing: {filename[:60]}...")
        
        try:
            # Extract text (OCR if needed)
            if needs_ocr(filename):
                print(f"    Using OCR extraction...")
                full_text = extract_text_with_ocr(pdf_path)
            else:
                full_text = extract_text_standard(pdf_path)
            
            # Determine material origin
            origin = infer_origin(filename)
            print(f"    Origin: {origin}")
            
            # Smart chunking
            chunks = smart_chunk_text(full_text)
            print(f"    Created {len(chunks)} chunks (before filtering)")
            
            valid_chunks = 0
            for i, (chunk, page_num) in enumerate(chunks):
                # Skip parasite content
                if is_parasite_content(chunk):
                    skipped_chunks += 1
                    continue
                
                # Extract metadata
                chapter, section = extract_chapter_section(chunk)
                topic_tags = extract_topic_tags(chunk)
                content_type = detect_content_type(chunk)
                
                # Create unique ID
                chunk_id = f"{filename}_{i}_{uuid.uuid4().hex[:8]}"
                
                # Build metadata
                metadata = {
                    "source": filename,
                    "material_origin": origin,
                    "chapter": chapter or "",
                    "section": section or "",
                    "page_number": page_num,
                    "topic_tags": ",".join(topic_tags),
                    "content_type": content_type,
                    "chunk_index": i
                }
                
                all_ids.append(chunk_id)
                all_docs.append(chunk)
                all_metadatas.append(metadata)
                valid_chunks += 1
            
            total_chunks += valid_chunks
            print(f"    ✓ Added {valid_chunks} chunks (skipped {len(chunks) - valid_chunks} parasite)")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Total chunks to ingest: {len(all_docs)}")
    print(f"Skipped parasite chunks: {skipped_chunks}")
    print("=" * 60)
    
    if all_docs:
        print("\nUpserting to ChromaDB...")
        batch_size = 100
        for i in range(0, len(all_docs), batch_size):
            end = min(i + batch_size, len(all_docs))
            collection.add(
                ids=all_ids[i:end],
                documents=all_docs[i:end],
                metadatas=all_metadatas[i:end]
            )
            print(f"    Batch {i//batch_size + 1}/{(len(all_docs)-1)//batch_size + 1} complete...")
        
        print("\n" + "=" * 60)
        print("✓ INGESTION COMPLETE!")
        print(f"  Collection count: {collection.count()}")
        print("=" * 60)
    else:
        print("No documents found/processed.")


if __name__ == "__main__":
    main()
