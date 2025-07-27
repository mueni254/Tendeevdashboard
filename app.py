import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# -----------------------
# In-memory user storage
# -----------------------
users = {}

def register_user(email, password):
    if email in users:
        return False
    users[email] = {
        "password": password,
        # Placeholder vehicle info, can be updated later
        "vehicle_type": None,
        "vehicle_cc": None,
        "battery_capacity": None,
        "vehicle_reg": None,
    }
    return True

def login_user(email, password):
    return email in users and users[email]["password"] == password

def logout_user():
    st.session_state["authenticated"] = False
    st.session_state.pop("email", None)

def is_authenticated():
    return st.session_state.get("authenticated", False)

# -----------------------
# EV Station Fetcher
# -----------------------
def get_nearest_charging_stations(user_location, max_results=3):
    api_key = st.secrets["open_charge_map"]["api_key"]
    latitude, longitude = user_location

    url = (
        f"https://api.openchargemap.io/v3/poi/?output=json"
        f"&latitude={latitude}&longitude={longitude}"
        f"&distance=20&distanceunit=KM&maxresults=20&key={api_key}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch charging stations.")
        return []

    data = response.json()
    stations = []

    for station in data:
        if "AddressInfo" in station:
            station_info = {
                "name": station["AddressInfo"].get("Title", "Unknown"),
                "latitude": station["AddressInfo"]["Latitude"],
                "longitude": station["AddressInfo"]["Longitude"],
                "distance": geodesic(user_location, (station["AddressInfo"]["Latitude"], station["AddressInfo"]["Longitude"])).km,
            }
            stations.append(station_info)

    stations.sort(key=lambda x: x["distance"])
    return stations[:max_results]

# -----------------------
# Map Rendering
# -----------------------
def show_map(user_location, stations):
    m = folium.Map(location=user_location, zoom_start=12)

    # Add user location marker
    folium.Marker(user_location, tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)

    # Add charging station markers
    for station in stations:
        folium.Marker(
            location=[station["latitude"], station["longitude"]],
            popup=f"{station['name']} ({station['distance']:.2f} km)",
            icon=folium.Icon(color='green')
        ).add_to(m)

    st_folium(m, width=700)

# -----------------------
# Default average consumption rates per vehicle type (kWh per 100km)
# -----------------------
DEFAULT_CONSUMPTION = {
    "Electric Car": 20.0,        # average 20 kWh/100km
    "Electric Motorcycle": 8.0,  # average 8 kWh/100km
    "Electric Tuk-Tuk": 10.0,    # average 10 kWh/100km
    "Other": 15.0,
    None: 15.0,                  # fallback average
}

# -----------------------
# EV Range Calculator without user input for consumption rate
# -----------------------
def calculate_range(battery_capacity, vehicle_type):
    consumption_rate = DEFAULT_CONSUMPTION.get(vehicle_type, 15.0)
    if battery_capacity is None or battery_capacity <= 0:
        return 0
    estimated_range = (battery_capacity / consumption_rate) * 100  # in km
    return estimated_range

# -----------------------
# Login & Welcome Page (combined)
# -----------------------
def login_page():
    st.title("Welcome to Twende EV")

    st.markdown("""
**Powering the Future of Mobility – One Charge at a Time**

Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control. Twende EV is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best—so you can focus on the road ahead.

**Key Benefits:**
- Smart Charging: No more guesswork—get precise, data-driven charging recommendations.
- Journey Confidence: Plan routes with real-time battery and station insights.
- Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

**Drive Smarter. Charge Smarter.**

Log in now to take full command of your electric journey.
""")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if login_user(email, password):
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown("Don't have an account?")
    if st.button("Register"):
        st.session_state["show_register"] = True
        st.experimental_rerun()

# -----------------------
# Registration Page (email + password only)
# -----------------------
def register_page():
    st.title("📝 Register")

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Register")

    if submit:
        if register_user(email, password):
            st.success("Registration successful. You can now login.")
            st.session_state["show_register"] = False
            st.experimental_rerun()
        else:
            st.error("Email already registered.")

    st.markdown("Already have an account?")
    if st.button("Back to Login"):
        st.session_state["show_register"] = False
        st.experimental_rerun()

# -----------------------
# Dashboard Page with vehicle info input and range calculation
# -----------------------
def dashboard():
    st.title("🔋 EV Charging Station Finder")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

    st.markdown(f"**Logged in as:** {st.session_state.get('email')}")

    user = users.get(st.session_state.get("email"), {})

    # Collect or update vehicle details here
    with st.expander("Update Vehicle Details (Optional)"):
        vehicle_type = st.selectbox(
            "Vehicle Type",
            ["Electric Car", "Electric Motorcycle", "Electric Tuk-Tuk", "Other"],
            index=["Electric Car", "Electric Motorcycle", "Electric Tuk-Tuk", "Other"].index(user.get("vehicle_type", "Electric Car")) if user.get("vehicle_type") else 0,
        )
        battery_capacity = st.number_input(
            "Battery Capacity (kWh)",
            min_value=0.0,
            format="%.2f",
            value=user.get("battery_capacity") if user.get("battery_capacity") else 0.0
        )
        vehicle_reg = st.text_input("Vehicle Registration Number", value=user.get("vehicle_reg", ""))

        # Save changes button
        if st.button("Save Vehicle Details"):
            user["vehicle_type"] = vehicle_type
            user["battery_capacity"] = battery_capacity
            user["vehicle_reg"] = vehicle_reg
            st.success("Vehicle details updated.")

    # Calculate range if battery_capacity provided
    if user.get("battery_capacity") and user.get("battery_capacity") > 0:
        ev_range = calculate_range(user.get("battery_capacity"), user.get("vehicle_type"))
        st.markdown(f"**Estimated EV Range:** {ev_range:.1f} km (based on typical consumption for your vehicle type)")

    # Location input by place name
    location_name = st.text_input("Enter your location (e.g., city or address)", value="Nairobi")

    if st.button("Find Nearest Stations"):
        if not location_name.strip():
            st.error("Please enter a valid location name.")
            return

        geolocator = Nominatim(user_agent="twende_ev_app")
        location = geolocator.geocode(location_name)
        if location is None:
            st.error("Location not found. Please enter a valid location name.")
            return

        user_location = (location.latitude, location.longitude)
        stations = get_nearest_charging_stations(user_location)

        if stations:
            st.success(f"Found {len(stations)} nearby stations:")
            for s in stations:
                st.write(f"- {s['name']} ({s['distance']:.2f} km)")

            show_map(user_location, stations)
        else:
            st.warning("No charging stations found nearby.")

# -----------------------
# App Entry Point
# -----------------------
def main():
    st.set_page_config(page_title="Twende EV Dashboard", layout="centered")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "show_register" not in st.session_state:
        st.session_state["show_register"] = False

    if is_authenticated():
        dashboard()
    elif st.session_state["show_register"]:
        register_page()
    else:
        login_page()

if __name__ == "__main__":
    main()



