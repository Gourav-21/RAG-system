# Document RAG System

The **Document RAG System** is a Retrieval Augmented Generation (RAG) platform that enables you to upload various document types, process them into semantic chunks, and perform vector-based searches. The system is built using Streamlit for the web interface and FastAPI for the backend API, with document storage and retrieval powered by Weaviate.


## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Running the Web Interface](#running-the-web-interface)
  - [API Endpoints](#api-endpoints)
- [Workflow](#workflow)
- [Dependencies](#dependencies)


## Features

- **Document Upload:** Supports PDF, DOCX, TXT, and JSON file formats.
- **Automatic Processing:** Uses OCR (pytesseract) for PDFs and text extraction libraries for other formats.
- **Text Chunking:** Splits large documents into manageable chunks with contextual information.
- **Semantic Search:** Implements vector-based search using Weaviate to retrieve relevant document chunks.
- **Clean UI:** Streamlit-based user interface for easy document upload, search, and database management.
- **API Integration:** FastAPI endpoints for document upload, search, and deletion.


## System Architecture

The system comprises two main components:

### 1. Web Interface (Frontend)
- **Built With:** [Streamlit](https://streamlit.io/)
- **Purpose:** Provides an intuitive interface for uploading documents, searching through them, and managing the database.
- **Features:**
  - **Upload Documents Page:** Users can upload files and clear the database.
  - **Search Documents Page:** Users can enter search queries and view formatted results with context.

### 2. Backend API
- **Built With:** [FastAPI](https://fastapi.tiangolo.com/)
- **Purpose:** Handles file processing, document chunking, and communicates with the Weaviate vector database.
- **Key Endpoints:**
  - **POST `/upload`:** Processes and uploads documents.
  - **GET `/query`:** Searches for document chunks based on semantic similarity.
  - **DELETE `/delete`:** Clears the entire document database.

### 3. Data Storage and Retrieval
- **Vector Database:** [Weaviate](https://weaviate.io/)
- **Workflow:** Documents are converted into chunks, embedded using a vectorizer, and stored as objects in a Weaviate collection named `DocumentChunk`.



## Setup and Installation

### Prerequisites

- **Python 3.8+**
- **pip** package manager

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Gourav-21/RAG-system.git
   cd RAG-system
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables:**

   Create a `.env` file in the root directory with the following keys:
   ```ini
   TESSERACT_CMD=/usr/bin/tesseract  # or your local Tesseract executable path
   WEAVIATE_API_KEY=your_weaviate_api_key
   WEAVIATE_URL=https://your-weaviate-instance.weaviate.network
   ```

5. **Additional Setup:**
   - Ensure [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) is installed and properly configured on your system.
   - Validate that your Weaviate instance is running and accessible using the provided URL and API key.


## Usage

### Running the Web Interface

The Streamlit interface allows you to interact with the system via a browser.

```bash
streamlit run app.py
```

- **Upload Documents:** Navigate to the "Upload Documents" page via the sidebar. Choose a file (PDF, DOCX, TXT, or JSON) to upload. The system will process the file into chunks and store them in the vector database.
- **Search Documents:** Go to the "Search Documents" page, enter your query, and adjust the number of desired results. Results include the document name, chunk identifier, text, and additional context.

### API Endpoints

The FastAPI backend exposes the following endpoints:

#### 1. **POST `/upload`**
- **Description:** Uploads and processes a document.
- **Parameters:** 
  - `file` (UploadFile): The document to upload. Accepted formats: PDF, DOCX, TXT, JSON.
- **Response:**
  ```json
  {
      "success": true,
      "message": "Document '<filename>' processed successfully",
      "chunks": <number_of_chunks>
  }
  ```

#### 2. **GET `/query`**
- **Description:** Searches for document chunks based on a text query.
- **Query Parameters:**
  - `query` (string): The search text.
  - `limit` (int, default: 5): Maximum number of results to return.
- **Response:**
  ```json
  {
      "results": [
          {
              "text": "Extracted chunk text",
              "document_name": "filename.ext",
              "chunk_id": 0,
              "document_type": "pdf",
              "context_before": "Previous chunk text",
              "context_after": "Next chunk text",
              "relevance_score": 0.95,
              "distance": 0.1
          },
          ...
      ],
      "query": "<your_query>"
  }
  ```

#### 3. **DELETE `/delete`**
- **Description:** Deletes all documents from the database.
- **Response:**
  ```json
  {
      "message": "All documents deleted successfully"
  }
  ```


## Workflow

1. **Document Upload:**
   - The user selects a file from the web interface.
   - The file is sent to the FastAPI `/upload` endpoint.
   - The system verifies the file type and temporarily stores the file.
   - For PDFs, each page is converted into an image and processed via Tesseract OCR.
   - The content is extracted (for DOCX, TXT, and JSON, text is directly read).
   - The extracted text is split into manageable chunks with a fixed size and overlap.
   - Each chunk is augmented with contextual information (previous and next chunks) and stored in Weaviate as a separate object.

2. **Document Search:**
   - The user enters a search query on the web interface.
   - The query is sent to the FastAPI `/query` endpoint.
   - Weaviate performs a semantic (vector) search on the stored document chunks.
   - Matching chunks are returned along with metadata (e.g., relevance score, document details).
   - The web interface displays the results in a user-friendly format.

3. **Database Management:**
   - Users can clear the entire document database using the "Delete All Documents" button.
   - This action calls the FastAPI `/delete` endpoint, which removes all objects from the Weaviate collection and resets the schema.


## Dependencies

- **Streamlit:** For building the web interface.
- **FastAPI:** For creating the RESTful API.
- **Weaviate:** For vector database storage and semantic search.
- **Tesseract (pytesseract):** For OCR processing of PDFs.
- **pdfplumber:** For extracting images/text from PDF files.
- **python-docx:** For reading DOCX files.
- **langchain:** For text chunking using `RecursiveCharacterTextSplitter`.
- **python-dotenv:** For loading environment variables.
- **Additional Libraries:** `os`, `shutil`, `tempfile`, etc.

