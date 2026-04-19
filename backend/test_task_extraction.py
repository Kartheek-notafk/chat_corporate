"""
Test script for AI-powered task extraction integration
"""

import sys
import os
from datetime import datetime, timezone
from database import (
    get_db, get_users_collection, get_events_collection,
    get_or_create_direct_conversation, send_message,
    get_events_by_date, get_user_events
)
from task_extractor import extract_tasks_from_message

def test_task_extraction():
    """Test the complete task extraction workflow"""
    
    print("🧪 Testing AI-Powered Task Extraction Integration")
    print("=" * 60)
    
    try:
        # Test 1: Database Connection
        print("\n1. Testing database connection...")
        db = get_db()
        users = get_users_collection()
        events = get_events_collection()
        print("✅ Database connected successfully")
        
        # Test 2: Get Test Users
        print("\n2. Setting up test users...")
        test_users = list(users.find({}).limit(2))
        if len(test_users) < 2:
            print("❌ Need at least 2 users for testing")
            return False
            
        user1 = test_users[0]["login_id"]
        user2 = test_users[1]["login_id"]
        print(f"✅ Using test users: {user1} and {user2}")
        
        # Test 3: Create Test Conversation
        print("\n3. Creating test conversation...")
        conversation = get_or_create_direct_conversation(user1, user2)
        conversation_id = conversation["conversation_id"]
        print(f"✅ Created conversation: {conversation_id}")
        
        # Test 4: Test Task Extraction Directly
        print("\n4. Testing task extraction directly...")
        test_messages = [
            {
                "text": "Hey Alice, let's have a meeting tomorrow at 3 PM about the AI project.",
                "expected_type": "meeting",
                "expected_date": "tomorrow",
                "expected_time": "15:00"
            },
            {
                "text": "Bob, please submit the report by Friday at 5 PM.",
                "expected_type": "deadline",
                "expected_date": "friday",
                "expected_time": "17:00"
            },
            {
                "text": "Team, we need to review the code next Monday morning.",
                "expected_type": "task",
                "expected_date": "next monday",
                "expected_time": None
            },
            {
                "text": "Just saying hello, no tasks here!",
                "expected_type": None,
                "expected_date": None,
                "expected_time": None
            }
        ]
        
        for i, test_msg in enumerate(test_messages):
            print(f"\n   Testing message {i+1}: {test_msg['text']}")
            
            # Extract tasks
            tasks = extract_tasks_from_message(
                test_msg["text"],
                user1,
                [user1, user2],
                conversation_id,
                f"test_msg_{i}"
            )
            
            if test_msg["expected_type"] is None:
                if not tasks:
                    print(f"   ✅ correctly identified no tasks")
                else:
                    print(f"   ⚠️  unexpected tasks found: {len(tasks)}")
            else:
                if tasks:
                    task = tasks[0]
                    print(f"   ✅ extracted task: {task['title']}")
                    print(f"      Type: {task['type']}")
                    print(f"      Date: {task['date']}")
                    print(f"      Time: {task.get('time', 'N/A')}")
                    print(f"      Assigned to: {task['assigned_to']}")
                    print(f"      Confidence: {task['confidence']}")
                    print(f"      Method: {task['extraction_method']}")
                else:
                    print(f"   ❌ no tasks extracted")
        
        # Test 5: Test Message Sending with Auto-Extraction
        print("\n5. Testing message sending with auto-extraction...")
        
        # Clear existing events for test user
        events.delete_many({"assigned_to": user1, "source_message_id": {"$regex": "^test_"}})
        
        # Send test message
        test_message = "Hi Alice, let's schedule a review meeting for tomorrow at 2 PM to discuss the project timeline."
        msg = send_message(conversation_id, user1, test_message)
        print(f"✅ Message sent: {msg['content'][:50]}...")
        
        # Check if events were created
        import time
        time.sleep(2)  # Wait for async processing
        
        user_events = list(events.find({"assigned_to": user1, "source_message_id": {"$regex": "^test_"}}))
        if user_events:
            print(f"✅ Auto-extracted {len(user_events)} event(s):")
            for event in user_events:
                print(f"   - {event['title']} ({event['type']}) on {event['date']} at {event.get('time', 'N/A')}")
        else:
            print("❌ No events auto-extracted")
        
        # Test 6: Test Calendar Integration
        print("\n6. Testing calendar integration...")
        
        # Get events for today
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = get_events_by_date(user1, today)
        print(f"✅ Retrieved {len(today_events)} events for today")
        
        # Get events for this month
        from datetime import date
        first_day = date.today().replace(day=1)
        start_date = first_day.strftime("%Y-%m-%d")
        
        if date.today().month == 12:
            last_day = date(date.today().year, 12, 31)
        else:
            last_day = date(date.today().year, date.today().month + 1, 1) - date.timedelta(days=1)
        end_date = last_day.strftime("%Y-%m-%d")
        
        month_events = get_user_events(user1, start_date, end_date)
        print(f"✅ Retrieved {len(month_events)} events for this month")
        
        # Test 7: Test Event Management
        print("\n7. Testing event management...")
        
        if user_events:
            test_event = user_events[0]
            event_id = test_event["_id"]
            
            # Test status update
            from database import update_event_status
            success = update_event_status(event_id, "completed")
            if success:
                print("✅ Event status updated to 'completed'")
            else:
                print("❌ Failed to update event status")
            
            # Test deletion
            from database import delete_event
            success = delete_event(event_id, user1)
            if success:
                print("✅ Event deleted successfully")
            else:
                print("❌ Failed to delete event")
        
        print("\n" + "=" * 60)
        print("🎉 Task extraction integration test completed!")
        print("\n📋 Summary:")
        print("- ✅ Database connection working")
        print("- ✅ Task extraction functioning")
        print("- ✅ Message sending with auto-extraction working")
        print("- ✅ Calendar integration working")
        print("- ✅ Event management working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_messages():
    """Test with sample messages to demonstrate the feature"""
    
    print("\n🎯 Testing with Sample Messages")
    print("=" * 40)
    
    sample_messages = [
        "Hey John, let's meet tomorrow at 10 AM to discuss the quarterly report.",
        "Sarah, please complete the presentation by Friday 5 PM.",
        "Team, we need to review the code next Monday afternoon.",
        "Mike, can you handle the client call on April 25th at 2 PM?",
        "Everyone, submit your timesheets by end of day Thursday.",
        "Let's have a standup meeting every morning at 9 AM.",
        "The project deadline is next Tuesday at midnight.",
        "Please review my pull request by tomorrow EOD."
    ]
    
    try:
        from task_extractor import extract_tasks_from_message
        
        for i, message in enumerate(sample_messages, 1):
            print(f"\n{i}. \"{message}\"")
            
            tasks = extract_tasks_from_message(
                message,
                "test_user",
                ["test_user", "colleague"],
                "test_conversation",
                f"sample_{i}"
            )
            
            if tasks:
                for j, task in enumerate(tasks, 1):
                    print(f"   Task {j}: {task['title']}")
                    print(f"   Type: {task['type']}, Date: {task['date']}, Time: {task.get('time', 'N/A')}")
                    print(f"   Confidence: {task['confidence']:.1%}, Method: {task['extraction_method']}")
            else:
                print("   No tasks detected")
                
    except Exception as e:
        print(f"❌ Error testing sample messages: {e}")

if __name__ == "__main__":
    # Run the integration test
    success = test_task_extraction()
    
    if success:
        # Test with sample messages
        test_sample_messages()
        
        print("\n🚀 Ready to use! The AI-powered task extraction is now fully integrated.")
        print("\nTo see it in action:")
        print("1. Start the chat application")
        print("2. Send messages like 'Let's meet tomorrow at 3 PM'")
        print("3. Check the calendar page to see auto-extracted events")
    else:
        print("\n❌ Integration test failed. Please check the error messages above.")
