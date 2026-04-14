# core/llamaindex_setup.py

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from .pinecone_client import index

# Configure global settings
Settings.embed_model = OpenAIEmbedding()
Settings.llm = OpenAI(model="gpt-4o-mini")

vector_store = PineconeVectorStore(pinecone_index=index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

def get_index():
    return VectorStoreIndex.from_vector_store(vector_store)
