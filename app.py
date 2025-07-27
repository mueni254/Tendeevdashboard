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

def register_user(email, password, vehicle_type, vehicle_cc, battery_capacity, consumption_rate, vehicle_reg):
    if email in users:
        return False
    users[email] = {
        "password": password,
        "vehicle_type": vehicle_type,
        "vehicle_cc": vehicle_cc,
        "battery_capacity": battery_capacity,       # in kWh
        "consumption_rate": consumption_rate,      # kWh per 100km
        "vehicle_reg": vehicle_reg                   # Vehicle Registration Number
    }
    return True

def login_user(email, password):
    return email in users and users[email]["password"] == password

def logout_user():
    st.session_state["authenticated"] = False

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
# EV Range Calculator
# -----------------------
def calculate_range(battery_capacity, consumption_rate):
    # consumption_rate is kWh per 100 km
    if consumption_rate <= 0:
        return 0
    estimated_range = (battery_capacity / consumption_rate) * 100  # in km
    return estimated_range

# -----------------------
# Login Page with Welcome Message
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

Ready to redefine your EV experience?
""")

    if "show_login_form" not in st.session_state:
        st.session_state["show_login_form"] = False

    if not st.session_state["show_login_form"]:
        if st.button("Get Started"):
            st.session_state["show_login_form"] = True
            st.experimental_rerun()
    else:
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
# Registration Page with Vehicle Details and Vehicle Reg Number
# -----------------------
def register_page():
    st.title("📝 Register")

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        vehicle_type = st.selectbox("Vehicle Type", ["Electric Car", "Electric Motorcycle", "Electric Tuk-Tuk", "Other"])
        vehicle_cc = st.number_input("Engine CC", min_value=0, step=1)
        battery_capacity = st.number_input("Battery Capacity (kWh)", min_value=0.0, format="%.2f")
        consumption_rate = st.number_input("Consumption Rate (kWh per 100km)", min_value=0.0, format="%.2f")
        vehicle_reg = st.text_input("Vehicle Registration Number")
        submit = st.form_submit_button("Register")

    if submit:
        if register_user(email, password, vehicle_type, vehicle_cc, battery_capacity, consumption_rate, vehicle_reg):
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
# Dashboard Page with Vehicle Registration Number Displayed
# -----------------------
def dashboard():
    st.title("🔋 EV Charging Station Finder")

    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

    st.markdown(f"**Logged in as:** {st.session_state.get('email')}")

    # Show user's vehicle info
    user = users.get(st.session_state.get("email"), {})
    if user:
        st.markdown(f"**Your Vehicle Registration:** {user.get('vehicle_reg', 'N/A')}")
        st.markdown(f"**Vehicle Type:** {user.get('vehicle_type', 'N/A')}, Engine CC: {user.get('vehicle_cc', 'N/A')}")
        st.markdown(f"Battery Capacity: {user.get('battery_capacity', 0)} kWh")
        st.markdown(f"Consumption Rate: {user.get('consumption_rate', 0)} kWh/100km")

        ev_range = calculate_range(user.get('battery_capacity', 0), user.get('consumption_rate', 0))
        st.markdown(f"**Estimated EV Range:** {ev_range:.1f} km")

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
    if "show_login_form" not in st.session_state:
        st.session_state["show_login_form"] = False

    if is_authenticated():
        dashboard()
    elif st.session_state["show_register"]:
        register_page()
    else:
        login_page()

if __name__ == "__main__":
    main()



