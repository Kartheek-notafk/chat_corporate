# backend/rag_indexer.py
import os
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")

# Use absolute path so it always points to the same folder regardless of where script is run
rag_store_path = os.path.join(os.path.dirname(__file__), "../rag_store")
chroma = chromadb.PersistentClient(path=rag_store_path)
collection = chroma.get_or_create_collection("messages")

def embed_and_upsert(doc):
    # Use sender_id to match what database.py actually stores
    sender = doc.get("sender_id") or doc.get("sender", "unknown")
    conversation_id = str(doc.get("conversation_id", ""))
    timestamp = str(doc.get("timestamp", ""))
    content = doc.get("content", "")

    text = f"[{sender} in {conversation_id} at {timestamp}]: {content}"
    embedding = model.encode(text).tolist()

    collection.upsert(
        ids=[str(doc["_id"])],
        embeddings=[embedding],
        documents=[text],
        metadatas={
            "sender": sender,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
        }
    )