# backend/rag_watcher.py
from pymongo import MongoClient
from backend.rag_indexer import embed_and_upsert

def watch_messages(db):
    pipeline = [{"$match": {"operationType": {"$in": ["insert", "update"]}}}]
    with db["messages"].watch(pipeline) as stream:
        for change in stream:
            doc = change["fullDocument"]
            embed_and_upsert(doc)  # index new message immediately