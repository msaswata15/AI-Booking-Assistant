import datetime
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# Path to your Google service account credentials JSON file
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
# The calendar ID (usually user's email or the calendar's ID)
# IMPORTANT: Set this to your Google Calendar email (not 'primary') if you are not the service account owner
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "msaswata15@gmail.com")  # e.g. 'yourname@gmail.com'

# --- AUTHENTICATION ---
def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=credentials)
    return service

# --- CHECK AVAILABILITY ---
def to_rfc3339_utc(dt: datetime.datetime) -> str:
    # Ensures RFC3339 UTC format: 2025-06-25T19:30:00Z
    return dt.astimezone(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def check_availability(start_dt: datetime.datetime, end_dt: datetime.datetime) -> bool:
    service = get_calendar_service()
    print(f"[DEBUG] Checking availability: calendarId={CALENDAR_ID}, timeMin={to_rfc3339_utc(start_dt)}, timeMax={to_rfc3339_utc(end_dt)}")
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=to_rfc3339_utc(start_dt),
        timeMax=to_rfc3339_utc(end_dt),
        maxResults=1,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    print(f"[DEBUG] Found {len(events)} events in that slot.")
    return len(events) == 0

def get_conflicting_event(start_dt: datetime.datetime, end_dt: datetime.datetime) -> dict:
    """Return the first event in the slot, or None if free."""
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=to_rfc3339_utc(start_dt),
        timeMax=to_rfc3339_utc(end_dt),
        maxResults=1,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if events:
        return events[0]
    return None

def delete_event(event_id: str):
    service = get_calendar_service()
    print(f"[DEBUG] Deleting event: {event_id}")
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    print(f"[DEBUG] Event {event_id} deleted.")

# --- BOOK EVENT ---
def book_event(summary: str, start_dt: datetime.datetime, end_dt: datetime.datetime, description: str = "") -> dict:
    service = get_calendar_service()
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': to_rfc3339_utc(start_dt),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': to_rfc3339_utc(end_dt),
            'timeZone': 'UTC',
        },
    }
    print(f"[DEBUG] Booking event: calendarId={CALENDAR_ID}, event={event}")
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"[DEBUG] Event created: {created_event}")
    return created_event

# --- USAGE ---
# To use these functions, you must:
# 1. Place your Google service account JSON in the backend directory and set the SERVICE_ACCOUNT_FILE path.
# 2. Share your Google Calendar with the service account email (found in the JSON file).
# 3. Optionally, set CALENDAR_ID to your calendar's ID or use "primary".
