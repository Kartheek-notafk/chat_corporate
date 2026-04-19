import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import SHARED_CSS
import datetime
import json
import threading
from pathlib import Path
from database import get_events_by_date, get_user_events, update_event_status, delete_event

st.set_page_config(
    page_title="Calendar - CSM",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Auth guard
if not st.session_state.get("logged_in"):
    st.switch_page("pages/streamlit_login.py")

# ── Auto-start calendar agent as background daemon thread ─────────────────────
# globals() persists across Streamlit re-runs within the same worker process,
# so the thread is only ever spawned once — not on every page reload.
def _start_calendar_agent():
    """Run the calendar agent's blocking poll loop in a background thread."""
    try:
        backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        import calendar_agent
        calendar_agent.run()
    except Exception as e:
        import logging
        logging.getLogger("calendar_agent").error(
            f"Agent thread crashed: {e}", exc_info=True
        )

if not globals().get("_CALENDAR_AGENT_STARTED"):
    globals()["_CALENDAR_AGENT_STARTED"] = True
    _agent_thread = threading.Thread(
        target=_start_calendar_agent,
        daemon=True,          # dies automatically when Streamlit exits
        name="CalendarAgent",
    )
    _agent_thread.start()

# ── Events file path ──────────────────────────────────────────────────────────
# frontend/pages/calendar.py  →  .parent = pages/  →  .parent = frontend/
#   →  .parent = project_root/  →  / "backend" / "calendar_events.json"
EVENTS_FILE = (
    Path(__file__).resolve().parent.parent.parent / "backend" / "calendar_events.json"
)

# ── Load / merge events ───────────────────────────────────────────────────────

def load_agent_events() -> dict[datetime.date, list[dict]]:
    """
    Read calendar_events.json written by the agent.
    Keys are ISO date strings; converted to datetime.date for lookups.
    """
    if not EVENTS_FILE.exists():
        return {}
    try:
        raw: dict = json.loads(EVENTS_FILE.read_text())
        result = {}
        for date_str, evts in raw.items():
            try:
                result[datetime.date.fromisoformat(date_str)] = evts
            except ValueError:
                pass
        return result
    except Exception:
        return {}


SAMPLE_EVENTS: dict[datetime.date, list[dict]] = {
    datetime.date(2024, 3, 22): [
        {"title": "Team Meeting",     "time": "10:00 AM", "type": "meeting"},
        {"title": "Project Deadline", "time": "5:00 PM",  "type": "deadline"},
    ],
    datetime.date(2024, 3, 25): [
        {"title": "Client Call",    "time": "2:00 PM", "type": "call"},
        {"title": "Review Session", "time": "4:00 PM", "type": "review"},
    ],
    datetime.date(2024, 3, 28): [
        {"title": "Presentation", "time": "11:00 AM", "type": "presentation"},
    ],
}


def get_ai_extracted_events() -> dict[datetime.date, list[dict]]:
    """Get AI-extracted events from MongoDB for the current user"""
    try:
        user_id = st.session_state.get("user_id") or st.session_state.get("login_id")
        if not user_id:
            return {}
            
        # Get events for current month and surrounding months
        current_date = st.session_state.selected_date
        start_date = (current_date.replace(day=1) - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (current_date.replace(day=1) + datetime.timedelta(days=65)).strftime("%Y-%m-%d")
        
        events = get_user_events(user_id, start_date, end_date)
        
        # Convert to date-keyed dictionary
        result = {}
        for event in events:
            try:
                event_date = datetime.datetime.strptime(event["date"], "%Y-%m-%d").date()
                
                # Format event for display
                display_event = {
                    "title": event["title"],
                    "time": event.get("time", "All day"),
                    "type": event.get("type", "task"),
                    "auto_added": True,
                    "ai_extracted": True,
                    "confidence": event.get("confidence", 0.5),
                    "status": event.get("status", "pending"),
                    "event_id": str(event["_id"]),
                    "created_by": event.get("created_by"),
                    "source_message_id": event.get("source_message_id"),
                    "extraction_method": event.get("extraction_method", "unknown")
                }
                
                result.setdefault(event_date, []).append(display_event)
            except (ValueError, KeyError) as e:
                continue  # Skip malformed events
                
        return result
        
    except Exception as e:
        st.error(f"Error loading AI events: {e}")
        return {}

def get_all_events() -> dict[datetime.date, list[dict]]:
    """Merge sample events, agent events, and AI-extracted events"""
    merged = dict(SAMPLE_EVENTS)
    
    # Add agent events from JSON file
    for date, evts in load_agent_events().items():
        existing_titles = {e["title"].lower() for e in merged.get(date, [])}
        for ev in evts:
            if ev["title"].lower() not in existing_titles:
                merged.setdefault(date, []).append(ev)
    
    # Add AI-extracted events from MongoDB
    ai_events = get_ai_extracted_events()
    for date, evts in ai_events.items():
        existing_titles = {e["title"].lower() for e in merged.get(date, [])}
        for ev in evts:
            # Check for duplicates by title and time
            is_duplicate = False
            for existing in merged.get(date, []):
                if (existing["title"].lower() == ev["title"].lower() and 
                    existing.get("time", "") == ev.get("time", "")):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.setdefault(date, []).append(ev)
    
    return merged


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.calendar-header {
    padding: 1rem;
    background-color: #A87B33;
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.event-detail {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 0.5rem;
    border-left: 4px solid #A87B33;
}
.event-detail.auto-added { border-left-color: #2e7d32; }
.event-detail.ai-extracted { border-left-color: #1976d2; }
.ai-badge {
    display: inline-block;
    background-color: #1976d2;
    color: white;
    font-size: 0.65rem;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    margin-left: 0.4rem;
    vertical-align: middle;
}
.confidence-indicator {
    display: inline-block;
    font-size: 0.7rem;
    padding: 0.1rem 0.3rem;
    border-radius: 8px;
    margin-left: 0.3rem;
    background-color: #e3f2fd;
    color: #1976d2;
}
.event-actions {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.5rem;
}
.event-actions button {
    font-size: 0.8rem;
    padding: 0.2rem 0.5rem;
}
.agent-badge {
    display: inline-block;
    background-color: #2e7d32;
    color: white;
    font-size: 0.65rem;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    margin-left: 0.4rem;
    vertical-align: middle;
}
.agent-status {
    font-size: 0.75rem;
    color: #555;
    padding: 0.3rem 0.6rem;
    background: #f0faf0;
    border: 1px solid #c8e6c9;
    border-radius: 6px;
    margin-bottom: 0.5rem;
}
.notes-section {
    padding: 1rem;
    border-top: 1px solid #e0e0e0;
    background-color: #f8f9fa;
}
.day-header {
    font-weight: bold;
    color: #A87B33;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_back = st.columns([6, 1])
with col_title:
    st.markdown("### 📅 Calendar")
with col_back:
    if st.button("← Back", use_container_width=True):
        if st.session_state.get("role") == "admin":
            st.switch_page("pages/admin_dashboard.py")
        else:
            st.switch_page("pages/user_dashboard.py")

st.divider()

# ── Agent status banner ───────────────────────────────────────────────────────
agent_events = load_agent_events()
agent_count  = sum(len(v) for v in agent_events.values())

# Check if thread is alive
agent_thread = next(
    (t for t in threading.enumerate() if t.name == "CalendarAgent"), None
)
agent_alive = agent_thread is not None and agent_thread.is_alive()

if agent_alive:
    if EVENTS_FILE.exists():
        mtime   = datetime.datetime.fromtimestamp(EVENTS_FILE.stat().st_mtime)
        age     = datetime.datetime.now() - mtime
        age_str = (
            f"{int(age.total_seconds())}s ago"
            if age.total_seconds() < 60
            else f"{int(age.total_seconds() // 60)}m ago"
        )
        st.markdown(
            f'<div class="agent-status">🤖 <strong>Calendar Agent active</strong> — '
            f'{agent_count} AI-detected event(s) · last sync <strong>{age_str}</strong></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="agent-status">🤖 <strong>Calendar Agent active</strong> — '
            'waiting for first sync…</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div class="agent-status" style="background:#fff8e1;border-color:#ffe082;">'
        '⚠️ Calendar Agent starting up…</div>',
        unsafe_allow_html=True,
    )

# ── Calendar state ────────────────────────────────────────────────────────────
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

events = get_all_events()

# ── Layout ────────────────────────────────────────────────────────────────────
col_sidebar, col_main = st.columns([1, 3])

with col_sidebar:
    st.markdown("**My Calendar**")

    current_month = st.session_state.selected_date.replace(day=1)
    prev_month    = (current_month - datetime.timedelta(days=1)).replace(day=1)
    next_month    = (current_month + datetime.timedelta(days=32)).replace(day=1)

    col_prev, col_month, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("←", use_container_width=True):
            st.session_state.selected_date = prev_month
            st.rerun()
    with col_month:
        st.markdown(f"**{current_month.strftime('%B %Y')}**")
    with col_next:
        if st.button("→", use_container_width=True):
            st.session_state.selected_date = next_month
            st.rerun()

    st.markdown("---")

    year, month = st.session_state.selected_date.year, st.session_state.selected_date.month
    first_day   = datetime.date(year, month, 1)
    if month == 12:
        last_day = datetime.date(year, 12, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    start_weekday = first_day.weekday()

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, d in enumerate(weekdays):
        with cols[i]:
            st.markdown(
                f"<div style='text-align:center;font-weight:bold;font-size:0.8rem;'>{d}</div>",
                unsafe_allow_html=True,
            )

    day = 1
    for week in range(6):
        cols = st.columns(7)
        for weekday in range(7):
            with cols[weekday]:
                if week == 0 and weekday < start_weekday:
                    st.markdown("")
                elif day > last_day.day:
                    st.markdown("")
                else:
                    current_date = datetime.date(year, month, day)
                    is_today    = current_date == datetime.date.today()
                    is_selected = current_date == st.session_state.selected_date
                    has_auto    = any(
                        e.get("auto_added") for e in events.get(current_date, [])
                    )
                    has_ai      = any(
                        e.get("ai_extracted") for e in events.get(current_date, [])
                    )
                    has_events  = current_date in events

                    bg        = "#fff3cd" if is_selected else "#e8f5e8" if is_today else "#ffffff"
                    if has_ai:
                        dot_color = "#1976d2"
                    elif has_auto:
                        dot_color = "#2e7d32"
                    else:
                        dot_color = "#A87B33"

                    # Single clickable div that combines display and functionality
                    button_style = f"""
                    background-color:{bg};border:1px solid #A87B33;border-radius:5px;
                    padding:0.5rem;text-align:center;cursor:pointer;width:100%;
                    {"border:2px solid #A87B33;" if is_selected else ""}
                    """
                    
                    if st.button(f"**{day}**", 
                               key=f"sel_{year}_{month}_{day}", 
                               use_container_width=True,
                               help=f"Events: {len(events.get(current_date, []))}"):
                        st.session_state.selected_date = current_date
                        st.rerun()
                    
                    # Show event indicator dot below the button
                    if has_events:
                        st.markdown(f"""
                        <div style='text-align:center;margin-top:-5px;margin-bottom:5px;'>
                            <div style='width:6px;height:6px;background-color:{dot_color};
                                       border-radius:50%;display:inline-block;'></div>
                        </div>
                        """, unsafe_allow_html=True)

                    day += 1
        if day > last_day.day:
            break

    st.markdown("---")
    st.markdown("**Notes**")
    st.text_area("Add notes for today:", height=100, key="daily_notes")
    if st.button("Save Notes", use_container_width=True):
        st.success("Notes saved!")

    st.markdown("---")
    st.markdown("**Settings**")
    
    # Auto-task creation toggle
    if "auto_task_creation" not in st.session_state:
        st.session_state.auto_task_creation = True
    
    auto_tasks = st.checkbox(
        "🤖 Auto-create tasks from chats", 
        value=st.session_state.auto_task_creation,
        help="Automatically extract meetings, deadlines, and tasks from chat messages"
    )
    st.session_state.auto_task_creation = auto_tasks
    
    if auto_tasks:
        st.markdown("""
        <div style='font-size:0.8rem;color:#666;margin-top:0.5rem;'>
        ✅ Tasks will be automatically extracted from chat messages and added to your calendar.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='font-size:0.8rem;color:#666;margin-top:0.5rem;'>
        ⚠️ Chat messages will not be automatically converted to calendar events.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Statistics (cached)
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def get_user_statistics(user_id):
        try:
            all_user_events = get_user_events(user_id)
            ai_events = [e for e in all_user_events if e.get("extraction_method") in ["ai", "rules"]]
            manual_events = [e for e in all_user_events if e.get("extraction_method") not in ["ai", "rules"]]
            return len(all_user_events), len(ai_events), len(manual_events)
        except:
            return 0, 0, 0
    
    user_id = st.session_state.get("user_id") or st.session_state.get("login_id")
    if user_id:
        total, ai_count, manual_count = get_user_statistics(user_id)
        st.markdown("**📊 Statistics**")
        st.markdown(f"• Total events: {total}")
        st.markdown(f"• AI-extracted: {ai_count}")
        st.markdown(f"• Manual: {manual_count}")
    
    st.markdown("---")
    if st.checkbox("🔄 Auto-refresh (20s)", value=False):
        import time
        time.sleep(20)
        st.rerun()

with col_main:
    st.markdown(f"""
    <div class="calendar-header">
        <span>{st.session_state.selected_date.strftime('%B %d, %Y')}</span>
        <span>Personal Calendar</span>
    </div>
    """, unsafe_allow_html=True)

    selected_events = events.get(st.session_state.selected_date, [])

    if selected_events:
        st.markdown(f"**{len(selected_events)} Event(s)**")
        for i, event in enumerate(selected_events):
            is_auto      = event.get("auto_added", False)
            is_ai_extracted = event.get("ai_extracted", False)
            
            # Determine styling and badges
            if is_ai_extracted:
                border_color = "#1976d2"
                confidence = event.get("confidence", 0.5)
                badge = f'<span class="ai-badge">🤖 AI Extracted</span>'
                confidence_badge = f'<span class="confidence-indicator">{int(confidence*100)}% confidence</span>'
            elif is_auto:
                border_color = "#2e7d32"
                badge = '<span class="agent-badge">🤖 AI detected</span>'
                confidence_badge = ""
            else:
                border_color = "#A87B33"
                badge = ""
                confidence_badge = ""
            
            participants = event.get("participants", [])
            participants_html = (
                f"<div style='color:#555;font-size:0.8rem;margin-top:0.3rem;'>"
                f"👥 {', '.join(participants)}</div>"
            ) if participants else ""
            
            notes_html = (
                f"<div style='color:#666;font-size:0.85rem;margin-top:0.3rem;"
                f"font-style:italic;'>{event.get('notes','')}</div>"
            ) if event.get("notes") else ""
            
            # Status indicator for AI events
            status_html = ""
            if is_ai_extracted and event.get("status"):
                status = event.get("status", "pending")
                status_colors = {
                    "pending": "#ff9800",
                    "completed": "#4caf50", 
                    "cancelled": "#f44336"
                }
                status_color = status_colors.get(status, "#ff9800")
                status_html = f"<span style='color:{status_color};font-size:0.8rem;font-weight:bold;'>● {status.title()}</span>"

            st.markdown(f"""
            <div class="event-detail {'auto-added' if is_auto else ''} {'ai-extracted' if is_ai_extracted else ''}"
                 style="border-left-color:{border_color};">
                <div style="font-weight:bold;">{event['title']}{badge} {confidence_badge}</div>
                <div style="color:#666;font-size:0.9rem;">
                    🕐 {event['time']} · {event['type'].title()} {status_html}
                </div>
                {participants_html}
                {notes_html}
            </div>
            """, unsafe_allow_html=True)
            
            # Add action buttons for AI-extracted events
            if is_ai_extracted:
                col_complete, col_cancel, col_delete = st.columns([1, 1, 1])
                with col_complete:
                    if st.button("✅ Complete", key=f"complete_{i}", use_container_width=True):
                        try:
                            update_event_status(event["event_id"], "completed")
                            st.success("Event marked as completed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating event: {e}")
                
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_{i}", use_container_width=True):
                        try:
                            update_event_status(event["event_id"], "cancelled")
                            st.success("Event cancelled!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating event: {e}")
                
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                        try:
                            user_id = st.session_state.get("user_id") or st.session_state.get("login_id")
                            if delete_event(event["event_id"], user_id):
                                st.success("Event deleted!")
                                st.rerun()
                            else:
                                st.error("Could not delete event")
                        except Exception as e:
                            st.error(f"Error deleting event: {e}")
                
                st.markdown("---")
    else:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#999;">
            <div style="font-size:2rem;margin-bottom:1rem;">📅</div>
            <div>No events scheduled for this day</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Add New Event**")
    col_t, col_ti, col_ty = st.columns([2, 1, 1])
    with col_t:
        event_title = st.text_input("Event Title")
    with col_ti:
        event_time = st.time_input("Time")
    with col_ty:
        event_type = st.selectbox(
            "Type", ["meeting", "call", "deadline", "presentation", "review"]
        )

    if st.button("Add Event", type="primary"):
        if event_title:
            all_evts = load_agent_events()
            date_key = st.session_state.selected_date.isoformat()
            new_ev = {
                "title":      event_title,
                "time":       event_time.strftime("%I:%M %p"),
                "type":       event_type,
                "auto_added": False,
                "added_at":   datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            all_evts.setdefault(date_key, []).append(new_ev)
            try:
                tmp = EVENTS_FILE.with_suffix(".tmp")
                tmp.write_text(json.dumps(all_evts, indent=2))
                tmp.replace(EVENTS_FILE)
                st.success("Event added!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save event: {e}")
        else:
            st.error("Please enter an event title")

    st.markdown("---")
    st.markdown("**Daily Notes**")
    st.markdown(f"""
    <div class="notes-section">
        <div class="day-header">Notes for {st.session_state.selected_date.strftime('%B %d, %Y')}</div>
        <div style="background-color:#ffffff;padding:1rem;border-radius:5px;min-height:100px;">
            Today's focus: Complete project documentation and prepare for tomorrow's presentation.
        </div>
    </div>
    """, unsafe_allow_html=True)