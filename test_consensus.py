from src.graph import app
from langchain_core.messages import HumanMessage
from src.agents.consensus import ConsensusManager

def test_consensus_flow():
    print("Testing Geotechnical Council (3-Stage Consensus)...")
    query = "Calculate the ultimate bearing capacity of a prompt footing. Gamma=18, B=2m, Df=1m, phi=30. Use Terzaghi."
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        print("Invoking graph (collecting responses from DeepSeek, GPT, Mistral)...")
        
        result = app.invoke(inputs)
        
        print("\n--- FINAL CONSENSUS STATE ---")
        msgs = result['messages']
        for m in msgs:
            print(f"> [{m.name}]: {m.content[:150]}...")
            
        print("\n--- Synthesis Result ---")
        print(result.get("result"))
        
        print("\nSUCCESS: Consensus Protocol Completed.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_consensus_flow()
