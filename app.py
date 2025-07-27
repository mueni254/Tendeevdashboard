import streamlit as st
import sqlite3
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# -------------------- Database Setup --------------------
conn = sqlite3.connect('twende_ev_users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        user_id INTEGER,
        vehicle_type TEXT,
        vehicle_cc TEXT,
        battery_capacity REAL,
        registration_number TEXT
    )
''')
conn.commit()

# -------------------- Authentication --------------------
def register():
    st.subheader("Register")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    if st.button("Register"):
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            st.success("Registration successful. Please log in.")
        except sqlite3.IntegrityError:
            st.error("This email is already registered.")

def login():
    st.subheader("Login")
    st.markdown("""
    ### Welcome to Twende EV  
    **Powering the Future of Mobility – One Charge at a Time**

    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

    #### Key Benefits:
    - Smart Charging: No more guesswork—get precise, data-driven charging recommendations.
    - Journey Confidence: Plan routes with real-time battery and station insights.
    - Proactive Maintenance: Stay ahead with alerts and diagnostics tailored to your EV.

    **Drive Smarter. Charge Smarter.**
    Log in now to take full command of your electric journey.
    """)

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.email = email
            st.success(f"Welcome back, {email}!")
        else:
            st.error("Invalid email or password.")

# -------------------- Vehicle and Range --------------------
def register_vehicle():
    st.subheader("Register Your Vehicle")
    vehicle_type = st.selectbox("Vehicle Type", ["Car", "Van", "Bike"])
    vehicle_cc = st.text_input("Engine CC")
    battery_capacity = st.number_input("Battery Capacity (in kWh)", min_value=1.0)
    registration_number = st.text_input("Vehicle Registration Number")
    
    if st.button("Save Vehicle Details"):
        cursor.execute("INSERT INTO vehicles (user_id, vehicle_type, vehicle_cc, battery_capacity, registration_number) VALUES (?, ?, ?, ?, ?)",
                       (st.session_state.user_id, vehicle_type, vehicle_cc, battery_capacity, registration_number))
        conn.commit()
        st.success("Vehicle details saved successfully.")

def range_estimator():
    st.subheader("Range Estimator")
    cursor.execute("SELECT battery_capacity FROM vehicles WHERE user_id=?", (st.session_state.user_id,))
    result = cursor.fetchone()
    if not result:
        st.warning("Please register your vehicle first.")
        return

    battery_capacity = result[0]
    consumption_rate = 0.15  # kWh/km for standard car; could be adjusted by vehicle type
    estimated_range = battery_capacity / consumption_rate

    st.info(f"Your estimated range is **{estimated_range:.0f} km** based on a consumption rate of {consumption_rate} kWh/km.")

    geolocator = Nominatim(user_agent="twende_ev")

    from_location = st.text_input("Start Location (e.g., Nairobi, Kenya)")
    to_location = st.text_input("Destination (e.g., Nakuru, Kenya)")

    if st.button("Calculate Distance"):
        try:
            from_coords = geolocator.geocode(from_location)
            to_coords = geolocator.geocode(to_location)

            if not from_coords or not to_coords:
                st.error("Could not geocode one of the locations. Please try again.")
                return

            from_point = (from_coords.latitude, from_coords.longitude)
            to_point = (to_coords.latitude, to_coords.longitude)
            distance_km = geodesic(from_point, to_point).km

            st.success(f"The distance between **{from_location}** and **{to_location}** is approximately **{distance_km:.2f} km**.")

            if distance_km > estimated_range:
                st.warning("⚠️ Your battery may not be sufficient for this trip. Please plan to charge.")
            else:
                st.success("✅ You have enough battery range for this journey.")

            # Show route on map
            route_map = folium.Map(location=from_point, zoom_start=7)
            folium.Marker(from_point, tooltip="Start: " + from_location).add_to(route_map)
            folium.Marker(to_point, tooltip="Destination: " + to_location).add_to(route_map)
            folium.PolyLine([from_point, to_point], color="blue", weight=2.5).add_to(route_map)
            st_folium(route_map, width=700, height=500)

        except Exception as e:
            st.error(f"Error: {e}")

# -------------------- Main --------------------
def main():
    st.set_page_config(page_title="Twende EV Dashboard", layout="centered")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Login":
            login()
        elif choice == "Register":
            register()
    else:
        st.sidebar.success(f"Logged in as {st.session_state.email}")
        options = ["Register Vehicle", "Range Estimator", "Logout"]
        choice = st.sidebar.selectbox("Select Option", options)

        if choice == "Register Vehicle":
            register_vehicle()
        elif choice == "Range Estimator":
            range_estimator()
        elif choice == "Logout":
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.success("You have been logged out.")

if __name__ == '__main__':
    main()





