"""
Local file-based database fallback for testing without MongoDB
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import uuid

# Data directory
DATA_DIR = Path(__file__).parent / "local_data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
MESSAGES_FILE = DATA_DIR / "messages.json"
EVENTS_FILE = DATA_DIR / "events.json"

def load_json_file(file_path):
    """Load data from JSON file"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json_file(file_path, data):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

# User management
def get_users_collection():
    """Mock users collection"""
    return LocalUsersCollection()

class LocalUsersCollection:
    def find_one(self, query):
        users = load_json_file(USERS_FILE)
        for user in users:
            if query.get("login_id") and user.get("login_id") == query["login_id"]:
                return user
        return None
    
    def find(self, query=None, projection=None):
        users = load_json_file(USERS_FILE)
        if projection and "password_hash" in projection:
            for user in users:
                user.pop("password_hash", None)
        return users
    
    def insert_one(self, user_data):
        users = load_json_file(USERS_FILE)
        user_data["_id"] = str(uuid.uuid4())
        user_data["created_at"] = datetime.now(timezone.utc).isoformat()
        users.append(user_data)
        save_json_file(USERS_FILE, users)
        return type('MockResult', (), {'inserted_id': user_data["_id"]})()
    
    def update_one(self, query, update):
        users = load_json_file(USERS_FILE)
        for i, user in enumerate(users):
            if query.get("login_id") and user.get("login_id") == query["login_id"]:
                if "$set" in update:
                    users[i].update(update["$set"])
                save_json_file(USERS_FILE, users)
                return type('MockResult', (), {'matched_count': 1, 'modified_count': 1})()
        return type('MockResult', (), {'matched_count': 0, 'modified_count': 0})()

# Conversation management
def get_conversations_collection():
    return LocalConversationsCollection()

class LocalConversationsCollection:
    def find_one(self, query):
        convs = load_json_file(CONVERSATIONS_FILE)
        for conv in convs:
            if query.get("_id") and conv.get("_id") == str(query["_id"]):
                return conv
        return None
    
    def insert_one(self, conv_data):
        convs = load_json_file(CONVERSATIONS_FILE)
        conv_data["_id"] = str(uuid.uuid4())
        conv_data["created_at"] = datetime.now(timezone.utc).isoformat()
        convs.append(conv_data)
        save_json_file(CONVERSATIONS_FILE, convs)
        return type('MockResult', (), {'inserted_id': conv_data["_id"]})()
    
    def find(self, query=None):
        convs = load_json_file(CONVERSATIONS_FILE)
        return convs

# Message management
def get_messages_collection():
    return LocalMessagesCollection()

class LocalMessagesCollection:
    def find(self, query=None, sort=None, limit=None):
        messages = load_json_file(MESSAGES_FILE)
        if sort and sort[0][1] == -1:  # Descending order
            messages = sorted(messages, key=lambda x: x.get("_id", ""), reverse=True)
        if limit:
            messages = messages[:limit]
        return messages
    
    def insert_one(self, msg_data):
        messages = load_json_file(MESSAGES_FILE)
        msg_data["_id"] = str(uuid.uuid4())
        msg_data["created_at"] = datetime.now(timezone.utc).isoformat()
        messages.append(msg_data)
        save_json_file(MESSAGES_FILE, messages)
        return type('MockResult', (), {'inserted_id': msg_data["_id"]})()
    
    def find_one(self, query=None, sort=None):
        messages = load_json_file(MESSAGES_FILE)
        if sort and sort[0][1] == -1:
            messages = sorted(messages, key=lambda x: x.get("_id", ""), reverse=True)
        if messages:
            return messages[0]
        return None

# Event management
def get_events_collection():
    return LocalEventsCollection()

class LocalEventsCollection:
    def find(self, query=None):
        events = load_json_file(EVENTS_FILE)
        return events
    
    def insert_one(self, event_data):
        events = load_json_file(EVENTS_FILE)
        event_data["_id"] = str(uuid.uuid4())
        event_data["created_at"] = datetime.now(timezone.utc).isoformat()
        events.append(event_data)
        save_json_file(EVENTS_FILE, events)
        return type('MockResult', (), {'inserted_id': event_data["_id"]})()
    
    def update_one(self, query, update):
        events = load_json_file(EVENTS_FILE)
        for i, event in enumerate(events):
            if query.get("_id") and event.get("_id") == str(query["_id"]):
                if "$set" in update:
                    events[i].update(update["$set"])
                save_json_file(EVENTS_FILE, events)
                return type('MockResult', (), {'matched_count': 1, 'modified_count': 1})()
        return type('MockResult', (), {'matched_count': 0, 'modified_count': 0})()
    
    def delete_one(self, query):
        events = load_json_file(EVENTS_FILE)
        for i, event in enumerate(events):
            if query.get("_id") and event.get("_id") == str(query["_id"]):
                del events[i]
                save_json_file(EVENTS_FILE, events)
                return type('MockResult', (), {'deleted_count': 1})()
        return type('MockResult', (), {'deleted_count': 0})()

# Initialize with sample data
def initialize_sample_data():
    """Create sample admin users"""
    if not USERS_FILE.exists():
        admin_users = [
            {
                "login_id": "devadm000000",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e",  # devadm000000
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@company.com",
                "department": "Development",
                "department_code": "dev",
                "role": "Admin",
                "role_code": "adm",
                "password_changed": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        save_json_file(USERS_FILE, admin_users)
        print("Sample admin user created: devadm000000 / devadm000000")
    
    if not CONVERSATIONS_FILE.exists():
        save_json_file(CONVERSATIONS_FILE, [])
    
    if not MESSAGES_FILE.exists():
        save_json_file(MESSAGES_FILE, [])
    
    if not EVENTS_FILE.exists():
        save_json_file(EVENTS_FILE, [])

# Initialize data on import
initialize_sample_data()
