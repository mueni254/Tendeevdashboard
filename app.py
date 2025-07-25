import streamlit as st
import pydeck as pdk
import pandas as pd
import requests
from geopy.geocoders import Nominatim

# Set up Mapbox token
pdk.settings.mapbox_api_key = st.secrets["mapbox"]["api_key"]

# --------------------------
# SESSION STATE SETUP
# --------------------------
if "registered_users" not in st.session_state:
    st.session_state.registered_users = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "email" not in st.session_state:
    st.session_state.email = ""

# --------------------------
# WELCOME PAGE + LOGIN FORM
# --------------------------
def show_welcome():
    st.markdown("# 🚗 Welcome to Twende EV")
    st.markdown("### Powering the Future of Mobility – One Charge at a Time")
    st.write("""
    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

    **Key Benefits**  
    - 🔋 Smart Charging: No more guesswork—get precise, data-driven charging recommendations.  
    - 🗺️ Journey Confidence: Plan routes with real-time battery and station insights.  
    - ⚙️ Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

    ---
    **Drive Smarter. Charge Smarter.**  
    Log in now to take full command of your electric journey.
    """)

    option = st.radio("Select an option", ["Log In", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            if email and password:
                st.session_state.registered_users[email] = password
                st.success("✅ Registration successful! You can now log in.")
            else:
                st.error("Please provide both email and password.")

    if option == "Log In":
        if st.button("Log In"):
            if st.session_state.registered_users.get(email) == password:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.success(f"✅ Welcome back, {email}!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

# --------------------------
# MAIN APP AFTER LOGIN
# --------------------------
def main_app():
    st.markdown(f"### 👋 Hello, {st.session_state.email}")
    st.title("EV Charging Station Finder (Nairobi)")

    location_input = st.text_input("Enter your location (e.g., Nairobi CBD):")

    if location_input:
        try:
            geolocator = Nominatim(user_agent="ev_locator")
            location = geolocator.geocode(location_input)
            if location:
                lat, lon = location.latitude, location.longitude

                # Hybrid approach
                stations = [
                    {"name": "Hardcoded Station A", "lat": -1.2921, "lon": 36.8219},
                    {"name": "Hardcoded Station B", "lat": -1.3000, "lon": 36.8155},
                    {"name": "Hardcoded Station C", "lat": -1.2800, "lon": 36.8250},
                ]

                df = pd.DataFrame(stations)

                st.map(df, latitude="lat", longitude="lon")

                st.write("### Nearest Charging Stations")
                for s in stations:
                    st.write(f"- **{s['name']}** @ ({s['lat']:.4f}, {s['lon']:.4f})")
            else:
                st.warning("📍 Location not found. Try being more specific.")
        except Exception as e:
            st.error(f"Error fetching location: {e}")

    if st.button("🔒 Log out"):
        st.session_state.authenticated = False
        st.experimental_rerun()

# --------------------------
# APP ROUTING
# --------------------------
if st.session_state.authenticated:
    main_app()
else:
    show_welcome()






