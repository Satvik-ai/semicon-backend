# documents/services.py

from llama_index.core import VectorStoreIndex, Document as LlamaDoc
from core.llamaindex_setup import storage_context
from pypdf import PdfReader

def extract_text(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def ingest_document(file_path):

    text = extract_text(file_path)

    doc = LlamaDoc(text=text)

    index = VectorStoreIndex.from_documents(
        [doc],
        storage_context=storage_context
    )

    return "Document indexed successfully"
