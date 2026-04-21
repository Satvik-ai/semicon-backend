# chat/services.py

from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import PromptTemplate

from core.llamaindex_setup import get_index, SYSTEM_PROMPT
from .models import ChatSession, ChatMessage

"""
The complete query flow when a user submits a query from the frontend:
    query_chatbot(user, query, filters)
    └─ build_query_engine(process_filter, stage_filter)
            ├─ VectorIndexRetriever  →  Pinecone top-5 chunks
            └─ RetrieverQueryEngine  →  Groq LLM synthesis
    └─ Save ChatSession + ChatMessage to PostgreSQL
    └─ Return { answer, sources, session_id, message_id }
"""


def build_query_engine(process_filter: str = None, stage_filter: str = None):
    """
    Builds a LlamaIndex query engine with optional Pinecone metadata filters.
    Filters map to the metadata stored at ingestion time:
      - process: e.g. "etching", "lithography", "deposition"
      - stage: e.g. "FEOL", "BEOL"
    """
    index = get_index()

    # Build metadata filters if provided
    filters = None
    if process_filter or stage_filter:
        from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator
        filter_list = []
        if process_filter:
            filter_list.append(MetadataFilter(key="process", value=process_filter, operator=FilterOperator.EQ))
        if stage_filter:
            filter_list.append(MetadataFilter(key="stage", value=stage_filter, operator=FilterOperator.EQ))
        filters = MetadataFilters(filters=filter_list)

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
        filters=filters
    )

    # Inject the strict grounding system prompt from project spec
    qa_prompt = PromptTemplate(
        SYSTEM_PROMPT + "\n\nContext:\n{context_str}\n\nQuestion: {query_str}\nAnswer:"
    )

    response_synthesizer = get_response_synthesizer(
        response_mode="compact",
        text_qa_template=qa_prompt,
        streaming=False,
    )

    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )


def query_chatbot(user, user_query: str, session_id: int = None,
                  process_filter: str = None, stage_filter: str = None) -> dict:
    """
    Main service function called by the chat view.
    - Runs the RAG query
    - Persists user message and assistant response to DB
    - Returns answer + structured sources
    """
    if not user_query or not user_query.strip():
        return {"error": "Query cannot be empty."}

    # Get or create session
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(user=user)
    else:
        session = ChatSession.objects.create(user=user)

    # Save the user message
    ChatMessage.objects.create(
        session=session,
        role='user',
        content=user_query
    )

    # Run RAG query
    query_engine = build_query_engine(process_filter=process_filter, stage_filter=stage_filter)
    response = query_engine.query(user_query)

    # Build structured source list with metadata
    sources = []
    for node in response.source_nodes:
        source_info = {
            "text": node.node.text[:300],  # Preview, not full chunk
            "score": round(node.score, 4) if node.score else None,
            "doc_title": node.node.metadata.get("doc_title", "Unknown"),
            "process": node.node.metadata.get("process", ""),
            "stage": node.node.metadata.get("stage", ""),
            "doc_type": node.node.metadata.get("doc_type", ""),
        }
        sources.append(source_info)

    answer = str(response)

    # Save the assistant response with sources
    assistant_msg = ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=answer,
        sources=sources
    )

    return {
        "session_id": session.id,
        "message_id": assistant_msg.id,
        "answer": answer,
        "sources": sources,
    }

