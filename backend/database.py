import os
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv()

_client = None
_use_local_db = False

def get_db():
    global _client, _use_local_db
    if _use_local_db:
        return None  # Using local database
    
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        try:
            _client = MongoClient(uri, serverSelectionTimeoutMS=6000)
            _client.admin.command("ping")
        except OperationFailure as e:
            print(f"MongoDB Auth Failed: {e}")
            _use_local_db = True
            return None
        except ServerSelectionTimeoutError:
            print("Cannot reach MongoDB. Using local file database instead.")
            _use_local_db = True
            return None
        except Exception as e:
            print(f"MongoDB connection error: {e}. Using local file database instead.")
            _use_local_db = True
            return None
    return _client[os.getenv("DB_NAME", "chatapp1")]

def get_users_collection():
    db = get_db()
    if db is None:
        # Use local database
        from local_db import get_users_collection as local_users
        return local_users()
    return db["users"]

def get_next_sequence_number(department_code, role_code):
    """Get the next sequential number for a department-role combination"""
    users = get_users_collection()
    pattern = f"^{department_code}{role_code}"
    
    # Handle local database which doesn't support regex queries the same way
    try:
        last_user = users.find_one({"login_id": {"$regex": pattern}}, sort=[("login_id", -1)])
    except:
        # For local DB, do manual filtering
        all_users = users.find()
        matching_users = [u for u in all_users if u.get("login_id", "").startswith(f"{department_code}{role_code}")]
        if matching_users:
            matching_users.sort(key=lambda x: x.get("login_id", ""), reverse=True)
            last_user = matching_users[0]
        else:
            last_user = None
    
    if last_user:
        last_number = int(last_user["login_id"][-6:])
        return last_number + 1
    else:
        return 1

def get_registered_users(department_code=None):
    """Get all registered users, optionally filtered by department"""
    users = get_users_collection()
    query = {}
    if department_code:
        query["department_code"] = department_code
    
    return list(users.find(query, {"password_hash": 0}).sort("created_at", -1))

def get_conversations_collection():
    db = get_db()
    if db is None:
        from local_db import get_conversations_collection as local_convos
        return local_convos()
    return db["conversations"]

def get_messages_collection():
    db = get_db()
    if db is None:
        from local_db import get_messages_collection as local_messages
        return local_messages()
    return db["messages"]

def get_events_collection():
    db = get_db()
    if db is None:
        from local_db import get_events_collection as local_events
        return local_events()
    return db["events"]

def get_user_conversations(login_id):
    """Get all conversations (direct and group) the user is a part of"""
    convos = get_conversations_collection()
    return list(convos.find({"participants": login_id}).sort("last_message_time", -1))

def get_or_create_direct_conversation(id1, id2):
    """Get existing direct conversation or create new one"""
    convos = get_conversations_collection()
    participants = sorted([id1, id2])
    convo_id = f"direct_{participants[0]}_{participants[1]}"
    
    existing = convos.find_one({"conversation_id": convo_id})
    if existing:
        return existing
        
    new_convo = {
        "conversation_id": convo_id,
        "is_group": False,
        "name": None,
        "participants": participants,
        "created_at": datetime.now(timezone.utc),
        "last_message": "Started a new conversation",
        "last_message_time": datetime.now(timezone.utc)
    }
    convos.insert_one(new_convo)
    return new_convo

def create_group_conversation(creator_id, name, participants):
    """Create a new group conversation"""
    convos = get_conversations_collection()
    convo_id = f"group_{uuid.uuid4().hex[:8]}"
    
    # Ensure creator is in participants
    if creator_id not in participants:
        participants.append(creator_id)
        
    new_convo = {
        "conversation_id": convo_id,
        "is_group": True,
        "name": name,
        "participants": list(set(participants)),
        "created_at": datetime.now(timezone.utc),
        "last_message": "Group created",
        "last_message_time": datetime.now(timezone.utc)
    }
    convos.insert_one(new_convo)
    return new_convo

def get_messages(conversation_id):
    """Get all messages for a conversation"""
    msgs = get_messages_collection()
    return list(msgs.find({"conversation_id": conversation_id}).sort("timestamp", 1))

def send_message(conversation_id, sender_id, content):
    """Send a message and update last_message on the conversation"""
    msgs = get_messages_collection()
    convos = get_conversations_collection()
    
    now = datetime.now(timezone.utc)
    msg = {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "content": content,
        "timestamp": now
    }
    
    # Insert message and get the inserted ID
    result = msgs.insert_one(msg)
    msg["_id"] = result.inserted_id
    
    # Update conversation's last message time and preview
    convos.update_one(
        {"conversation_id": conversation_id},
        {"$set": {
            "last_message": content[:50] + "..." if len(content) > 50 else content,
            "last_message_time": now
        }}
    )
    
    # Extract tasks from the message (non-blocking)
    try:
        # Check if auto-task creation is enabled (default to True for now)
        # In a real implementation, this would be passed from the frontend
        auto_task_creation = True  # TODO: Get from user settings
        
        if auto_task_creation:
            # Get conversation participants
            conversation = convos.find_one({"conversation_id": conversation_id})
            if conversation:
                participants = conversation.get("participants", [])
                
                # Import task extractor
                from task_extractor import extract_tasks_from_message
                
                # Extract tasks
                tasks = extract_tasks_from_message(
                    content, 
                    sender_id, 
                    participants, 
                    conversation_id,
                    str(result.inserted_id)
                )
                
                # Store extracted tasks as events
                if tasks:
                    events_collection = get_events_collection()
                    for task in tasks:
                        event = {
                            "title": task.get("title"),
                            "type": task.get("type", "task"),
                            "date": task.get("date"),
                            "time": task.get("time"),
                            "assigned_to": task.get("assigned_to", []),
                            "created_by": task.get("created_by"),
                            "source_message_id": task.get("source_message_id"),
                            "conversation_id": conversation_id,
                            "confidence": task.get("confidence", 0.5),
                            "extraction_method": task.get("extraction_method", "unknown"),
                            "created_at": now,
                            "status": "pending"  # pending, completed, cancelled
                        }
                        events_collection.insert_one(event)
                        
    except Exception as e:
        # Log error but don't fail message sending
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error extracting tasks from message: {e}")
    
    return msg

def get_all_users_for_chat(exclude_id=None):
    """Get users for selecting to chat (names and login ids)"""
    users = get_users_collection()
    query = {}
    if exclude_id:
        query["login_id"] = {"$ne": exclude_id}
        
    return list(users.find(query, {"password_hash": 0}).sort("first_name", 1))

def get_user_by_login_id(login_id):
    """Get user details by login ID"""
    users = get_users_collection()
    return users.find_one({"login_id": login_id}, {"password_hash": 0})

# Events/Calendar functions
def create_event(event_data):
    """Create a new calendar event"""
    events = get_events_collection()
    event_data["created_at"] = datetime.now(timezone.utc)
    result = events.insert_one(event_data)
    return result.inserted_id

def get_user_events(user_id, start_date=None, end_date=None):
    """Get events for a specific user"""
    events = get_events_collection()
    query = {"assigned_to": user_id}
    
    # Add date range filter if provided
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["date"] = date_query
    
    return list(events.find(query).sort("date", 1))

def get_events_by_date(user_id, date):
    """Get events for a specific user on a specific date"""
    events = get_events_collection()
    return list(events.find({
        "assigned_to": user_id,
        "date": date
    }).sort("time", 1))

def update_event_status(event_id, status):
    """Update event status (pending, completed, cancelled)"""
    events = get_events_collection()
    result = events.update_one(
        {"_id": event_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0

def delete_event(event_id, user_id):
    """Delete an event (only if user is assigned or created it)"""
    events = get_events_collection()
    result = events.delete_one({
        "_id": event_id,
        "$or": [
            {"assigned_to": user_id},
            {"created_by": user_id}
        ]
    })
    return result.deleted_count > 0

def get_all_events_for_user(user_id):
    """Get all events for a user (including past events)"""
    events = get_events_collection()
    return list(events.find({"assigned_to": user_id}).sort("date", -1))

def get_conversation_participants(conversation_id):
    """Get all participants in a conversation"""
    convos = get_conversations_collection()
    conversation = convos.find_one({"conversation_id": conversation_id})
    return conversation.get("participants", []) if conversation else []

