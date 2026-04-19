import csv
import sys
import os

# Add parent dir to path so we can import from backend modules
sys.path.insert(0, os.path.dirname(__file__))

from database import get_messages_collection, get_conversations_collection, get_users_collection

def export_rag_data(filename="rag_chat_data.csv"):
    try:
        messages_col = get_messages_collection()
        users_col = get_users_collection()
        
        # Cache users to avoid repeated queries
        users_cache = {}
        for u in users_col.find():
            users_cache[u["login_id"]] = u
            
        messages = list(messages_col.find().sort("timestamp", 1))
        
        if not messages:
            print("No messages found to export.")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Headers explicitly structured for RAG text extraction context
            writer.writerow(["Timestamp", "Conversation_ID", "Sender_Name", "Sender_Department", "Sender_Role", "Message_Text"])
            
            for msg in messages:
                sender_id = msg.get("sender_id", "Unknown")
                user = users_cache.get(sender_id, {})
                
                sender_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or sender_id
                sender_dept = user.get("department", "Unknown")
                sender_role = user.get("role", "Unknown")
                
                writer.writerow([
                    msg.get("timestamp", ""),
                    msg.get("conversation_id", ""),
                    sender_name,
                    sender_dept,
                    sender_role,
                    msg.get("content", "")
                ])
                
        print(f"Successfully exported {len(messages)} messages to {filename}")
        
    except Exception as e:
        print(f"Error exporting data: {e}")

if __name__ == "__main__":
    export_rag_data()
