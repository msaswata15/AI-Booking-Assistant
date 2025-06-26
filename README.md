# AI Booking Assistant

Conversational agent to book appointments on Google Calendar using FastAPI, LangGraph, and Streamlit.

## Setup

### 1. Clone the Repository
```
git clone <your-repo-url>
cd tailor-talk
```

### 2. Environment Variables
Create a `.env` file in the `backend/` directory with the following content:

```
GOOGLE_APPLICATION_CREDENTIALS=serviceaccount.json
GOOGLE_CALENDAR_ID=your-calendar-id@gmail.com
GEMINI_API_KEY=your-gemini-api-key-here
```
- Replace `your-calendar-id@gmail.com` with your Google Calendar ID.
- Replace `your-gemini-api-key-here` with your Gemini API key.
- Place your Google service account JSON as `serviceaccount.json` in the project root or update the path accordingly.

**Note:** `.env` and `serviceaccount.json` are included in `.gitignore` to prevent accidental commits of sensitive data.

### 3. Backend
```
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### 4. Frontend
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
