import streamlit as st
from geopy.distance import geodesic
import requests

# Set page config
st.set_page_config(page_title="Twende EV", layout="centered")

# Load Mapbox API Key
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]

# Dummy charging stations
charging_stations = [
    {"name": "Karen Charging Hub", "lat": -1.317, "lon": 36.707},
    {"name": "Junction Mall Charger", "lat": -1.312, "lon": 36.782},
    {"name": "Galleria EV Point", "lat": -1.329, "lon": 36.721},
]

# --- LOGIN PAGE ---
def login_page():
    st.title("🔒 Login to Twende EV")
    st.subheader("Drive Smarter. Charge Smarter.")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
        else:
            st.warning("Please enter both email and password.")

# --- WELCOME PAGE ---
def show_welcome():
    st.title("⚡ Welcome to Twende EV")
    st.subheader("Powering the Future of Mobility – One Charge at a Time")

    st.markdown("""
    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

    **Key Benefits:**
    - 🚘 Smart Charging: No more guesswork—get precise, data-driven charging recommendations.
    - 🧭 Journey Confidence: Plan routes with real-time battery and station insights.
    - 🔧 Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

    **Ready to redefine your EV experience?**
    """)

# --- EV RANGE CALCULATOR ---
def range_calculator():
    st.subheader("🔋 EV Range Calculator")
    
    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Motorcycle", "Tuk-tuk"])
    vehicle_cc = st.number_input("Vehicle Engine Size (cc)", min_value=50, step=50)
    battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=1.0)
    charge_percent = st.slider("Current Battery Charge (%)", 0, 100, 50)

    if st.button("Calculate Range"):
        efficiency_factor = 5  # km per kWh baseline
        if vehicle_type == "Motorcycle":
            efficiency_factor = 10
        elif vehicle_type == "Tuk-tuk":
            efficiency_factor = 7

        usable_kwh = (charge_percent / 100) * battery_capacity
        estimated_range = usable_kwh * efficiency_factor

        st.success(f"Estimated range: {estimated_range:.2f} km")

# --- LOCATION SEARCH ---
def find_nearby_stations():
    st.subheader("📍 Find Nearby Charging Stations")

    location = st.text_input("Enter a location (e.g. Langata)")
    
    if st.button("Search"):
        if not location:
            st.warning("Please enter a location.")
            return

        # Geocode the user input using Mapbox
        geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{location}.json"
        params = {"access_token": MAPBOX_API_KEY}
        response = requests.get(geocode_url, params=params)
        data = response.json()

        try:
            coords = data['features'][0]['center']
            user_loc = (coords[1], coords[0])
        except (IndexError, KeyError):
            st.error("Unable to geocode location.")
            return

        # Find nearest charging stations
        nearby = sorted(charging_stations, key=lambda x: geodesic(user_loc, (x["lat"], x["lon"])).km)[:3]

        if not nearby:
            st.warning("No charging stations found nearby.")
        else:
            st.markdown("**Nearest Stations:**")
            for station in nearby:
                dist = geodesic(user_loc, (station["lat"], station["lon"])).km
                st.write(f"🔌 {station['name']} – {dist:.2f} km away")

# --- MAIN DASHBOARD ---
def main_dashboard():
    show_welcome()
    range_calculator()
    find_nearby_stations()

# --- APP ENTRYPOINT ---
def run_app():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        main_dashboard()
    else:
        login_page()

if __name__ == "__main__":
    run_app()


