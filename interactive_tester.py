import sys
import os
from src.graph import app
from langchain_core.messages import HumanMessage
import time

def main():
    print("==================================================")
    print("   GEOTECHNICAL AI COUNCIL - INTERACTIVE SUITE    ")
    print("==================================================")
    print("Modes available:")
    print(" - 'Generate an exam...': Triggers Exam Council")
    print(" - 'Explain theory...': Triggers Mind Map + Consensus")
    print(" - 'Calculate...': Triggers Standard Consensus")
    print("Type 'exit' or 'quit' to stop.")
    print("==================================================\n")

    while True:
        try:
            query = input("\n[USER REQUEST] >> ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break
            if not query:
                continue

            print(f"\n... Processing Request: '{query}' ...")
            start_time = time.time()
            
            inputs = {"messages": [HumanMessage(content=query)]}
            
            # Streaming could be added, but invoke is safer for now
            result = app.invoke(inputs)
            
            elapsed = time.time() - start_time
            
            print(f"\n--- [RESULT] ({elapsed:.2f}s) ---")
            
            # Handle different output keys
            final_text = ""
            if "result" in result:
                final_text = result["result"]
                print(final_text)
            else:
                print(result)
            
            # Check for rendered mindmap image
            if "mindmap_path" in result and result["mindmap_path"]:
                try:
                    mm_path = result["mindmap_path"]
                    print(f"\n[INFO] Mindmap image saved to: {mm_path}")
                    # Auto-open the image (Windows)
                    os.startfile(mm_path)
                except Exception as ex:
                    print(f"[WARN] Could not open mindmap image: {ex}")
                
            print("\n--------------------------------------------------")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
