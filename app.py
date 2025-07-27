import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# -----------------------
# User Storage in session_state
# -----------------------
if "users" not in st.session_state:
    st.session_state["users"] = {}

def register_user(email, password):
    users = st.session_state["users"]
    if email in users:
        return False
    users[email] = {"password": password, "vehicle_info": {}}
    st.session_state["users"] = users
    return True

def login_user(email, password):
    users = st.session_state.get("users", {})
    return email in users and users[email]["password"] == password

def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["email"] = None

def is_authenticated():
    return st.session_state.get("authenticated", False)

# -----------------------
# EV Station Fetcher
# -----------------------
def get_nearest_charging_stations(user_location, max_results=5):
    api_key = st.secrets["open_charge_map"]["api_key"]
    latitude, longitude = user_location

    url = (
        f"https://api.openchargemap.io/v3/poi/?output=json&latitude={latitude}&longitude={longitude}"
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
# Range Calculator
# -----------------------
def calculate_range(battery_capacity_kwh, vehicle_type):
    # Average consumption rates (kWh per 100 km) by vehicle type (approximate)
    consumption_rates = {
        "Motorbike": 3.0,
        "Car": 15.0,
        "Tuk-tuk": 6.0,
    }
    consumption_rate = consumption_rates.get(vehicle_type, 15.0)  # default 15 if unknown
    range_km = (battery_capacity_kwh / consumption_rate) * 100
    return range_km

# -----------------------
# Map Rendering
# -----------------------
def show_map(user_location, stations):
    m = folium.Map(location=user_location, zoom_start=12)

    # Add user location
    folium.Marker(user_location, tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)

    # Add station markers
    for station in stations:
        folium.Marker(
            location=[station["latitude"], station["longitude"]],
            popup=f"{station['name']} ({station['distance']:.2f} km)",
            icon=folium.Icon(color='green')
        ).add_to(m)

    st_folium(m, width=700)

# -----------------------
# Geocode location name to lat/lon
# -----------------------
def geocode_location(location_name):
    geolocator = Nominatim(user_agent="twende_ev_app")
    try:
        location = geolocator.geocode(location_name)
        if location:
            return (location.latitude, location.longitude)
    except:
        pass
    return None

# -----------------------
# Login Page
# -----------------------
def login_page():
    st.title("🔐 Login")

    st.markdown(
        """
        **Welcome to Twende EV**  
        *Powering the Future of Mobility – One Charge at a Time*

        Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control. Twende EV is designed to eliminate range anxiety, optimize charging efficiency, and keep your EV performing at its best—so you can focus on the road ahead.

        **Key Benefits:**  
        - Smart Charging: No more guesswork—get precise, data-driven charging recommendations.  
        - Journey Confidence: Plan routes with real-time battery and station insights.  
        - Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.  

        Drive Smarter. Charge Smarter.  
        Log in now to take full command of your electric journey.  
        Ready to redefine your EV experience? [Get Started]
        """
    )

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
# Registration Page
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
# Dashboard Page
# -----------------------
def dashboard():
    st.title("🔋 Twende EV Charging Station Finder & Range Calculator")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

    # User info
    email = st.session_state.get("email")
    user = st.session_state["users"].get(email, {})

    st.markdown(f"**Logged in as:** {email}")

    # Vehicle details input
    st.markdown("### 🚗 Enter your vehicle details")

    vehicle_type = st.selectbox("Vehicle Type", ["Motorbike", "Car", "Tuk-tuk"])
    vehicle_cc = st.text_input("Engine CC (e.g., 150)")
    battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=0.1, max_value=200.0, step=0.1, value=10.0)
    vehicle_reg = st.text_input("Vehicle Registration Number")

    # Save vehicle info in session_state users dictionary on submit
    if st.button("Save Vehicle Details"):
        user["vehicle_info"] = {
            "vehicle_type": vehicle_type,
            "vehicle_cc": vehicle_cc,
            "battery_capacity": battery_capacity,
            "vehicle_reg": vehicle_reg,
        }
        st.session_state["users"][email] = user
        st.success("Vehicle details saved!")

    # Location input by name
    st.markdown("### 📍 Enter your location (city, address, or place name)")
    location_name = st.text_input("Location")

    if st.button("Find Nearest Stations & Calculate Range"):
        if not location_name:
            st.error("Please enter a location name.")
            return

        coords = geocode_location(location_name)
        if coords is None:
            st.error("Could not find the location. Please enter a valid place name.")
            return

        stations = get_nearest_charging_stations(coords)

        if stations:
            st.success(f"Found {len(stations)} nearby stations:")
            for s in stations:
                st.write(f"- {s['name']} ({s['distance']:.2f} km)")

            show_map(coords, stations)
        else:
            st.warning("No charging stations found nearby.")

        # Calculate and show range if vehicle info is available
        vehicle_info = user.get("vehicle_info", {})
        if vehicle_info:
            range_km = calculate_range(vehicle_info.get("battery_capacity", 0), vehicle_info.get("vehicle_type", "Car"))
            st.markdown(f"### Estimated Range: **{range_km:.1f} km** based on your vehicle's battery capacity and type.")
        else:
            st.info("Please save your vehicle details to see estimated range.")

# -----------------------
# App Entry Point
# -----------------------
def main():
    st.set_page_config(page_title="Twende EV Dashboard", layout="centered")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "show_register" not in st.session_state:
        st.session_state["show_register"] = False
    if "email" not in st.session_state:
        st.session_state["email"] = None

    if is_authenticated():
        dashboard()
    elif st.session_state["show_register"]:
        register_page()
    else:
        login_page()

if __name__ == "__main__":
    main()




