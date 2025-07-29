import streamlit as st
import sqlite3
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.distance import geodesic
import requests
import hashlib
import datetime
import os

# -------------------------------
# CONFIG
# -------------------------------
OPENCHARGEMAP_API_KEY = st.secrets["openchargemap_api_key"]
MAPBOX_API_KEY = st.secrets["mapbox_api_key"]

# -------------------------------
# DATABASE SETUP
# -------------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT)''')

# -------------------------------
# AUTHENTICATION HELPERS
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(email, password):
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password)))
    return c.fetchone()

def create_user(email, password):
    c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
    conn.commit()

# -------------------------------
# UI SECTIONS
# -------------------------------

def welcome():
    st.markdown("""
    # Welcome to Twende EV
    ### Powering the Future of Mobility – One Charge at a Time

    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

    **Key Benefits:**
    - 🚀 Smart Charging: No more guesswork—get precise, data-driven charging recommendations.
    - 🚗 Journey Confidence: Plan routes with real-time battery and station insights.
    - ⚡ Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

    **Drive Smarter. Charge Smarter.**
    
    Log in now to take full command of your electric journey.
    """)

def register():
    st.subheader("Create an Account")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        try:
            create_user(email, password)
            st.success("Account created. Please log in.")
        except:
            st.error("User already exists.")

def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        user = check_credentials(email, password)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["user"] = email
            st.success("Logged in successfully")
        else:
            st.error("Invalid email or password")

def logout():
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user"] = None

# -------------------------------
# RANGE ESTIMATION
# -------------------------------
def estimate_range():
    st.subheader("Range Estimator")
    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Van", "Bike", "Bus", "Truck"])
    battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=10.0, value=60.0)
    battery_age = st.slider("Battery Age (years)", 0, 10, 2)
    charge_percentage = st.slider("Current Battery %", 0, 100, 80)

    age_factor = 1 - (battery_age * 0.02)  # 2% loss per year
    usable_capacity = battery_capacity * (charge_percentage / 100) * age_factor

    estimated_efficiency = 0.18  # kWh/km assumed average
    estimated_range = usable_capacity / estimated_efficiency

    st.success(f"Estimated Range: {estimated_range:.1f} km")

# -------------------------------
# NEAREST STATION LOCATOR
# -------------------------------
def nearest_station_locator():
    st.subheader("Find Nearest Charging Station")
    location_query = st.text_input("Enter your location (e.g. Nairobi, KE)")
    if st.button("Search Station"):
        geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location_query}.json?access_token={MAPBOX_API_KEY}"
        response = requests.get(geocode_url)
        if response.status_code == 200:
            features = response.json()["features"]
            if features:
                lat, lon = features[0]["center"][1], features[0]["center"][0]
                show_charging_map(lat, lon)
            else:
                st.warning("Location not found.")
        else:
            st.error("Mapbox API error.")


def show_charging_map(lat, lon):
    url = f"https://api.openchargemap.io/v3/poi/?output=json&latitude={lat}&longitude={lon}&distance=20&maxresults=10&key={OPENCHARGEMAP_API_KEY}"
    response = requests.get(url)
    data = response.json()

    m = folium.Map(location=[lat, lon], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    for station in data:
        try:
            name = station["AddressInfo"]["Title"]
            address = station["AddressInfo"].get("AddressLine1", "")
            s_lat = station["AddressInfo"]["Latitude"]
            s_lon = station["AddressInfo"]["Longitude"]
            folium.Marker([s_lat, s_lon], tooltip=f"{name}\n{address}").add_to(marker_cluster)
        except:
            continue

    st_folium(m, width=700, height=500)

# -------------------------------
# MAIN
# -------------------------------
def main():
    st.set_page_config(page_title="Twende EV Dashboard", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user"] = None

    if st.session_state["logged_in"]:
        st.sidebar.markdown(f"**Logged in as:** {st.session_state['user']}")
        logout()
        st.title("Twende EV Dashboard")
        estimate_range()
        nearest_station_locator()

    else:
        welcome()
        choice = st.selectbox("Choose Action", ["Login", "Register"])
        if choice == "Login":
            login()
        else:
            register()

if __name__ == '__main__':
    main()





