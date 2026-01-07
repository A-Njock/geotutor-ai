try:
    print("Importing langchain_community...")
    import langchain_community
    print("Success langchain_community")
except Exception as e:
    print(f"Failed langchain_community: {e}")

try:
    print("Importing chromadb...")
    import chromadb
    print("Success chromadb")
except Exception as e:
    print(f"Failed chromadb: {e}")

try:
    print("Importing PyMuPDFLoader...")
    from langchain_community.document_loaders import PyMuPDFLoader
    print("Success PyMuPDFLoader")
except Exception as e:
    print(f"Failed PyMuPDFLoader: {e}")

try:
    print("Importing Chroma...")
    from langchain_community.vectorstores import Chroma
    print("Success Chroma")
except Exception as e:
    print(f"Failed Chroma: {e}")
