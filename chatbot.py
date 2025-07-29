import requests
import streamlit as st

# Load Groq API key from Streamlit secrets
GROQ_API_KEY = st.secrets["groq"]["api_key"]

def chatbot_assistant(user_message):
    """
    Send user_message to Groq API and get the chatbot reply.
    """
    url = "https://api.groq.ai/v1/chat/completions"  # Example endpoint, confirm with Groq docs
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",  # or your desired model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EV owners."},
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        # Parse the chatbot reply from the response JSON structure (adjust as per Groq API spec)
        reply = response_json["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        return f"Sorry, I couldn't get a response. Error: {str(e)}"
