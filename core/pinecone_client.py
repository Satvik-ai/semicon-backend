# core/pinecone_client.py

import os
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "semicon-index"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,        # OpenAI text-embedding-ada-002 output dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",       # Change to "gcp" if using GCP Pinecone project
            region="us-east-1" # Match your Pinecone project region
        )
    )
 
index = pc.Index(index_name)
