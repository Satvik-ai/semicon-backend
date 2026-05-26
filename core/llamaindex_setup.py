# core/llamaindex_setup.py

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface_api import HuggingFaceInferenceAPIEmbeddings

from .pinecone_client import get_pinecone_index
from semicon_chatbot_backend.settings import GROQ_API_KEY, EMBEDDING_MODEL, LLM_MODEL, LLM_TEMPERATURE, CHUNK_SIZE, CHUNK_OVERLAP,HF_TOKEN

# --- LLM & Embedding Configuration ---
Settings.embed_model = HuggingFaceInferenceAPIEmbeddings(
    model_name=EMBEDDING_MODEL,
    huggingfacehub_api_token=HF_TOKEN,
)

Settings.llm = Groq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    api_key=GROQ_API_KEY
)

Settings.node_parser = SentenceSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)

# --- Strict Grounding System Prompt ---
SYSTEM_PROMPT = """You are a semiconductor manufacturing expert assistant.

Rules:
- Answer ONLY from the provided context documents when relevant information is available
- If the answer is not found in the context:
    - You may answer using your own general knowledge ONLY IF the query is clearly related to semiconductor manufacturing processes or closely related technologies
    - In such cases, you MUST include this disclaimer at the beginning of your response:
      "This response is based on general semiconductor knowledge and not from the current knowledge base."
- If the query is not related to semiconductor manufacturing and not found in context, respond with:
  "I don't have information on that in the current knowledge base."
- Be precise and technical — use correct units, process node terminology, and fab-standard acronyms
- Explain step-by-step when describing a process
- Always mention which document or source your answer comes from when using context
- Give answer with professional markdown formatting 
"""

# --- Pinecone Vector Store ---
def get_vector_store():
    """Lazily create the vector store only when needed."""
    return PineconeVectorStore(pinecone_index=get_pinecone_index())

def get_storage_context():
    """Lazily create storage context only when needed."""
    return StorageContext.from_defaults(vector_store=get_vector_store())

def get_index():
    """Lazily create the VectorStoreIndex only when needed."""
    return VectorStoreIndex.from_vector_store(get_vector_store())