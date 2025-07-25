import streamlit as st
import json
import os
import matplotlib.pyplot as plt

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

def register():
    st.subheader("Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        if email in st.session_state.users:
            st.error("Email already registered. Please log in.")
        elif not email or not password:
            st.error("Please enter both email and password.")
        else:
            st.session_state.users[email] = password
            save_users(st.session_state.users)
            st.success("Registration successful! You can now log in.")
            st.experimental_rerun()

def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if st.session_state.users.get(email) == password:
            st.session_state.authenticated = True
            st.session_state.current_user = email
            st.success(f"Welcome back, {email}!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = ""
    st.experimental_rerun()

def show_battery_chart():
    labels = ['Used %', 'Remaining %']
    charge = st.slider("Battery %", 0, 100, 75)
    data = [100 - charge, charge]

    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%')
    st.pyplot(fig)

def show_dashboard():
    st.title("Twende EV")
    st.markdown("""
    ### Powering the Future of Mobility – One Charge at a Time

    Empower your electric driving experience with real-time insights, intelligent analytics, and seamless control.

    - **Smart Charging**: No more guesswork—get precise, data-driven charging recommendations.
    - **Journey Confidence**: Plan routes with real-time battery and station insights.
    - **Proactive Maintenance**: Stay ahead with alerts and diagnostics tailored to your EV.

    #### Drive Smarter. Charge Smarter.
    """)

    st.markdown("#### Battery Analytics")
    show_battery_chart()

    if st.button("Logout"):
        logout()

def main():
    st.set_page_config(page_title="Twende EV", layout="centered")
    st.sidebar.title("Twende EV")

    if st.session_state.authenticated:
        show_dashboard()
    else:
        action = st.sidebar.radio("Choose action:", ["Login", "Register"])
        if action == "Login":
            login()
        else:
            register()

if __name__ == "__main__":
    main()




