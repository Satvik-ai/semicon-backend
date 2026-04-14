# documents/services.py

import os
from pypdf import PdfReader
from llama_index.core import VectorStoreIndex, Document as LlamaDoc
from llama_index.core.node_parser import SentenceSplitter

from core.llamaindex_setup import storage_context
from .models import Document


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def ingest_document(document: Document) -> str:
    """
    Full ingestion pipeline for a Document model instance:
    1. Extract text from PDF
    2. Create LlamaDoc with rich metadata (mirroring Pinecone metadata schema)
    3. Chunk using project-spec settings (600 tokens, 100 overlap)
    4. Embed and store in Pinecone
    5. Update Document.is_indexed status
    """
    file_path = document.file.path

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")

    # Extract text
    text = extract_text_from_pdf(file_path)

    if not text:
        raise ValueError(f"Could not extract text from '{document.title}'. Is it a scanned PDF?")

    # Build metadata dict — this will be stored in each Pinecone chunk node
    metadata = {
        "doc_title": document.title,
        "process": document.process,
        "stage": document.stage,
        "doc_type": document.doc_type,
        "document_id": document.id,
        "uploaded_by": document.uploaded_by.username if document.uploaded_by else "unknown",
    }

    # Create LlamaIndex Document with metadata
    llama_doc = LlamaDoc(text=text, metadata=metadata)

    splitter = SentenceSplitter(chunk_size=600, chunk_overlap=100)
    nodes = splitter.get_nodes_from_documents([llama_doc])

    # Index nodes into Pinecone
    VectorStoreIndex(nodes, storage_context=storage_context)

    # Mark as indexed in PostgreSQL
    document.is_indexed = True
    document.indexing_error = ''
    document.save(update_fields=['is_indexed', 'indexing_error'])

    return f"Successfully indexed '{document.title}' — {len(nodes)} chunks stored in Pinecone."


def ingest_document_safe(document: Document) -> str:
    """
    Wrapper that catches errors and records them on the Document model
    instead of crashing the request.
    """
    try:
        return ingest_document(document)
    except Exception as e:
        error_msg = str(e)
        document.is_indexed = False
        document.indexing_error = error_msg
        document.save(update_fields=['is_indexed', 'indexing_error'])
        raise

