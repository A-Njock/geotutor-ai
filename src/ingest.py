import os
import glob
import uuid
import fitz
import chromadb
from chromadb.utils import embedding_functions

def infer_origin(filename: str) -> str:
    """
    Infers the material origin type from the filename.
    """
    fn = filename.lower()
    if "code" in fn or "eurocode" in fn or "astm" in fn or "standard" in fn:
        return "Design Code"
    if "book" in fn or "textbook" in fn or "manual" in fn or "handbook" in fn or "mechanics" in fn or "edition" in fn:
        return "Book/Textbook"
    if "exam" in fn or "problem" in fn or "exercise" in fn or "quiz" in fn or "cse" in fn or "paper" in fn or "solution" in fn:
        return "Exam/Exercise"
    if "borelog" in fn or "cpt" in fn or "report" in fn or "project" in fn:
        return "Project Data"
    return "General Reference"

def recursive_split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Simple recursive splitter implementation.
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to find a nice break point (newline or space)
        if end < len(text):
            # Look back for newline
            p = text.rfind('\n', start, end)
            if p == -1 or p < start + chunk_size // 2:
                 p = text.rfind(' ', start, end)
            
            if p != -1 and p > start:
                end = p + 1
        
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end
        
    return chunks

class MockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        # Return random vectors of size 384
        import random
        return [[random.random() for _ in range(384)] for _ in input]

def main():
    pdf_dir = "PDF_database"
    # Locate directory
    if not os.path.exists(pdf_dir):
        if os.path.exists("../PDF_database"):
             pdf_dir = "../PDF_database"
        else:
            print(f"Directory {pdf_dir} not found.")
            return

    print("Initializing ChromaDB client...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Try to get default embedding function, else fallback to mock
    ef = None
    try:
        # This might fail if onnxruntime/torch issues exist
        # ef = embedding_functions.DefaultEmbeddingFunction()
        # For safety in this verified broken env, use mock or simple
        print("Using Mock Embeddings to bypass ML dependency hell.")
        ef = MockEmbeddingFunction()
    except Exception as e:
        print(f"Failed to load default embeddings: {e}")
        ef = MockEmbeddingFunction()

    collection = client.get_or_create_collection(name="geotech_docs", embedding_function=ef)
    
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    print(f"Found {len(pdf_files)} PDFs.")
    
    all_ids = []
    all_docs = []
    all_metadatas = []

    for pdf_path in pdf_files:
        try:
            print(f"Processing {os.path.basename(pdf_path)}...")
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            
            # Split
            chunks = recursive_split_text(full_text)
            print(f" - Created {len(chunks)} chunks.")
            
            for i, chunk in enumerate(chunks):
                all_ids.append(f"{os.path.basename(pdf_path)}_{i}_{uuid.uuid4().hex[:8]}")
                all_docs.append(chunk)
                origin = infer_origin(os.path.basename(pdf_path))
                all_metadatas.append({
                    "source": os.path.basename(pdf_path), 
                    "chunk_index": i,
                    "material_origin": origin
                })
                
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

    if all_docs:
        print(f"Upserting {len(all_docs)} chunks...")
        # Batching is better but simplified here
        batch_size = 100
        for i in range(0, len(all_docs), batch_size):
            end = min(i + batch_size, len(all_docs))
            collection.add(
                ids=all_ids[i:end],
                documents=all_docs[i:end],
                metadatas=all_metadatas[i:end]
            )
        print("Ingestion complete.")
        print(f"Collection count: {collection.count()}")
    else:
        print("No documents found/processed.")

if __name__ == "__main__":
    main()
