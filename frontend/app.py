import streamlit as st
import requests

st.set_page_config(page_title="AI Booking Assistant")
st.title("\U0001F4C5 AI Booking Assistant")

BACKEND_URL = "http://localhost:8000"
USER_ID = "demo-user"

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("How can I help you book?"):
    # Always append what the user typed, no filtering
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Streamlit will rerun automatically after chat_input

# Always show every user message in chat history
# Find the last user message that hasn't been answered
if (
    st.session_state["messages"]
    and st.session_state["messages"][-1]["role"] == "user"
    and (len(st.session_state["messages"]) == 1 or st.session_state["messages"][-2]["role"] == "assistant")
):
    prompt = st.session_state["messages"][-1]["content"]
    with st.spinner("Thinking..."):
        response = requests.post(
            BACKEND_URL + "/chat",
            json={"user_id": USER_ID, "message": prompt},
        )
        msg = response.json().get("response", "")
        if not msg:
            msg = "Sorry, I didn’t understand that. Please try again."
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    # Streamlit will rerun automatically after chat_input
