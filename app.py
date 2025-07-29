import streamlit as st
import sqlite3
import hashlib
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from math import radians, cos, sin, asin, sqrt
from streamlit.components.v1 import html
import openchargemap
import plotly.graph_objects as go

# ----------------------- DATABASE FUNCTIONS -----------------------

def create_usertable():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(email TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def add_userdata(email, password):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('INSERT INTO users(email, password) VALUES (?, ?)', (email, password))
    conn.commit()
    conn.close()

def login_user(email, password):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email =? AND password = ?', (email, password))
    data = c.fetchall()
    conn.close()
    return data

# ----------------------- HASHING -----------------------

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# ----------------------- GEOCODING AND DISTANCE -----------------------

def geocode(place_name):
    geolocator = Nominatim(user_agent="twende_ev")
    location = geolocator.geocode(place_name)
    if location:
        return location.latitude, location.longitude
    return None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# ----------------------- STATIONS -----------------------
charging_stations = {
    "Nairobi CBD": ( -1.286389, 36.817223),
    "Westlands": (-1.2676, 36.8110),
    "Kilimani": (-1.3003, 36.7831),
    "Karen": (-1.3202, 36.7205),
    "Thika": (-1.0333, 37.0707),
    "Juja": (-1.1019, 37.0144)
}

# ----------------------- APP FUNCTIONS -----------------------

def register():
    st.subheader("Create a New Account")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type='password', key="reg_password")
    if st.button("Register"):
        create_usertable()
        hashed_pw = make_hashes(password)
        add_userdata(email, hashed_pw)
        st.success("Account created successfully. Please log in.")

def login():
    st.subheader("Log In")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type='password', key="login_password")
    if st.button("Log In"):
        create_usertable()
        hashed_pw = make_hashes(password)
        result = login_user(email, hashed_pw)
        if result:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Logged in successfully")
        else:
            st.error("Invalid email or password")

# ----------------------- RANGE ESTIMATION -----------------------

def gauge_chart(range_km):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = range_km,
        title = {'text': "Estimated Range (km)"},
        gauge = {
            'axis': {'range': [0, 500]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 200], 'color': "red"},
                {'range': [200, 400], 'color': "orange"},
                {'range': [400, 500], 'color': "lightgreen"},
            ]
        }))
    st.plotly_chart(fig)

def range_estimator():
    st.subheader("🔋 EV Range Estimator")

    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Van", "Bike", "Bus", "Truck"])
    battery_age = st.slider("Battery Age (in years)", 0, 10, 2)
    battery_charge = st.slider("Battery Charge Remaining (%)", 0, 100, 80)

    base_range = {
        "Car": 400,
        "Van": 350,
        "Bike": 150,
        "Bus": 300,
        "Truck": 250
    }[vehicle_type]

    age_factor = 1 - (battery_age * 0.02)
    final_range = base_range * (battery_charge / 100) * age_factor

    st.info(f"Estimated Remaining Range: {final_range:.2f} km")
    gauge_chart(final_range)

# ----------------------- CHARGING STATIONS -----------------------

def charging_station_locator():
    st.subheader("📍 Find Nearest Charging Stations")
    user_location = st.text_input("Enter your current location (e.g. Westlands, Karen)", key="user_location")

    if user_location:
        user_lat, user_lon = geocode(user_location)
        if user_lat is not None:
            sorted_stations = sorted(
                charging_stations.items(),
                key=lambda x: haversine(user_lat, user_lon, x[1][0], x[1][1])
            )[:3]

            st.success("Top 3 nearest stations:")
            for name, (lat, lon) in sorted_stations:
                dist = haversine(user_lat, user_lon, lat, lon)
                st.write(f"{name}: {dist:.2f} km")

            m = folium.Map(location=[user_lat, user_lon], zoom_start=12)
            folium.Marker([user_lat, user_lon], tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)
            for name, (lat, lon) in charging_stations.items():
                folium.Marker([lat, lon], tooltip=name, icon=folium.Icon(color='green')).add_to(m)
            st_folium(m, width=700)
        else:
            st.error("Could not find location. Please enter a recognizable place name.")

# ----------------------- MAIN -----------------------

def main():
    st.set_page_config(page_title="Twende EV Dashboard", layout="wide")

    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>Welcome to Twende EV</h1>
        <h3>Powering the Future of Mobility – One Charge at a Time</h3>
        <p>Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.<br>
        Twende EV is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best.</p>
        <ul style='text-align: left;'>
            <li><b>Smart Charging:</b> No more guesswork—get precise, data-driven charging recommendations.</li>
            <li><b>Journey Confidence:</b> Plan routes with real-time battery and station insights.</li>
            <li><b>Proactive Maintenance:</b> Stay ahead with alerts and diagnostics tailored to your EV.</li>
        </ul>
        <p><b>Drive Smarter. Charge Smarter.</b><br>Log in now to take full command of your electric journey.</p>
        <hr>
    </div>
    """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        option = st.sidebar.radio("Choose Option", ["Login", "Register"])
        if option == "Login":
            login()
        else:
            register()
    else:
        menu = st.sidebar.radio("Main Menu", ["Range Estimator", "Charging Stations"])
        if menu == "Range Estimator":
            range_estimator()
        elif menu == "Charging Stations":
            charging_station_locator()

if __name__ == '__main__':
    main()





