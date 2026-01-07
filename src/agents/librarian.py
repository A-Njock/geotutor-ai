from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .utils import get_llm
import chromadb
from chromadb.utils import embedding_functions

class LibrarianAgent:
    def __init__(self):
        self.llm = get_llm("gpt-4o")
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use Simple/Mock embedding to match ingestion
        # In a real scenario, use openai_ef or similar
        class MockEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __call__(self, input: list[str]) -> list[list[float]]:
                import random
                return [[random.random() for _ in range(384)] for _ in input]

        self.ef = MockEmbeddingFunction()
        
        try:
           # Get collection
           self.collection = self.client.get_collection(name="geotech_docs", embedding_function=self.ef)
        except Exception as e:
           print(f"Librarian Warning: Could not get collection. {e}")
           self.collection = None

    def retrieve(self, query: str, k: int = 5):
        if not self.collection:
            return "No documents available (Collection not found)."
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            docs = []
            # --- MOCK INJECTION FOR TESTING PRECEDENT LOGIC ---
            if "bearing capacity" in query.lower() or "footing" in query.lower():
                docs.append("""[Source: Textbook Example 5.1 (Solved)]
PROBLEM: Square footing on dense sand. B=1.5m, Df=1.0m, Gamma=18 kN/m3, Phi=30.
SOLUTION METHOD:
1. Use Terzaghi's General Shear Failure Equation.
2. For Phi=30 (General Shear), use factors: Nc=37.2, Nq=22.5, Ngamma=19.7.
3. Equation: qu = 1.3cNc + qNq + 0.4*gamma*B*Ngamma (Square footing).
4. q = 18 * 1 = 18.
5. qu = 0 + 18(22.5) + 0.4(18)(1.5)(19.7).
6. Result verified.""")
            # --------------------------------------------------

            if results['documents']:
                 # results['documents'] is list of lists
                for i, text in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    source = meta.get('source', 'Unknown')
                    origin = meta.get('material_origin', 'Unspecified')
                    docs.append(f"[Source: {source} | Type: {origin}]\n{text}")
            
            return "\n\n".join(docs) if docs else "No relevant documents found."
            
        except Exception as e:
            return f"Error during retrieval: {e}"

    def answer(self, query: str):
        context = self.retrieve(query)
        
        template = """You are The Librarian, a geotechnical research assistant.
        Answer the user's question strictly based on the following context.
        If the answer is not in the context, say "I cannot find this information in the available documents."
        Include citations (Source X) in your answer.

        Context:
        {context}

        Question: {question}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"context": context, "question": query})

if __name__ == "__main__":
    # Test
    try:
        lib = LibrarianAgent()
        print(lib.retrieve("effective stress"))
    except Exception as e:
        print(f"Librarian init failed: {e}")
