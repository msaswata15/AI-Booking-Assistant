import google.generativeai as genai
import os

import google.generativeai as genai
import os

def gemini_extract_slots(message: str) -> dict:
    """
    Use Gemini to extract booking slots from a user message.
    Returns a dict with keys: date, time, duration, title (values or None)
    """
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Google Gemini API key not set in GOOGLE_GEMINI_API_KEY env var.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    prompt = (
        "Extract the following booking details from this message as JSON: "
        "date (YYYY-MM-DD), time (HH:MM or range), duration (e.g. one hour, thirty minutes), and title (meeting/call/appointment). "
        "If a detail is missing, set its value to null. "
        "Always use written numbers (e.g., 'one hour' not '1 hour'). "
        f"Message: {message}\n"
        "Respond ONLY with a single JSON object, with no extra text."
    )
    response = model.generate_content(prompt)
    import json
    text = response.text.strip()
    if '```' in text:
        text = text.split('```')[-1].replace('json','').strip()
    try:
        first_brace = text.index('{')
        last_brace = text.rindex('}')
        json_str = text[first_brace:last_brace+1]
        slots = json.loads(json_str)
        return slots
    except Exception:
        return {}
    import json
    # Try to robustly extract JSON from Gemini output
    text = response.text.strip()
    if '```' in text:
        text = text.split('```')[-1].replace('json','').strip()
    # Remove any non-JSON prefix/suffix
    try:
        first_brace = text.index('{')
        last_brace = text.rindex('}')
        json_str = text[first_brace:last_brace+1]
        slots = json.loads(json_str)
        return slots
    except Exception:
        return {}
