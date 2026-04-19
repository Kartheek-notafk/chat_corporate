"""
Simple script to check if calendar was updated with AI-extracted events
"""

from database import get_events_collection
from datetime import datetime

def check_calendar_updates():
    """Check for recent AI-extracted events"""
    
    print("🔍 Checking Calendar Updates")
    print("=" * 40)
    
    try:
        events = get_events_collection()
        
        # Get all AI-extracted events
        ai_events = list(events.find({
            'extraction_method': {'$in': ['ai', 'rules']}
        }).sort('created_at', -1))
        
        print(f"📊 Total AI-extracted events: {len(ai_events)}")
        
        if ai_events:
            print("\n📅 Recent AI-Extracted Events:")
            print("-" * 40)
            
            for i, event in enumerate(ai_events[:10], 1):  # Show last 10
                print(f"{i}. {event['title']}")
                print(f"   Type: {event['type']}")
                print(f"   Date: {event['date']} at {event.get('time', 'All day')}")
                print(f"   Assigned to: {', '.join(event['assigned_to'])}")
                print(f"   Confidence: {event.get('confidence', 0):.0%}")
                print(f"   Status: {event.get('status', 'pending')}")
                print(f"   Created: {event.get('created_at', 'Unknown')}")
                print()
        else:
            print("❌ No AI-extracted events found")
            print("\n💡 To create events:")
            print("1. Send messages like 'Let's meet tomorrow at 3 PM'")
            print("2. Check the calendar page")
            print("3. Look for events with '🤖 AI Extracted' badges")
        
        # Check total events
        total_events = events.count_documents({})
        print(f"\n📈 Total events in calendar: {total_events}")
        
        # Check by type
        meeting_events = events.count_documents({'type': 'meeting'})
        deadline_events = events.count_documents({'type': 'deadline'})
        task_events = events.count_documents({'type': 'task'})
        
        print(f"   Meetings: {meeting_events}")
        print(f"   Deadlines: {deadline_events}")
        print(f"   Tasks: {task_events}")
        
    except Exception as e:
        print(f"❌ Error checking calendar: {e}")

if __name__ == "__main__":
    check_calendar_updates()
