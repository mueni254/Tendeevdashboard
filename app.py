import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import json
import os

# --------------------------
# USER AUTH SYSTEM
# --------------------------

USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

def register_user(email, password):
    users = load_users()
    if email in users:
        return False
    users[email] = {"password": password}
    save_users(users)
    return True

def login_user(email, password):
    users = load_users()
    return email in users and users[email]["password"] == password

def logout_user():
    for key in ["authenticated", "email"]:
        if key in st.session_state:
            del st.session_state[key]

# --------------------------
# CHARGING STATION LOCATOR
# --------------------------

geolocator = Nominatim(user_agent="ev_app")

CHARGING_STATIONS = [
    {"name": "ABC EV Station - Nairobi", "location": (-1.2921, 36.8219)},
    {"name": "XYZ Power Charge - Westlands", "location": (-1.2675, 36.8121)},
    {"name": "E-Moto FastCharge - Kiambu", "location": (-1.1596, 36.8445)},
    {"name": "RapidCharge EV - Karen", "location": (-1.3337, 36.6997)}
]

def geocode_location(location_name):
    try:
        loc = geolocator.geocode(location_name)
        return (loc.latitude, loc.longitude) if loc else None
    except:
        return None

def get_nearest_charging_stations(coords, num=3):
    stations_with_distance = []
    for station in CHARGING_STATIONS:
        dist = geodesic(coords, station["location"]).km
        stations_with_distance.append({**station, "distance": dist})
    return sorted(stations_with_distance, key=lambda x: x["distance"])[:num]

def show_map(center, stations):
    m = folium.Map(location=center, zoom_start=12)
    folium.Marker(center, tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)
    for s in stations:
        folium.Marker(location=s["location"], tooltip=s["name"], icon=folium.Icon(color='green')).add_to(m)
    st_folium(m, width=700)

# --------------------------
# MAIN PAGES
# --------------------------

def show_welcome_message():
    st.markdown("""
        ## 👋 Welcome to Twende EV
        ### Powering the Future of Mobility – One Charge at a Time

        Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.  
        **Twende EV** is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best—so you can focus on the road ahead.

        **Key Benefits**:
        - 🔋 Smart Charging: No more guesswork—get precise, data-driven charging recommendations.
        - 🗺️ Journey Confidence: Plan routes with real-time battery and station insights.
        - 🔧 Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

        **Drive Smarter. Charge Smarter.**  
        *Log in now to take full command of your electric journey.*

        ---
    """)

def register():
    st.header("🔐 Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if register_user(email, password):
            st.success("Registered successfully! Please log in.")
        else:
            st.error("User already exists.")

def login():
    st.header("🔓 Log In")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if login_user(email, password):
            st.session_state.authenticated = True
            st.session_state.email = email
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

def dashboard():
    st.title("🚘 Twende EV Dashboard")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

    # Range Calculator
    st.markdown("## 🔋 Estimate Your EV Range")
    vehicle_reg = st.text_input("Vehicle Registration Number")
    vehicle_type = st.selectbox("Vehicle Type", ["Car", Van", "Bike"])
    vehicle_cc = st.number_input("Engine CC", min_value=50, max_value=5000, step=50)
    battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=5.0, max_value=200.0, value=40.0)

    if st.button("Estimate Range"):
        est_range = battery_capacity * 6  # Approx. 6 km per kWh
        st.success(f"Estimated range for your {vehicle_type} ({vehicle_reg}) is {est_range:.2f} km.")

    # Charging Station Search
    st.markdown("## 📍 Find Nearby Charging Stations")
    location = st.text_input("Enter location (e.g., Nairobi, Kenya)", value="Nairobi, Kenya")

    if "location_coords" not in st.session_state:
        st.session_state["location_coords"] = None
    if "stations" not in st.session_state:
        st.session_state["stations"] = []

    if st.button("Find Stations"):
        coords = geocode_location(location)
        if coords:
            st.session_state["location_coords"] = coords
            st.session_state["stations"] = get_nearest_charging_stations(coords)
        else:
            st.error("Could not geocode the location.")

    if st.session_state["location_coords"] and st.session_state["stations"]:
        st.success(f"Found {len(st.session_state['stations'])} stations near {location}")
        for s in st.session_state["stations"]:
            st.write(f"- {s['name']} ({s['distance']:.2f} km away)")
        show_map(st.session_state["location_coords"], st.session_state["stations"])

# --------------------------
# MAIN APP
# --------------------------

def main():
    st.set_page_config(page_title="Twende EV", layout="wide")
    show_welcome_message()

    if "authenticated" in st.session_state and st.session_state["authenticated"]:
        dashboard()
    else:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login()
        with tab2:
            register()

if __name__ == "__main__":
    main()





