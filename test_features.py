from src.graph import app
from langchain_core.messages import HumanMessage
import os

def test_exam_generation():
    print("\n--- TEST 1: EXAM GENERATION (CSE 2015 Scenario) ---")
    query = "Generate an exam similar to the 2015 CSE paper. Include questions on bearing capacity and settlement."
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        result = app.invoke(inputs)
        
        print("\n[Result Log]")
        print(result.get("result", "No result found"))
        
        # Check if file exists
        files = os.listdir("outputs")
        print(f"\n[Output Directory]: {files}")
        
    except Exception as e:
        print(f"Exam Test Failed: {e}")
        import traceback
        traceback.print_exc()

def test_mindmap():
    print("\n--- TEST 2: MIND MAP (Smith's Effective Stress) ---")
    query = "Explain effective stress using Smith's method."
    
    try:
        inputs = {"messages": [HumanMessage(content=query)]}
        result = app.invoke(inputs)
        
        full_text = result.get("result", "")
        if "mindmap" in full_text:
            print("[SUCCESS] Mermaid Mindmap block found in output.")
            print(full_text.split("```mermaid")[1][:150] + "...")
        else:
            print("[FAILURE] No mindmap found.")
            
    except Exception as e:
         print(f"MindMap Test Failed: {e}")

if __name__ == "__main__":
    test_exam_generation()
    test_mindmap()
