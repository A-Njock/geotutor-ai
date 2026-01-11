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
# Configuration - Cloudflare R2 Public URL
CHROMADB_URL = "https://pub-0e7a2751c3a94d1298717489b3f15361.r2.dev/chroma_db.zip"
# Use Railway volume path if available, or default to local directory
CHROMA_DB_PATH = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "./chroma_db")


def download_and_extract_chromadb():
    """Download chroma_db.zip from Cloudflare R2 and extract it."""
    db_path = Path(CHROMA_DB_PATH)
    sqlite_file = db_path / "chroma.sqlite3"
    
    # Check if database looks valid by trying to find the collection
    is_valid = False
    if sqlite_file.exists():
        try:
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            # Try to get the specific collection we need
            client.get_collection("geotech_docs")
            print(f"[ChromaDB] Valid database and 'geotech_docs' collection found at {CHROMA_DB_PATH}, skipping download.")
            is_valid = True
        except Exception as e:
            print(f"[ChromaDB] Database at {CHROMA_DB_PATH} is invalid or missing 'geotech_docs' collection: {e}")
            is_valid = False
    
    if is_valid:
        return True
    
    # If directory exists but is invalid, it's stale/empty. Force re-download.
    if db_path.exists():
        print(f"[ChromaDB] Path {db_path} is incomplete or invalid. Forcing re-download...")
        import shutil
        try:
            shutil.rmtree(db_path)
        except Exception as e:
            print(f"[ChromaDB] Warning: Could not remove existing dir: {e}")
    
    print(f"[ChromaDB] Database not found or invalid. Downloading from Cloudflare R2...")
    
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
    return download_and_extract_chromadb()


if __name__ == "__main__":
    # Test the download
    success = ensure_chromadb_available()
    print(f"ChromaDB available: {success}")
