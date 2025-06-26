from dateutil import parser as date_parser
import re
import datetime
import pytz
from calendar_utils import check_availability, book_event
from gemini_utils import gemini_extract_slots

# Conversation state per user (in-memory; for demo only)
USER_STATE = {}

# Required slots for booking
REQUIRED_SLOTS = ["date", "time", "duration", "title"]

# Simple regex for time ranges (e.g., 3-5 PM)
TIME_RANGE_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*[-to]+\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.I)


def extract_datetime(message, now=None):
    """Try to extract date and time info from user message."""
    now = now or None
    try:
        dt = date_parser.parse(message, fuzzy=True, default=now)
        return dt
    except Exception:
        return None


def extract_time_range(message):
    """Extract time range if present (e.g., 3-5 PM)."""
    match = TIME_RANGE_RE.search(message)
    if match:
        return match.groups()
    return None


def get_missing_slots(state):
    return [slot for slot in REQUIRED_SLOTS if slot not in state]


def reset_state(user_id):
    USER_STATE[user_id] = {}


def parse_duration(duration_str):
    if duration_str.endswith("h"):
        return datetime.timedelta(hours=float(duration_str[:-1]))
    if duration_str.endswith("m"):
        return datetime.timedelta(minutes=float(duration_str[:-1]))
    return datetime.timedelta(hours=1)  # default


def parse_time(state):
    # Returns start_dt, end_dt (Asia/Kolkata tz-aware)
    date_str = state["date"]
    time_str = state["time"]
    duration_str = state["duration"]
    kolkata = pytz.timezone("Asia/Kolkata")
    tr = TIME_RANGE_RE.search(time_str)
    if tr:
        # Use first hour as start, last as end
        start_hour = int(tr[0])
        start_min = int(tr[1] or 0)
        start_ampm = tr[2]
        end_hour = int(tr[3])
        end_min = int(tr[4] or 0)
        end_ampm = tr[5]
        # Normalize am/pm
        if start_ampm and start_ampm.lower() == "pm" and start_hour < 12:
            start_hour += 12
        if end_ampm and end_ampm.lower() == "pm" and end_hour < 12:
            end_hour += 12
        start_dt = datetime.datetime.strptime(f"{date_str} {start_hour}:{start_min}", "%Y-%m-%d %H:%M")
        end_dt = datetime.datetime.strptime(f"{date_str} {end_hour}:{end_min}", "%Y-%m-%d %H:%M")
    else:
        # Single time + duration
        start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + parse_duration(duration_str)
    # Localize to Asia/Kolkata
    start_dt = kolkata.localize(start_dt)
    end_dt = kolkata.localize(end_dt)
    return start_dt, end_dt


def process_user_message(user_id, message):
    # Initialize or fetch state
    state = USER_STATE.get(user_id, {})
    now = None  # Could use current time

    # Handle overwrite confirmation
    if state.get('pending_overwrite'):
        if 'yes' in message.lower():
            # User confirmed overwrite
            event_id = state['pending_overwrite']['event_id']
            from calendar_utils import delete_event
            try:
                delete_event(event_id)
                # Try booking the new event
                start_dt, end_dt = state['pending_overwrite']['start_end']
                event = book_event(state['title'], start_dt, end_dt)
                reset_state(user_id)
                return f"Previous event deleted. Booked your {state['title']} on {start_dt.strftime('%A, %B %d at %I:%M %p')} for {state['duration']}."
            except Exception as e:
                reset_state(user_id)
                return f"Sorry, there was an error overwriting your appointment: {str(e)}. Please try again."
        else:
            reset_state(user_id)
            return "Okay, your previous event is unchanged. Let me know if you want to book a different slot."

    # Reset conversation
    if "reset" in message.lower():
        reset_state(user_id)
        return "Let's start over. What would you like to book?"

    # --- Use Gemini to extract slots from message ---
    # --- Improved slot extraction: always extract all slots from every message ---
    gemini_slots = {}
    gemini_warning = ''
    try:
        gemini_slots = gemini_extract_slots(message)
        print(f"[DEBUG] Gemini output: {gemini_slots}")
        if not gemini_slots:
            gemini_warning = "\n⚠️ Gemini AI is temporarily unavailable or rate-limited. Using classic extraction. Some flexible language may not be understood."
    except Exception as e:
        print(f"[DEBUG] Gemini extraction failed: {e}")
        gemini_warning = "\n⚠️ Gemini AI is temporarily unavailable or rate-limited. Using classic extraction. Some flexible language may not be understood."
    # Use all slots Gemini found, fallback to classic parsing for missing ones
    for slot in ["date", "time", "duration", "title"]:
        if gemini_slots.get(slot):
            state[slot] = gemini_slots[slot]
    # --- IMPROVED CLASSIC EXTRACTION ---
    import re as _re
    import datetime as _dt
    user_lower = message.lower()
    today = _dt.datetime.now(pytz.timezone("Asia/Kolkata")).date()
    # Date extraction
    if "today" in user_lower:
        state["date"] = today.isoformat()
    elif "tomorrow" in user_lower:
        state["date"] = (today + _dt.timedelta(days=1)).isoformat()
    elif _re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", message):
        match = _re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", message)
        d, m, y = match.group(1), match.group(2), match.group(3)
        if len(y) == 2:
            y = "20" + y
        try:
            state["date"] = _dt.date(int(y), int(m), int(d)).isoformat()
        except Exception:
            pass
    else:
        dt = extract_datetime(message)
        if dt:
            state["date"] = dt.date().isoformat()
            state["time"] = dt.strftime("%H:%M")
    # Time range extraction (8am - 9am, 10:00-11:00, etc.)
    time_range = _re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*[-to]+\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', user_lower)
    if time_range:
        # Example: 8am - 9am, 10:00 - 11:00
        t1_h = int(time_range.group(1))
        t1_m = int(time_range.group(2) or 0)
        t1_ampm = time_range.group(3)
        t2_h = int(time_range.group(4))
        t2_m = int(time_range.group(5) or 0)
        t2_ampm = time_range.group(6)
        # Normalize times
        def to_24h(h, ampm):
            if ampm == 'pm' and h < 12:
                return h + 12
            if ampm == 'am' and h == 12:
                return 0
            return h
        t1_h = to_24h(t1_h, t1_ampm)
        t2_h = to_24h(t2_h, t2_ampm)
        state["time"] = f"{t1_h:02d}:{t1_m:02d} - {t2_h:02d}:{t2_m:02d}"
        # If duration not set, infer from range
        if "duration" not in state:
            t1 = _dt.datetime(2000,1,1,t1_h,t1_m)
            t2 = _dt.datetime(2000,1,1,t2_h,t2_m)
            mins = int((t2-t1).total_seconds()//60)
            if mins >= 60:
                state["duration"] = f"{mins//60}h" if mins%60==0 else f"{mins//60}h{mins%60}m"
            else:
                state["duration"] = f"{mins}m"
    elif "time" not in state:
        dt = extract_datetime(message)
        if dt:
            state["time"] = dt.strftime("%H:%M")
    # Duration extraction (improved)
    if "duration" not in state:
        # Handle "1 hour", "2 hours", "30 min", "half an hour", etc.
        duration_patterns = [
            (r"(\d+)\s*hours?", lambda m: f"{m.group(1)}h"),
            (r"(\d+)\s*mins?", lambda m: f"{m.group(1)}m"),
            (r"(\d+)\s*minutes?", lambda m: f"{m.group(1)}m"),
            (r"(\d+)\s*h\b", lambda m: f"{m.group(1)}h"),
            (r"half an hour", lambda m: "30m"),
            (r"quarter of an hour", lambda m: "15m"),
            (r"(\d+)\s*hr", lambda m: f"{m.group(1)}h"),
            (r"(\d+)\s*m\b", lambda m: f"{m.group(1)}m"),
            (r"(one|1)\s*hour", lambda m: "1h"),
            (r"(two|2)\s*hours", lambda m: "2h"),
            (r"(three|3)\s*hours", lambda m: "3h"),
            (r"(thirty|30)\s*minutes?", lambda m: "30m"),
            (r"(fifteen|15)\s*minutes?", lambda m: "15m"),
        ]
        for pat, fmt in duration_patterns:
            m = _re.search(pat, user_lower)
            if m:
                state["duration"] = fmt(m)
                break
    # Title extraction
    if "title" not in state:
        if "meeting" in user_lower:
            state["title"] = "Meeting"
        elif "call" in user_lower:
            state["title"] = "Call"
        elif "appointment" in user_lower:
            state["title"] = "Appointment"

    # Save state
    USER_STATE[user_id] = state

    missing = get_missing_slots(state)
    if missing:
        prompts = {
            "date": "What date would you like to book?",
            "time": "What time do you prefer?",
            "duration": "How long should the appointment be?",
            "title": "What is the appointment for? (e.g., meeting, call)"
        }
        next_slot = missing[0]
        return prompts[next_slot] + " (Tip: You can use natural language, e.g. 'tomorrow 8-9am meeting')"

    # --- Real calendar check and booking ---
    try:
        start_dt, end_dt = parse_time(state)
        # Use Asia/Kolkata for both availability and booking
        from calendar_utils import get_conflicting_event
        conflict = get_conflicting_event(start_dt, end_dt)
        if conflict:
            # Ask user if they want to overwrite
            state['pending_overwrite'] = {
                'event_id': conflict['id'],
                'start_end': (start_dt, end_dt)
            }
            USER_STATE[user_id] = state
            summary = conflict.get('summary', 'an event')
            return f"There is already an event ('{summary}') at that time. Would you like to delete and overwrite it with your new booking? (yes/no)"
        event = book_event(state['title'], start_dt, end_dt)
        reset_state(user_id)
        return f"Booked your {state['title']} on {start_dt.strftime('%A, %B %d at %I:%M %p')} for {state['duration']}. You'll receive a confirmation shortly."
    except Exception as e:
        reset_state(user_id)
        return f"Sorry, there was an error booking your appointment: {str(e)}. Please try again."
