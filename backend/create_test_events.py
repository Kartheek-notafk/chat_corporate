"""
Create test AI-extracted events to demonstrate the calendar feature
"""

from database import get_events_collection, get_users_collection
from datetime import datetime, timezone, timedelta

def create_test_events():
    """Create sample AI-extracted events for demonstration"""
    
    print("🎯 Creating Test AI-Extracted Events")
    print("=" * 40)
    
    try:
        # Get a test user
        users = get_users_collection()
        test_user = users.find_one()
        
        if not test_user:
            print("❌ No users found. Please create a user first.")
            return
        
        user_id = test_user["login_id"]
        print(f"👤 Using test user: {user_id}")
        
        events = get_events_collection()
        
        # Create sample events
        sample_events = [
            {
                "title": "Team Meeting about AI Project",
                "type": "meeting",
                "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "15:00",
                "assigned_to": [user_id],
                "created_by": user_id,
                "source_message_id": "test_msg_001",
                "conversation_id": "test_conversation",
                "confidence": 0.85,
                "extraction_method": "ai",
                "created_at": datetime.now(timezone.utc),
                "status": "pending"
            },
            {
                "title": "Submit Project Report",
                "type": "deadline",
                "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "17:00",
                "assigned_to": [user_id],
                "created_by": user_id,
                "source_message_id": "test_msg_002",
                "conversation_id": "test_conversation",
                "confidence": 0.90,
                "extraction_method": "ai",
                "created_at": datetime.now(timezone.utc),
                "status": "pending"
            },
            {
                "title": "Code Review Session",
                "type": "task",
                "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "10:00",
                "assigned_to": [user_id],
                "created_by": user_id,
                "source_message_id": "test_msg_003",
                "conversation_id": "test_conversation",
                "confidence": 0.75,
                "extraction_method": "rules",
                "created_at": datetime.now(timezone.utc),
                "status": "pending"
            }
        ]
        
        # Insert events
        inserted_count = 0
        for event in sample_events:
            try:
                result = events.insert_one(event)
                print(f"✅ Created: {event['title']} on {event['date']}")
                inserted_count += 1
            except Exception as e:
                print(f"❌ Failed to create {event['title']}: {e}")
        
        print(f"\n🎉 Successfully created {inserted_count} test events!")
        
        # Verify creation
        total_events = events.count_documents({})
        ai_events = events.count_documents({'extraction_method': {'$in': ['ai', 'rules']}})
        
        print(f"\n📊 Calendar Statistics:")
        print(f"   Total events: {total_events}")
        print(f"   AI-extracted: {ai_events}")
        
        print(f"\n🔍 To verify in the application:")
        print(f"1. Run: cd frontend && python -m streamlit run home.py")
        print(f"2. Login as: {user_id}")
        print(f"3. Go to Calendar page")
        print(f"4. Look for events with blue borders and '🤖 AI Extracted' badges")
        print(f"5. Check dates: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}, {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}, {(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}")
        
    except Exception as e:
        print(f"❌ Error creating test events: {e}")

if __name__ == "__main__":
    create_test_events()
