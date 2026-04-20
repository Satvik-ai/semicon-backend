# core/pinecone_client.py

import os
from pinecone import Pinecone, PodSpec

_index = None

def get_pinecone_index():
    global _index
    if _index is not None:
        return _index

    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY", "local-dummy-key"),
        host=os.getenv("PINECONE_HOST", "http://localhost:5081"),
    )

    index_name = "semicon-index"

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=PodSpec(
                environment="local",
                pod_type="p1.x1",
            )
        )

    _index = pc.Index(index_name)
    return _index
