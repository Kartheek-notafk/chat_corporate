import os
import bcrypt
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_db():
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        try:
            _client = MongoClient(uri, serverSelectionTimeoutMS=6000)
            _client.admin.command("ping")
        except OperationFailure as e:
            raise OperationFailure(f"MongoDB Auth Failed: {e}")
        except ServerSelectionTimeoutError:
            raise ServerSelectionTimeoutError(
                "Cannot reach MongoDB Atlas. Whitelist your IP in Atlas → Network Access."
            )
    return _client[os.getenv("DB_NAME", "chatapp1")]

def get_users_collection():
    return get_db()["users"]

def get_next_sequence_number(department_code, role_code):
    """Get the next sequential number for a department-role combination"""
    users = get_users_collection()
    pattern = f"^{department_code}{role_code}"
    last_user = users.find_one({"login_id": {"$regex": pattern}}, sort=[("login_id", -1)])
    
    if last_user:
        last_number = int(last_user["login_id"][-6:])
        return last_number + 1
    else:
        return 1

def create_admin_accounts():
    """Create pre-registered admin accounts for each department"""
    departments = {
        "dev": "Developer",
        "hrs": "Human Resources", 
        "fin": "Finance",
        "mkt": "Marketing",
        "sal": "Sales",
        "sup": "Support"
    }
    
    users = get_users_collection()
    
    for dept_code, dept_name in departments.items():
        login_id = f"{dept_code}adm000000"
        
        # Check if admin already exists
        if users.find_one({"login_id": login_id}):
            print(f"Admin {login_id} already exists")
            continue
            
        # Hash the password (same as login_id)
        hashed_password = bcrypt.hashpw(login_id.encode(), bcrypt.gensalt())
        
        # Create admin account
        admin_user = {
            "first_name": dept_name,
            "last_name": "Administrator",
            "login_id": login_id,
            "password_hash": hashed_password,
            "department": dept_name,
            "department_code": dept_code,
            "role": "admin",
            "role_code": "adm",
            "password_changed": False,  # Admin must change password on first login
            "created_at": "2026-03-28"
        }
        
        users.insert_one(admin_user)
        print(f"Created admin account: {login_id}")

if __name__ == "__main__":
    create_admin_accounts()
    print("Admin accounts creation completed!")
