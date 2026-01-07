from src.graph import app
from langchain_core.messages import HumanMessage

def test_council():
    print("Testing Geotechnical Council (Chair-Driven)...")
    # A standard problem: Bearing capacity
    query = "Calculate the ultimate bearing capacity of a prompt footing on sand. Gamma=18, B=2m, Df=1m, phi=30."
    
    try:
        # Recursion limit might be hit if Chair loops too long, but standard graph defaults to 25 steps
        inputs = {"messages": [HumanMessage(content=query)]}
        
        # Invoke app
        print("Invoking graph (this may take time as agents discuss)...")
        result = app.invoke(inputs)
        
        print("\n--- FINAL STATE ---")
        print(f"Messages: {len(result['messages'])}")
        
        # Print discussion history
        for m in result['messages']:
            print(f"> [{m.name}]: {m.content[:100]}...")
            
        print("\n--- Artifacts ---")
        if result.get("context"): print(f"Context: Yes ({len(result['context'])})")
        if result.get("plan"): print(f"Plan: {result['plan'][:50]}...")
        if result.get("code"): print(f"Code: {result['code'][:50]}...")
        if result.get("result"): print(f"Result: {result['result']}")
        if result.get("critique"): print(f"Critique: {result['critique']}")
        
        print("\nSUCCESS: Council Session Adjourned.")
        
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_council()
