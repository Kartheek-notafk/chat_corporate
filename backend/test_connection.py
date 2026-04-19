"""
Run this from the chat-app folder to test MongoDB connectivity:
    python test_connection.py
"""
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
 
URI = "mongodb+srv://dineshkataru:venkataD17@cluster0.et0vwk6.mongodb.net/?appName=Cluster0"
DB  = "chatapp1"
 
print("⏳ Connecting to MongoDB Atlas...")
 
try:
    client = MongoClient(URI, serverSelectionTimeoutMS=6000)
    client.admin.command("ping")
    print("✅ SUCCESS — MongoDB connected!")
    print(f"✅ Database '{DB}' is ready.")
    print(f"✅ Collections: {client[DB].list_collection_names()}")
 
except OperationFailure as e:
    print("❌ AUTHENTICATION FAILED")
    print("   → Wrong username or password in the URI.")
    print(f"   → Detail: {e}")
 
except ServerSelectionTimeoutError as e:
    print("❌ CONNECTION TIMED OUT")
    print("   → Your IP is NOT whitelisted in Atlas Network Access.")
    print("   → Fix: Atlas → Network Access → Add IP Address → Allow from Anywhere (0.0.0.0/0)")
    print(f"   → Detail: {e}")
 
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}") 
