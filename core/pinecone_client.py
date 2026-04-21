# core/pinecone_client.py

import os
from pinecone import Pinecone, ServerlessSpec
from semicon_chatbot_backend.settings import PINECONE_API_KEY

_index = None

def get_pinecone_index():
    global _index
    if _index is not None:
        return _index

    pc = Pinecone(
        api_key=PINECONE_API_KEY,
    )

    index_name = "semicon-index"

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    _index = pc.Index(index_name)
    return _index
