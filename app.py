import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from utils.auth import login_user, logout_user, register_user, is_authenticated
from utils.mapbox import get_nearest_stations
from utils.analytics import get_battery_data, generate_battery_chart

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Tende EV Dashboard", layout="wide")

# ---- SESSION STATE SETUP ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = None


# ---- LOGIN PAGE ----
def login():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid email or password.")
    if st.button("Register"):
        st.session_state.register = True
        st.rerun()


# ---- REGISTER PAGE ----
def register():
    st.title("📝 Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        if register_user(email, password):
            st.success("Account created! Please log in.")
            st.session_state.register = False
            st.rerun()
        else:
            st.error("Email already registered.")
    if st.button("Back to Login"):
        st.session_state.register = False
        st.rerun()


# ---- LOGOUT ----
def logout():
    logout_user()
    st.session_state.logged_in = False
    st.session_state.email = None
    st.success("Logged out successfully.")
    st.rerun()


# ---- MAIN APP CONTENT ----
def main_app():
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Go to", ["🏠 Welcome", "🔋 Battery Analytics", "🔌 Find Charging Stations"])
    st.sidebar.button("Logout", on_click=logout)

    if menu == "🏠 Welcome":
        st.header(f"Welcome, {st.session_state.email} 👋")
        st.write("Use the sidebar to navigate the dashboard features.")

    elif menu == "🔋 Battery Analytics":
        st.header("🔋 Battery Performance Analytics")
        data = get_battery_data()
        fig = generate_battery_chart(data)
        st.pyplot(fig)

    elif menu == "🔌 Find Charging Stations":
        st.header("🔌 Nearby Charging Stations")
        location = st.text_input("Enter location (e.g., Langata, Nairobi):")
        if st.button("Search"):
            with st.spinner("Searching..."):
                results = get_nearest_stations(location)
                if results:
                    st.subheader("Top 3 Nearest Stations:")
                    for station in results:
                        st.markdown(f"**{station['name']}** - {station['address']}")
                else:
                    st.warning("No charging stations found for that location.")


# ---- ENTRY POINT ----
def main():
    if st.session_state.get("register", False):
        register()
    elif not st.session_state.logged_in:
        login()
    else:
        main_app()


if __name__ == "__main__":
    main()







