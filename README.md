# AI Booking Assistant

Conversational agent to book appointments on Google Calendar using FastAPI, LangGraph, and Streamlit.

## How to Run

### Backend
```
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### Frontend
```
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Make sure the backend is running before starting the frontend.

## Features
- Natural language booking
- Checks calendar availability
- Books confirmed slots

## To Do
- Implement LangGraph agent logic
- Integrate Google Calendar API
- Handle edge cases and confirmations
