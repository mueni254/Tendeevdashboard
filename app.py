import streamlit as st
from geopy.distance import geodesic
import requests
import math
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Twende EV", layout="centered")

# Hardcoded login credentials
USERS = {
    "user@example.com": "password123",
    "admin@twende.com": "adminpass"
}

# Hardcoded charging stations
CHARGING_STATIONS = [
    {"name": "Karen Hub Station", "location": "Karen, Nairobi", "coords": (-1.3127, 36.7191)},
    {"name": "Galleria Mall Station", "location": "Langata, Nairobi", "coords": (-1.3626, 36.7578)},
    {"name": "The Hub EV Station", "location": "Kilimani, Nairobi", "coords": (-1.2987, 36.7754)},
]

# Load Mapbox API Key
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# ----------------------------------
# Utility Functions
# ----------------------------------

def authenticate(email, password):
    return USERS.get(email) == password

def find_coordinates(location):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
    params = {"access_token": MAPBOX_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["features"]:
            coords = data["features"][0]["center"]
            return coords[1], coords[0]  # lat, lon
    return None

def find_nearest_stations(user_coords, stations=CHARGING_STATIONS, top_n=3):
    results = []
    for station in stations:
        distance_km = geodesic(user_coords, station["coords"]).km
        results.append((station, round(distance_km, 2)))
    results.sort(key=lambda x: x[1])
    return results[:top_n]

def show_welcome():
    st.title("Welcome to Twende EV")
    st.subheader("Powering the Future of Mobility – One Charge at a Time")

    st.markdown("""
    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.  
    Twende EV is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best—so you can focus on the road ahead.

    ### Key Benefits:
    - 🚗 **Smart Charging**: No more guesswork—get precise, data-driven charging recommendations.  
    - 🛣️ **Journey Confidence**: Plan routes with real-time battery and station insights.  
    - 🛠️ **Proactive Maintenance**: Stay ahead with alerts and diagnostics tailored to your EV.

    ---
    """)
    st.success("Drive Smarter. Charge Smarter. Use the sidebar to get started.")

def battery_range_estimate(vehicle_type, vehicle_cc, battery_capacity, charge_pct):
    efficiency_km_per_kWh = 6  # basic assumption
    usable_kWh = battery_capacity * (charge_pct / 100)
    estimated_range = usable_kWh * efficiency_km_per_kWh
    return round(estimated_range, 1)

def show_battery_chart():
    st.subheader("🔋 Battery Analytics")
    charges = list(range(0, 101, 10))
    distances = [battery_range_estimate("Sedan", 1500, 50, c) for c in charges]
    fig, ax = plt.subplots()
    ax.plot(charges, distances, marker='o')
    ax.set_xlabel("Charge Level (%)")
    ax.set_ylabel("Estimated Range (km)")
    ax.set_title("Battery Charge vs. Estimated Driving Range")
    st.pyplot(fig)

# ----------------------------------
# Login Page
# ----------------------------------

def login_page():
    st.title("🔐 Login to Twende EV")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if authenticate(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success(f"Welcome back, {email}!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

# ----------------------------------
# Main Dashboard
# ----------------------------------

def dashboard():
    st.sidebar.title("Navigation")
    selected = st.sidebar.radio("Choose Action", ["🏠 Welcome", "🔋 Battery Estimator", "📍 Find Charging Stations", "📈 Battery Analytics", "🚪 Logout"])

    if selected == "🏠 Welcome":
        show_welcome()

    elif selected == "🔋 Battery Estimator":
        st.subheader("🔋 Estimate EV Range")
        vehicle_type = st.selectbox("Vehicle Type", ["Sedan", "SUV", "Truck"])
        vehicle_cc = st.number_input("Engine CC", 1000, 5000, 1500)
        battery_capacity = st.number_input("Battery Capacity (kWh)", 10, 150, 50)
        charge_pct = st.slider("Current Charge (%)", 0, 100, 80)
        if st.button("Calculate Range"):
            range_km = battery_range_estimate(vehicle_type, vehicle_cc, battery_capacity, charge_pct)
            st.success(f"Estimated Range: {range_km} km")

    elif selected == "📍 Find Charging Stations":
        st.subheader("📍 Find Nearby Charging Stations")
        user_location = st.text_input("Enter your location (e.g., Langata, Nairobi)")
        if st.button("Search"):
            coords = find_coordinates(user_location)
            if coords:
                nearest = find_nearest_stations(coords)
                for station, distance in nearest:
                    st.markdown(f"**{station['name']}**  \n📍 {station['location']}  \n📏 {distance} km away")
            else:
                st.warning("Could not determine location.")

    elif selected == "📈 Battery Analytics":
        show_battery_chart()

    elif selected == "🚪 Logout":
        st.session_state.logged_in = False
        st.experimental_rerun()

# ----------------------------------
# Run App
# ----------------------------------

def run_app():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        dashboard()
    else:
        login_page()

if __name__ == "__main__":
    run_app()



