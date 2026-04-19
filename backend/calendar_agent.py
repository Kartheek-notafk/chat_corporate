"""
backend/calendar_agent.py — Agentic Calendar Sync Service (Groq-powered)
=========================================================================
Always-on background agent. Polls MongoDB for new chat messages, identifies
conversations where BOTH sides have mutually agreed on a meeting, and writes
confirmed events into calendar_events.json — which calendar.py reads live.

Usage:
    python backend/calendar_agent.py

Keep this running alongside the Streamlit app.
"""

import os
import sys
import json
import time
import logging
import datetime
import re
from pathlib import Path
from typing import Optional

from groq import Groq
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CalendarAgent] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("calendar_agent")

# ── Config ────────────────────────────────────────────────────────────────────
POLL_INTERVAL   = int(os.getenv("CALENDAR_AGENT_POLL_INTERVAL", "15"))   # seconds
MONGODB_URI     = os.getenv("MONGODB_URI", "")
DB_NAME         = os.getenv("DB_NAME", "chatapp1")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = "llama-3.3-70b-versatile"

# calendar_events.json lives next to this script (backend/)
EVENTS_FILE = Path(__file__).parent / "calendar_events.json"

# ── Groq client ───────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)

# ── Persistence helpers ───────────────────────────────────────────────────────

def load_events() -> dict:
    """Load existing events from the JSON sidecar. Keys are ISO date strings."""
    if EVENTS_FILE.exists():
        try:
            return json.loads(EVENTS_FILE.read_text())
        except Exception:
            pass
    return {}


def save_events(events: dict):
    """Persist events back to the JSON sidecar atomically."""
    tmp = EVENTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(events, indent=2))
    tmp.replace(EVENTS_FILE)
    log.info(f"Saved {sum(len(v) for v in events.values())} total event(s) to {EVENTS_FILE}")


def load_agent_state() -> dict:
    state_file = Path(__file__).parent / "calendar_agent_state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except Exception:
            pass
    return {}


def save_agent_state(state: dict):
    state_file = Path(__file__).parent / "calendar_agent_state.json"
    state_file.write_text(json.dumps(state, indent=2))

# ── MongoDB helpers ───────────────────────────────────────────────────────────

def get_db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]


def fetch_recent_conversations(db, after_id: Optional[str]) -> list[dict]:
    """
    Fetch conversations that have received new messages since last poll.
    Returns a list of {conversation_id, messages: [...]} dicts.
    """
    query = {}
    if after_id:
        try:
            query["_id"] = {"$gt": ObjectId(after_id)}
        except Exception:
            pass

    # Get recently updated messages
    recent_msgs = list(
        db.messages.find(query).sort("_id", -1).limit(100)
    )

    if not recent_msgs:
        return []

    # Group by conversation_id
    conv_map: dict[str, list] = {}
    for msg in recent_msgs:
        cid = str(msg.get("conversation_id", ""))
        if cid:
            conv_map.setdefault(cid, []).append(msg)

    # For each conversation, fetch the full recent thread (last 30 msgs)
    threads = []
    for cid, _ in conv_map.items():
        from bson import ObjectId as ObjId
        try:
            full_thread = list(
                db.messages.find({"conversation_id": ObjId(cid)})
                .sort("_id", -1)
                .limit(30)
            )
            full_thread.reverse()  # chronological order
            threads.append({
                "conversation_id": cid,
                "messages": full_thread,
            })
        except Exception as e:
            log.warning(f"Could not fetch thread {cid}: {e}")

    return threads


def get_latest_message_id(db) -> Optional[str]:
    msg = db.messages.find_one({}, sort=[("_id", -1)])
    return str(msg["_id"]) if msg else None

# ── Groq AI extraction ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a meeting detection agent for a corporate chat app.

You will receive a conversation thread between colleagues. Your job:
1. Determine if BOTH parties have mutually agreed on a specific meeting or event
   — look for explicit agreement signals: "sounds good", "confirmed", "I'll be there",
     "done", "see you then", "works for me", "let's do it", "agreed", etc.
   — a one-sided proposal with no reply/acceptance does NOT count
2. If mutual agreement exists, extract the event details

Respond ONLY with valid JSON. No prose, no markdown fences.

If a confirmed mutual meeting is found:
{
  "confirmed": true,
  "title": "meeting title",
  "date": "YYYY-MM-DD",
  "time": "HH:MM AM/PM",
  "type": "meeting|call|deadline|presentation|review",
  "participants": ["name1", "name2"],
  "notes": "brief context"
}

If no confirmed mutual meeting:
{
  "confirmed": false
}

Today's date for reference: {{TODAY}}
"""

def extract_event_from_thread(thread: list[dict]) -> Optional[dict]:
    """Send a conversation thread to Groq and extract confirmed event if any."""
    if len(thread) < 2:
        return None  # Need at least 2 messages for mutual agreement

    # Check if there are at least 2 unique senders (mutual conversation)
    senders = set(str(m.get("sender_id", m.get("sender", ""))) for m in thread)
    if len(senders) < 2:
        return None

    # Format thread for the prompt
    lines = []
    for msg in thread:
        sender = msg.get("sender_name", msg.get("sender", "Unknown"))
        content = msg.get("content", msg.get("text", msg.get("message", "")))
        ts = msg.get("created_at", msg.get("timestamp", ""))
        if isinstance(ts, datetime.datetime):
            ts = ts.strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{ts}] {sender}: {content}")

    conversation_text = "\n".join(lines)
    today = datetime.date.today().isoformat()
    system = SYSTEM_PROMPT.replace("{{TODAY}}", today)

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Conversation:\n{conversation_text}"},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()

        result = json.loads(raw)
        if result.get("confirmed"):
            log.info(f"✅ Confirmed event detected: {result.get('title')} on {result.get('date')}")
            return result
        return None

    except json.JSONDecodeError as e:
        log.warning(f"Groq returned non-JSON: {e} | raw: {raw[:200]}")
        return None
    except Exception as e:
        log.error(f"Groq API error: {e}")
        return None

# ── Event merging ─────────────────────────────────────────────────────────────

def merge_event_into_store(events: dict, extracted: dict, conv_id: str) -> bool:
    """
    Add the extracted event into the events dict if not already present.
    Returns True if a new event was added.
    """
    date_str = extracted.get("date", "")
    if not date_str:
        return False

    # Validate date format
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        log.warning(f"Invalid date from Groq: {date_str!r}")
        return False

    new_event = {
        "title":      extracted.get("title", "Meeting"),
        "time":       extracted.get("time", "TBD"),
        "type":       extracted.get("type", "meeting"),
        "notes":      extracted.get("notes", ""),
        "participants": extracted.get("participants", []),
        "source_conv": conv_id,         # track which conversation spawned this
        "auto_added":  True,
        "added_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    existing = events.get(date_str, [])

    # Deduplicate: skip if same title+date already exists
    for ev in existing:
        if ev.get("title", "").lower() == new_event["title"].lower():
            log.info(f"⏭  Skipping duplicate: {new_event['title']} on {date_str}")
            return False

    existing.append(new_event)
    events[date_str] = existing
    log.info(f"📅 Added to calendar: '{new_event['title']}' on {date_str} at {new_event['time']}")
    return True

# ── Main agent loop ───────────────────────────────────────────────────────────

def run():
    log.info("=" * 60)
    log.info("  Calendar Agent starting up")
    log.info(f"  Model   : {GROQ_MODEL}")
    log.info(f"  Poll    : every {POLL_INTERVAL}s")
    log.info(f"  Events  : {EVENTS_FILE}")
    log.info("=" * 60)

    state = load_agent_state()
    last_msg_id: Optional[str] = state.get("last_message_id")
    processed_convs: set[str] = set(state.get("processed_conversations", []))

    # Track which conversations we've already processed up to which message
    conv_watermarks: dict[str, str] = state.get("conv_watermarks", {})

    while True:
        try:
            db = get_db()

            # Discover what conversations have new activity
            threads = fetch_recent_conversations(db, last_msg_id)

            if threads:
                log.info(f"📨 Found {len(threads)} active conversation(s) to scan")
            else:
                log.debug("No new messages since last poll")

            events = load_events()
            changed = False

            for thread_data in threads:
                conv_id = thread_data["conversation_id"]
                messages = thread_data["messages"]

                if not messages:
                    continue

                # Check if this conversation has new messages since last scan
                latest_in_thread = str(messages[-1]["_id"])
                if conv_watermarks.get(conv_id) == latest_in_thread:
                    continue  # No new messages in this thread

                log.info(f"🔍 Scanning conversation {conv_id} ({len(messages)} messages)")

                extracted = extract_event_from_thread(messages)
                if extracted:
                    added = merge_event_into_store(events, extracted, conv_id)
                    if added:
                        changed = True

                # Update watermark for this conversation
                conv_watermarks[conv_id] = latest_in_thread

            if changed:
                save_events(events)

            # Update agent state
            new_last_id = get_latest_message_id(db)
            if new_last_id:
                last_msg_id = new_last_id

            save_agent_state({
                "last_message_id": last_msg_id,
                "conv_watermarks": conv_watermarks,
                "last_run": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            })

        except Exception as e:
            log.error(f"Agent loop error: {e}", exc_info=True)

        log.debug(f"Sleeping {POLL_INTERVAL}s …")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()