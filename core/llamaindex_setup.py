# core/llamaindex_setup.py

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from .pinecone_client import index

# --- LLM & Embedding Configuration ---
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)

# 500–800 tokens, 100 overlap — keeps process steps intact, avoids broken context
Settings.node_parser = SentenceSplitter(
    chunk_size=600,   # Middle of 500–800 range
    chunk_overlap=100
)

# --- Pinecone Vector Store ---
vector_store = PineconeVectorStore(pinecone_index=index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# --- Strict Grounding System Prompt (from project spec) ---
SYSTEM_PROMPT = """You are a semiconductor manufacturing expert assistant.

Rules:
- Answer ONLY from the provided context documents
- If the answer is not found in the context, respond with: "I don't have information on that in the current knowledge base."
- Be precise and technical — use correct units, process node terminology, and fab-standard acronyms
- Explain step-by-step when describing a process
- Always mention which document or source your answer comes from
"""

def get_index():
    return VectorStoreIndex.from_vector_store(vector_store)