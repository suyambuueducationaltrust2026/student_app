import streamlit as st
from utils import supabase

def profile_update_form():
    # Fetch all users
    users_res = supabase.table("profiles").select("*").execute()
    users = users_res.data if users_res.data else []

    if not users:
        st.info("No users found in profiles table.")
        return

    # Select user
    user_emails = [u["email"] for u in users]
    selected_email = st.selectbox("Select user to edit", user_emails)

    selected_user = next((u for u in users if u["email"] == selected_email), None)

    if selected_user:
        with st.form("update_profile_form"):
            name = st.text_input("Full Name", value=selected_user.get("name", ""))
            mobile_number = st.text_input("Mobile Number", value=selected_user.get("mobile_number", ""))
            
            role_map = {
                "superadmin": 1,
                "admin": 2,
                "subadmin": 3
            }
            role = st.selectbox("Role", list(role_map.keys()), index=list(role_map.keys()).index(selected_user["role"]))
            role_code = role_map[role]

            submitted = st.form_submit_button("Update Profile")

            if submitted:
                # Update profile in Supabase
                supabase.table("profiles").update({
                    "name": name,
                    "mobile_number": mobile_number,
                    "role": role,
                    "role_code": role_code
                }).eq("email", selected_email).execute()

                st.success(f"Profile for {selected_email} updated successfully!")