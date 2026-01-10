"""
ChromaDB Download Utility
Downloads and extracts the ChromaDB database from Cloudflare R2 on startup.
This avoids storing the large database in the Git repository.
"""
import os
import zipfile
import requests
from pathlib import Path

# Configuration - Cloudflare R2 Public URL
CHROMADB_URL = "https://pub-0e7a2751c3a94d129871749b3f15361.r2.dev/chroma_db.zip"
CHROMA_DB_PATH = "./chroma_db"


def download_and_extract_chromadb():
    """Download chroma_db.zip from Cloudflare R2 and extract it."""
    db_path = Path(CHROMA_DB_PATH)
    
    # Skip if already exists
    if db_path.exists() and any(db_path.iterdir()):
        print(f"[ChromaDB] Database already exists at {CHROMA_DB_PATH}, skipping download.")
        return True
    
    print(f"[ChromaDB] Database not found. Downloading from Cloudflare R2...")
    
    try:
        print(f"[ChromaDB] Downloading from: {CHROMADB_URL}")
        
        # Download the zip file
        zip_path = Path("chroma_db_temp.zip")
        response = requests.get(CHROMADB_URL, stream=True, timeout=600)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r[ChromaDB] Downloading: {percent:.1f}%", end="", flush=True)
        
        print(f"\n[ChromaDB] Download complete. Extracting...")
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Clean up
        zip_path.unlink()
        
        print(f"[ChromaDB] Extraction complete. Database ready at {CHROMA_DB_PATH}")
        return True
        
    except Exception as e:
        print(f"[ChromaDB] ERROR: Failed to download database: {e}")
        return False


def ensure_chromadb_available():
    """Ensure ChromaDB is available, downloading if necessary."""
    db_path = Path(CHROMA_DB_PATH)
    
    if not db_path.exists() or not any(db_path.iterdir()):
        return download_and_extract_chromadb()
    
    return True


if __name__ == "__main__":
    # Test the download
    success = ensure_chromadb_available()
    print(f"ChromaDB available: {success}")
