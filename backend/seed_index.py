# backend/seed_index.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from backend.database import get_db
from backend.rag_indexer import embed_and_upsert

def seed():
    db = get_db()
    messages = list(db["messages"].find({}))
    
    if not messages:
        print("No messages found in database. Send some messages first, then re-run this script.")
        return

    count = 0
    errors = 0
    for msg in messages:
        try:
            embed_and_upsert(msg)
            count += 1
        except Exception as e:
            print(f"Error indexing message {msg.get('_id')}: {e}")
            errors += 1

    print(f"Seeding done. Indexed {count} messages. Errors: {errors}")

if __name__ == "__main__":
    seed()