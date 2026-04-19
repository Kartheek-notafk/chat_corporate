import re
from dateutil import parser as dateparser

def extract_schedule_signals(messages: list[str]) -> dict:
    busy_slots = []
    patterns = [r"\b(meeting|call|standup|sync)\b.{0,40}\b(\d{1,2}(:\d{2})?\s?(am|pm)?)\b"]
    for msg in messages:
        for pat in patterns:
            if re.search(pat, msg, re.IGNORECASE):
                busy_slots.append(msg)
    return {"busy_mentions": busy_slots}

STATUS_SIGNALS = {
    "done": ["shipped", "deployed", "completed", "finished", "merged"],
    "blocked": ["blocked", "stuck", "waiting on", "can't proceed"],
    "in_progress": ["working on", "in progress", "started", "WIP"],
}

def extract_project_status(messages: list[str]) -> dict:
    status_map = {}
    for msg in messages:
        for status, keywords in STATUS_SIGNALS.items():
            if any(kw in msg.lower() for kw in keywords):
                status_map[msg[:60]] = status
    return status_map