import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Geotechnical LLM System",
    page_icon="🏗️",
    layout="wide"
)

def main():
    st.title("🏗️ Geotechnical Engineering AI Agent")
    
    st.markdown("""
    Welcome to the Advanced Geotechnical Engineering AI. 
    This system is designed to assist with:
    - Answering complex queries with citations
    - Solving design problems
    - Regulatory compliance checks
    """)

    with st.sidebar:
        st.header("Control Panel")
        mode = st.radio("Select Mode", ["Chat", "Document Ingestion", "Exam Generator"])
        
    if mode == "Chat":
        st.subheader("Consultation Mode")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ask a geotechnical question..."):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.spinner("The Council is deliberating..."):
                try:
                    from src.graph import app
                    from langchain_core.messages import HumanMessage
                    
                    # Run the graph
                    inputs = {"messages": [HumanMessage(content=prompt)]}
                    result = app.invoke(inputs)
                    
                    # Extract the final critique/answer
                    response = result.get("critique", "No response generated.")
                    
                    # Display assistant response in chat message container
                    # Display assistant response
                    with st.chat_message("assistant"):
                        # Get the text result
                        st.markdown(response)
                        
                        # Check for mindmap image
                        mindmap_path = result.get("mindmap_path", "")
                        if mindmap_path and os.path.exists(mindmap_path):
                            st.caption("📊 Concept Map")
                            st.image(mindmap_path, caption="Generated Mindmap")
                        
                        # expander for details
                        with st.expander("See reasoning process"):
                            st.markdown("**Context Retrieved:**")
                            st.info(result.get("context", "None"))
                            st.markdown("**Analyst Plan:**")
                            st.info(result.get("plan", "None"))
                            st.markdown("**Engineer Code:**")
                            st.code(result.get("code", "# No code"), language="python")
                            st.markdown("**Calculation Result:**")
                            st.success(result.get("result", "None"))

                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"System Error: {e}")

    elif mode == "Exam Generator":
        st.subheader("Exam Material Generator")
        topic = st.text_input("Enter Exam Topic/Context (e.g., 'Soil Mechanics Finals, focus on piles')")
        if st.button("Generate Exam"):
            with st.spinner("The Exam Council is designing the paper..."):
                try:
                    from src.graph import app
                    from langchain_core.messages import HumanMessage
                    
                    query = f"Generate an exam for: {topic}"
                    inputs = {"messages": [HumanMessage(content=query)]}
                    result = app.invoke(inputs)
                    
                    st.success("Exam Generated!")
                    st.markdown(result.get("result", ""))
                    
                    # Check for file output in result text
                    import re
                    match = re.search(r"File saved at: (.*)", result.get("result", ""))
                    if match:
                        st.info(f"Download available at: {match.group(1)}")
                        
                except Exception as e:
                    st.error(f"Generation Failed: {e}")

    elif mode == "Document Ingestion":
        st.subheader("Knowledge Base Ingestion")
        uploaded_files = st.file_uploader("Upload Standards/Textbooks (PDF)", accept_multiple_files=True)
        if st.button("Ingest Files"):
             st.info("Please run `python src/ingest.py` in the terminal for now.")

if __name__ == "__main__":
    main()
