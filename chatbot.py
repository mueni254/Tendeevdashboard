import requests
import streamlit as st

GROQ_API_KEY = st.secrets["groq"]["api_key"]

def chatbot_assistant(user_message):
    url = "https://api.groq.com/v1/chat/completions"  # Correct chat completions endpoint
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",  # Use your API key here
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EV owners."},
            {"role": "user", "content": user_message}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        return f"Sorry, I couldn't get a response. Error: {str(e)}"


