import streamlit as st
from utils import supabase, get_profile

# ------------------------------
# Auth functions
# ------------------------------
def sign_up(email, password):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Registration failed: {e}")

def sign_in(email, password):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Login failed: {e}")

def sign_out():
    try:
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.profile = None
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")

# ------------------------------
# Main app
# ------------------------------
def main_app():
    profile = st.session_state.profile
    st.title("🏠 Welcome to Suyambuu Learning Centre")
    st.sidebar.success(f"Logged in as: {profile['email']} ({profile['role']}) 👋")

    # Display user profile info
    st.header("📝 My Profile")
    st.write(f"**Name:** {profile.get('name', '')}")
    st.write(f"**Mobile:** {profile.get('mobile_number', '')}")
    st.write(f"**Role:** {profile.get('role', '')}")

    # Admin section: update other users
    if profile["role_code"] in [1, 2]:  # superadmin/admin
        st.subheader("👤 Admin: Update User Profiles")
        from profile import profile_update_form
        profile_update_form()

    if st.sidebar.button("Logout"):
        sign_out()

# ------------------------------
# Auth screen
# ------------------------------
def auth_screen():
    st.title("🔐 SUYAMBUU Learning Centre!")
    option = st.selectbox("Choose an action:", ["Login", "Sign Up"])
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Sign Up":
        if st.button("Register"):
            user = sign_up(email, password)
            if user and user.user:
                st.success("Registration successful. Please log in.")

    elif option == "Login":
        if st.button("Login"):
            user = sign_in(email, password)
            if user and user.user:
                st.session_state.user = user.user  # store auth user
            # Fetch profile from 'profiles' table
                profile = get_profile(user.user.id)
            if profile:
                st.session_state.profile = profile
                st.success(f"Welcome back, {profile['name']} ({profile['role']})!")
            else:
                st.error("Profile not found. Contact admin.")
            st.rerun()
# ------------------------------
# Initialize session state
# ------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None

# ------------------------------
# App flow control
# ------------------------------
if st.session_state.user and st.session_state.profile:
    main_app()
else:
    auth_screen()