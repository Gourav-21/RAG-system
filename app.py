import streamlit as st
from main import upload, search, delete_all
import os
import pytesseract

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")

st.set_page_config(
    page_title="Document RAG System",
    page_icon="📚",
    layout="wide"
)

# Sidebar for app navigation
st.sidebar.title("📚 Document RAG System")
page = st.sidebar.radio("Navigation", ["Upload Documents", "Search Documents"])


# Custom CSS
st.markdown("""
<style>
    .result-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #4CAF50;
    }
    .document-info {
        font-size: 0.8em;
        color: #6c757d;
    }
    .main-text {
        font-size: 1.1em;
        margin: 10px 0;
    }
    .context {
        font-size: 0.9em;
        color: #495057;
        padding: 8px;
        background-color: #e9ecef;
        border-radius: 3px;
        margin-top: 5px;
    }
    .score {
        font-weight: bold;
        color: #28a745;
    }
    .upload-container {
        border: 2px dashed #ddd;
        border-radius: 8px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        background-color: #f8f9fa;
        transition: all 0.3s ease;
    }
    .upload-container:hover {
        border-color: #4CAF50;
        background-color: #f1f8e9;
    }
    .section-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .file-info {
        padding: 10px;
        background-color: #e3f2fd;
        border-radius: 5px;
        margin: 10px 0;
    }
    .clear-section {
        background-color: #fff3f3;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ffcdd2;
    }
</style>
""", unsafe_allow_html=True)

# Upload Documents Page
if page == "Upload Documents":
    st.title("Upload Documents")
    
    # Create a clean, focused upload section
    st.subheader("Upload New Document")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file (PDF, DOCX, TXT, JSON)",
            type=["pdf", "docx", "txt", "json"]
        )
        
        if uploaded_file is not None:
            st.info(f"Selected file: {uploaded_file.name}")
            if st.button("Upload Document", use_container_width=True):
                with st.spinner("Uploading and processing document..."):
                    result = upload(uploaded_file)
                    
                    if result.get("success"):
                        st.success(f"Document processed successfully! Created {result['chunks']} chunks.")
                    else:
                        st.error(f"Error: {result.get('detail', 'Unknown error')}")
    
    with col2:
        # Delete all documents button
        st.markdown("### 🗑️Clear Database")
        if st.button("Delete All Documents", type="primary", use_container_width=True):
            with st.spinner("Deleting all documents..."):
                result = delete_all()
                st.success(f"{result['message']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        ### Supported File Types
        - PDF (`.pdf`)
        - Word (`.docx`)
        - Text (`.txt`)
        - JSON (`.json`)
        """)

# Search Documents Page
elif page == "Search Documents":
    st.title("Search Documents")
    
    query = st.text_input("Enter your search query")
    
    result_limit = st.slider("Number of results", min_value=1, max_value=10, value=5)
    
    if st.button("Search"):
        if not query:
            st.warning("Please enter a search query")
        else:
            with st.spinner("Searching..."):
                results = search(query, result_limit)
                
                if results.get("results"):
                    st.subheader(f"Search Results for: '{results['query']}'")
                    
                    for i, result in enumerate(results["results"]):
                        # Display each result with custom HTML/CSS
                        st.markdown(f"""
                        <div class="result-box">
                            <div class="document-info">
                                📄 <b>{result['document_name']}</b> (Type: {result['document_type']}, Chunk: {result['chunk_id']})
                                <span class="score">Score: {result['relevance_score']:.2f}</span>
                            </div>
                            <div class="main-text">{result['text']}</div>
                            <details>
                                <summary>Show Context</summary>
                                <div class="context">
                                    <b>Context Before:</b><br>
                                    {result['context_before']}<br><br>
                                    <b>Context After:</b><br>
                                    {result['context_after']}
                                </div>
                            </details>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No results found. Try modifying your query.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This is a Retrieval Augmented "
    "Generation (RAG) system. Upload documents and search through them using "
    "semantic search powered by vector embeddings."
)