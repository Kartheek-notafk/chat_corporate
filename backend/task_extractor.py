"""
AI-powered Task Extraction Module for Corporate Chat Application

This module automatically detects meetings, deadlines, and tasks from chat messages
and converts them into structured calendar events.
"""

import re
import json
import logging
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
from typing import List, Dict, Optional, Any
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskExtractor:
    """AI-powered task extraction from chat messages"""
    
    def __init__(self):
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    def extract_tasks_from_message(self, message_text: str, sender_id: str, 
                                 participants: List[str], conversation_id: str,
                                 message_id: str) -> List[Dict[str, Any]]:
        """
        Extract tasks from a message using AI and rule-based methods
        
        Args:
            message_text: The message content
            sender_id: ID of the message sender
            participants: List of participant IDs in the conversation
            conversation_id: ID of the conversation
            message_id: ID of the message
            
        Returns:
            List of extracted tasks as dictionaries
        """
        tasks = []
        
        try:
            # First try AI-based extraction
            ai_tasks = self._extract_with_ai(message_text, sender_id, participants, message_id)
            tasks.extend(ai_tasks)
            
            # Fallback to rule-based extraction if AI fails
            if not ai_tasks:
                rule_tasks = self._extract_with_rules(message_text, sender_id, participants, message_id)
                tasks.extend(rule_tasks)
                
        except Exception as e:
            logger.error(f"Error extracting tasks from message: {e}")
            # Try rule-based as fallback
            try:
                rule_tasks = self._extract_with_rules(message_text, sender_id, participants, message_id)
                tasks.extend(rule_tasks)
            except Exception as fallback_error:
                logger.error(f"Rule-based extraction also failed: {fallback_error}")
        
        return tasks
    
    def _extract_with_ai(self, message_text: str, sender_id: str, 
                        participants: List[str], message_id: str) -> List[Dict[str, Any]]:
        """Extract tasks using Claude AI"""
        
        prompt = f"""
Extract any meetings, deadlines, or tasks from this message. Return valid JSON only.

Message: "{message_text}"

Rules:
1. Look for meetings, deadlines, tasks, follow-ups, submissions, reviews
2. Extract dates (tomorrow, next Monday, April 25, etc.)
3. Extract times if mentioned (3 PM, 15:00, etc.)
4. Identify who is assigned (names mentioned)
5. Return empty array [] if no actionable tasks found

JSON format:
{{
  "tasks": [
    {{
      "type": "meeting|deadline|task",
      "title": "brief description",
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "assigned_names": ["name1", "name2"],
      "confidence": 0.8
    }}
  ]
}}
"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Clean response to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                tasks = []
                for task_data in result.get("tasks", []):
                    # Convert names to user IDs
                    assigned_ids = self._map_names_to_user_ids(
                        task_data.get("assigned_names", []), 
                        participants
                    )
                    
                    if assigned_ids:  # Only create task if we can assign to someone
                        task = {
                            "type": task_data.get("type", "task"),
                            "title": task_data.get("title", ""),
                            "date": task_data.get("date"),
                            "time": task_data.get("time"),
                            "assigned_to": assigned_ids,
                            "created_by": sender_id,
                            "source_message_id": message_id,
                            "confidence": task_data.get("confidence", 0.5),
                            "extraction_method": "ai"
                        }
                        tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            
        return []
    
    def _extract_with_rules(self, message_text: str, sender_id: str,
                           participants: List[str], message_id: str) -> List[Dict[str, Any]]:
        """Extract tasks using rule-based patterns"""
        
        tasks = []
        
        # Task detection patterns
        task_patterns = [
            # Meeting patterns
            (r'\b(meet|meeting|call|sync|standup|discuss|talk)\b.*?\b(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|next\s+week|this\s+week)\b', 'meeting'),
            
            # Deadline patterns
            (r'\b(deadline|due|submit|deliver|complete|finish|by|before)\b.*?\b(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|next\s+week|this\s+week)\b', 'deadline'),
            
            # Task patterns
            (r'\b(task|assign|responsible|handle|work on|look into|check|review|prepare|create|update)\b.*?\b(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|next\s+week|this\s+week)\b', 'task'),
        ]
        
        # Time patterns
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',
            r'\b(\d{1,2})\s*(am|pm)\b',
            r'\b(at\s+\d{1,2}\s*(am|pm))\b'
        ]
        
        # Name patterns - look for capitalized words that might be names
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        
        for pattern, task_type in task_patterns:
            matches = re.finditer(pattern, message_text, re.IGNORECASE)
            
            for match in matches:
                # Extract the matched text
                matched_text = match.group()
                
                # Parse date
                date_str = self._extract_date_from_text(matched_text)
                if not date_str:
                    continue
                
                # Parse time
                time_str = None
                for time_pattern in time_patterns:
                    time_match = re.search(time_pattern, matched_text)
                    if time_match:
                        time_str = self._normalize_time(time_match.group())
                        break
                
                # Extract names
                names = re.findall(name_pattern, message_text)
                
                # Create title from matched text
                title = self._create_title_from_text(matched_text, task_type)
                
                # Map names to user IDs
                assigned_ids = self._map_names_to_user_ids(names, participants)
                
                if assigned_ids:  # Only create if we can assign to someone
                    task = {
                        "type": task_type,
                        "title": title,
                        "date": date_str,
                        "time": time_str,
                        "assigned_to": assigned_ids,
                        "created_by": sender_id,
                        "source_message_id": message_id,
                        "confidence": 0.6,  # Lower confidence for rule-based
                        "extraction_method": "rules"
                    }
                    tasks.append(task)
        
        return tasks
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract and normalize date from text"""
        try:
            # Common date patterns
            date_patterns = [
                r'\b(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|week))\b',
                r'\b(this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|week))\b',
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})?)\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_text = match.group()
                    
                    # Parse relative dates
                    now = datetime.now(timezone.utc)
                    if date_text.lower() == "tomorrow":
                        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
                    elif date_text.lower() == "today":
                        return now.strftime("%Y-%m-%d")
                    elif date_text.lower().startswith("next "):
                        day = date_text.lower().replace("next ", "")
                        target_date = self._get_next_weekday(day)
                        if target_date:
                            return target_date.strftime("%Y-%m-%d")
                    elif date_text.lower().startswith("this "):
                        day = date_text.lower().replace("this ", "")
                        target_date = self._get_this_weekday(day)
                        if target_date:
                            return target_date.strftime("%Y-%m-%d")
                    else:
                        # Try parsing with dateutil
                        try:
                            parsed_date = dateparser.parse(date_text, fuzzy=True)
                            if parsed_date:
                                return parsed_date.strftime("%Y-%m-%d")
                        except:
                            continue
            
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
        
        return None
    
    def _normalize_time(self, time_str: str) -> Optional[str]:
        """Normalize time string to HH:MM format"""
        try:
            # Extract time using regex
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str.lower())
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3)
                
                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                return f"{hour:02d}:{minute:02d}"
                
        except Exception as e:
            logger.error(f"Error normalizing time: {e}")
        
        return None
    
    def _get_next_weekday(self, day_name: str) -> Optional[datetime]:
        """Get date for next occurrence of specified weekday"""
        try:
            days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                   'friday': 4, 'saturday': 5, 'sunday': 6}
            
            if day_name.lower() in days:
                target_day = days[day_name.lower()]
                now = datetime.now(timezone.utc)
                current_day = now.weekday()
                
                days_ahead = (target_day - current_day) % 7
                if days_ahead == 0:  # Today, so next week
                    days_ahead = 7
                    
                return now + timedelta(days=days_ahead)
                
        except Exception as e:
            logger.error(f"Error getting next weekday: {e}")
        
        return None
    
    def _get_this_weekday(self, day_name: str) -> Optional[datetime]:
        """Get date for this week's occurrence of specified weekday"""
        try:
            days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                   'friday': 4, 'saturday': 5, 'sunday': 6}
            
            if day_name.lower() in days:
                target_day = days[day_name.lower()]
                now = datetime.now(timezone.utc)
                current_day = now.weekday()
                
                days_ahead = (target_day - current_day)
                if days_ahead < 0:  # Already passed this week
                    return None
                    
                return now + timedelta(days=days_ahead)
                
        except Exception as e:
            logger.error(f"Error getting this weekday: {e}")
        
        return None
    
    def _create_title_from_text(self, text: str, task_type: str) -> str:
        """Create a meaningful title from matched text"""
        # Clean up the text and create a concise title
        words = text.split()
        
        # Remove common filler words and keep relevant ones
        filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'for', 'to', 'with'}
        relevant_words = [word for word in words if word.lower() not in filler_words and len(word) > 2]
        
        if relevant_words:
            title = ' '.join(relevant_words[:8])  # Limit to first 8 relevant words
            title = title.capitalize()
        else:
            # Fallback titles based on type
            type_titles = {
                'meeting': 'Meeting scheduled',
                'deadline': 'Deadline set',
                'task': 'Task assigned'
            }
            title = type_titles.get(task_type, 'Task created')
        
        return title
    
    def _map_names_to_user_ids(self, names: List[str], participants: List[str]) -> List[str]:
        """Map extracted names to user IDs using participant list"""
        try:
            from database import get_users_collection
            
            users_collection = get_users_collection()
            assigned_ids = []
            
            # Get user details for all participants
            participants_data = list(users_collection.find(
                {"login_id": {"$in": participants}}, 
                {"login_id": 1, "first_name": 1, "last_name": 1}
            ))
            
            # Create name to ID mapping
            name_to_id = {}
            for user in participants_data:
                # Map by first name, last name, and full name
                first_name = user.get("first_name", "").lower()
                last_name = user.get("last_name", "").lower()
                full_name = f"{first_name} {last_name}".strip()
                
                name_to_id[first_name] = user["login_id"]
                name_to_id[last_name] = user["login_id"]
                name_to_id[full_name] = user["login_id"]
            
            # Map extracted names to IDs
            for name in names:
                name_lower = name.lower()
                
                # Direct match
                if name_lower in name_to_id:
                    assigned_ids.append(name_to_id[name_lower])
                else:
                    # Partial match (first name or last name)
                    for mapped_name, user_id in name_to_id.items():
                        if name_lower in mapped_name or mapped_name in name_lower:
                            assigned_ids.append(user_id)
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ids = []
            for user_id in assigned_ids:
                if user_id not in seen:
                    seen.add(user_id)
                    unique_ids.append(user_id)
            
            return unique_ids
            
        except Exception as e:
            logger.error(f"Error mapping names to user IDs: {e}")
            return []

# Global instance
task_extractor = TaskExtractor()

def extract_tasks_from_message(message_text: str, sender_id: str, 
                             participants: List[str], conversation_id: str,
                             message_id: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract tasks from a message
    
    Args:
        message_text: The message content
        sender_id: ID of the message sender
        participants: List of participant IDs in the conversation
        conversation_id: ID of the conversation
        message_id: ID of the message
        
    Returns:
        List of extracted tasks as dictionaries
    """
    return task_extractor.extract_tasks_from_message(
        message_text, sender_id, participants, conversation_id, message_id
    )
