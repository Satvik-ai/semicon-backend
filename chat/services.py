# chat/services.py

from core.llamaindex_setup import get_index

def query_chatbot(user_query):

    index = get_index()

    query_engine = index.as_query_engine(
        similarity_top_k=5
    )

    response = query_engine.query(user_query)

    return {
        "answer": str(response),
        "sources": [node.node.text for node in response.source_nodes]
    }
