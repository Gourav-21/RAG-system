from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import docx
import os
import shutil
import tempfile
from langchain.text_splitter import RecursiveCharacterTextSplitter
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter, MetadataQuery
import pdfplumber
import pytesseract

load_dotenv()

wcd_key = os.getenv("WEAVIATE_API_KEY")
wcd_url = os.getenv("WEAVIATE_URL")

if not wcd_key or not wcd_url:
    raise ValueError(
        "Missing required environment variables. Please ensure WEAVIATE_API_KEY and WEAVIATE_URL are set."
    )

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

wcd_key = os.getenv("WEAVIATE_API_KEY")
wcd_url = os.getenv("WEAVIATE_URL")

def get_weaviate_client():    
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=wcd_url,                    
        auth_credentials=Auth.api_key(wcd_key), 
    )
    return client

def setup_weaviate_schema():
    client= get_weaviate_client()
    if not client.collections.exists("DocumentChunk"):
        client.collections.create(
            "DocumentChunk",
            description="Stores document text chunks with embeddings",
            vectorizer_config=[
                Configure.NamedVectors.text2vec_weaviate(
                    name="document_vector",
                    source_properties=["text"],
                    model="Snowflake/snowflake-arctic-embed-m-v1.5",
                )
            ],
            properties=[
                Property(name="document_name", data_type=DataType.TEXT),
                Property(name="chunk_id", data_type=DataType.INT),
                Property(name="document_type", data_type=DataType.TEXT),
                Property(name="total_chunks", data_type=DataType.INT),
                Property(name="text", data_type=DataType.TEXT),
                Property(name="context_before", data_type=DataType.TEXT),  
                Property(name="context_after", data_type=DataType.TEXT)    
            ]
        )
    client.close()

setup_weaviate_schema()

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    filename = getattr(file, "filename", None) or getattr(file, "name", None)
    if not filename:
        raise HTTPException(status_code=400, detail="File does not have a valid filename")
   
    file_extension = filename.split(".")[-1]
    if file_extension not in ['pdf', 'docx', 'txt', 'json']:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    try:
        client= get_weaviate_client()
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, filename)
        
        # Save the file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file if hasattr(file, "file") else file, buffer)
        
        delete_doc(filename)
        
        chunks = process_doc(temp_file_path, file_extension, filename)

        collection = client.collections.get("DocumentChunk")
        with collection.batch.dynamic() as batch:
            for data_row in chunks:
                batch.add_object(
                    properties=data_row,
                )
        
    finally:
        # Clean up the temporary file
        shutil.rmtree(temp_dir)
        client.close()

    return {
            "success": True,
            "message": f"Document '{filename}' processed successfully",
            "chunks": len(chunks)
        }

@app.get("/query")
def search(query: str, limit: int = 5):
    client = get_weaviate_client()
    try:
        collection = client.collections.get("DocumentChunk")
        response = collection.query.near_text(
            query=query,
            limit=limit,
            return_metadata=MetadataQuery(distance=True, certainty=True)
        )
        results = []
        for item in response.objects:
            results.append({
                "text": item.properties["text"],
                "document_name": item.properties["document_name"],
                "chunk_id": item.properties["chunk_id"],
                "document_type": item.properties["document_type"],
                "context_before": item.properties.get("context_before", ""),
                "context_after": item.properties.get("context_after", ""),
                "relevance_score": item.metadata.certainty,
                "distance": item.metadata.distance
            })
    finally:
        client.close()
        
    return {"results": results, "query": query}


@app.delete("/delete")
def delete_all():
    try:
        client= get_weaviate_client()
        client.collections.delete("DocumentChunk")
        setup_weaviate_schema()
    finally:
            client.close()
            
    return {"message": "All documents deleted successfully"}
    

def process_doc(file_path: str, file_type: str, file_name: str) -> list:
    text = ""
    if file_type == "pdf":
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                img = page.to_image(resolution=300).annotated
                text += pytesseract.image_to_string(img) + "\n"
    elif file_type == "docx":
        doc = docx.Document(file_path)
        text = " ".join([para.text for para in doc.paragraphs])
    elif file_type == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            text = json.dumps(data)
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=150,
            length_function=len
        )
    
    chunks = splitter.split_text(text)

    document_chunks = []
    for i, chunk in enumerate(chunks):
        context_before = chunks[i-1] if i > 0 else ""
        context_after = chunks[i+1] if i < len(chunks)-1 else ""
        document_chunks.append({
            "text": chunk,
            "document_name": file_name,
            "chunk_id": i,
            "document_type": file_type,  
            "total_chunks": len(chunks),
            "context_before": context_before,
            "context_after": context_after
        })
    
    return document_chunks

def delete_doc(document_name: str):
    client= get_weaviate_client()
    try:
        collection = client.collections.get("DocumentChunk")
        collection.data.delete_many(
            where=Filter.by_property("document_name").equal(document_name)
        )
    finally:
        client.close()