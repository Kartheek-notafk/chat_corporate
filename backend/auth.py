import bcrypt
import re
from database import get_users_collection, get_next_sequence_number

# Department and role codes mapping
DEPARTMENTS = {
    "dev": "Developer",
    "hrs": "Human Resources", 
    "fin": "Finance",
    "mkt": "Marketing",
    "sal": "Sales",
    "sup": "Support"
}

ROLES = {
    "adm": "Admin",
    "man": "Manager",
    "asm": "Assistant Manager",
    "tld": "Team Lead",
    "sen": "Senior Employee",
    "clk": "Clerk",
    "int": "Intern"
}

def validate_login_id(login_id):
    """Validate login ID format: [dept][role][6-digit number]"""
    if not login_id.strip():
        return False, "Login ID is required."
    
    pattern = r"^[a-z]{3}[a-z]{3}[0-9]{6}$"
    if not re.match(pattern, login_id.strip().lower()):
        return False, "Invalid login ID format. Use format: [department][role][6-digit number]"
    
    dept_code = login_id[:3].lower()
    role_code = login_id[3:6].lower()
    
    if dept_code not in DEPARTMENTS:
        return False, f"Invalid department code: {dept_code}"
    
    if role_code not in ROLES:
        return False, f"Invalid role code: {role_code}"
    
    return True, ""

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must contain at least one special character (@, #, $ ...)."
    return True, ""

def validate_name(name, field):
    if not name.strip():
        return False, f"{field} is required."
    if len(name.strip()) < 2:
        return False, f"{field} must be at least 2 characters."
    if not re.match(r"^[A-Za-z\s'-]+$", name.strip()):
        return False, f"{field} can only contain letters, spaces, hyphens, apostrophes."
    return True, ""

def generate_login_id(department_code, role_code):
    """Generate login ID with format: [dept][role][6-digit number]"""
    next_num = get_next_sequence_number(department_code, role_code)
    return f"{department_code}{role_code}{next_num:06d}"

def register_user(first_name, last_name, department_code, role_code):
    """Register a new user with automatic login ID generation"""
    errors = []
    
    ok, msg = validate_name(first_name, "First Name")
    if not ok: errors.append(msg)
    ok, msg = validate_name(last_name, "Last Name")
    if not ok: errors.append(msg)
    
    if department_code not in DEPARTMENTS:
        errors.append(f"Invalid department: {department_code}")
    
    if role_code not in ROLES:
        errors.append(f"Invalid role: {role_code}")
    
    if errors:
        return False, "\n".join(errors), None, None
    
    users = get_users_collection()
    
    # Generate login ID
    login_id = generate_login_id(department_code, role_code)
    
    # Check if login ID already exists (shouldn't happen with proper sequencing)
    if users.find_one({"login_id": login_id}):
        return False, "Login ID already exists. Please try again.", None, None
    
    # Set initial password same as login ID
    initial_password = login_id
    hashed_password = bcrypt.hashpw(initial_password.encode(), bcrypt.gensalt()).decode('utf-8')  # Convert to string for JSON storage
    
    # Create user
    user_data = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "login_id": login_id,
        "password_hash": hashed_password,
        "department": DEPARTMENTS[department_code],
        "department_code": department_code,
        "role": ROLES[role_code],
        "role_code": role_code,
        "password_changed": False,  # User must change password on first login
        "created_at": "2026-03-28"
    }
    
    users.insert_one(user_data)
    
    return True, "User registered successfully!", login_id, initial_password

def login_user(login_id, password):
    if not login_id.strip():
        return False, "Login ID is required.", None
    if not password:
        return False, "Password is required.", None
    
    # Validate login ID format
    ok, msg = validate_login_id(login_id)
    if not ok:
        return False, msg, None
    
    users = get_users_collection()
    user = users.find_one({"login_id": login_id.strip()})
    if not user:
        return False, "No account found with that login ID.", None
    # Handle both string and bytes password hashes
    password_hash = user["password_hash"]
    if isinstance(password_hash, str):
        password_hash = password_hash.encode('utf-8')
    
    if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
        return False, "Incorrect password.", None
    
    return True, "Login successful!", {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "role_code": user["role_code"],
        "department": user["department"],
        "department_code": user["department_code"],
        "login_id": user["login_id"],
        "password_changed": user.get("password_changed", True),
    }

def change_password(login_id, current_password, new_password, confirm_password):
    """Change user password"""
    errors = []
    
    if not current_password:
        errors.append("Current password is required.")
    
    ok, msg = validate_password(new_password)
    if not ok:
        errors.append(msg)
    
    if new_password != confirm_password:
        errors.append("New passwords do not match.")
    
    if errors:
        return False, "\n".join(errors)
    
    users = get_users_collection()
    user = users.find_one({"login_id": login_id})
    
    if not user:
        return False, "User not found."
    
    # Handle both string and bytes password hashes
    password_hash = user["password_hash"]
    if isinstance(password_hash, str):
        password_hash = password_hash.encode('utf-8')
    
    if not bcrypt.checkpw(current_password.encode('utf-8'), password_hash):
        return False, "Current password is incorrect."
    
    # Update password
    new_hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode('utf-8')  # Convert to string for JSON storage
    users.update_one(
        {"login_id": login_id},
        {"$set": {"password_hash": new_hashed, "password_changed": True}}
    )
    
    return True, "Password changed successfully!"
