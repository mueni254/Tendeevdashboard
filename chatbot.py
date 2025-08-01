import requests
import streamlit as st

GROQ_API_KEY = st.secrets["groq"]["api_key"]

def chatbot_response(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",  # choose a supported Groq model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EV owners."},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Sorry, I couldn't get a response. Error: {str(e)}"



