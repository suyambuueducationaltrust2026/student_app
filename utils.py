import os
import streamlit as st
from supabase import create_client, Client

# --- Detect if running on Streamlit Cloud ---
ON_STREAMLIT = st.runtime.exists()

if ON_STREAMLIT:
    # Use Streamlit secrets on the cloud
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
else:
    # Use .env locally
    from dotenv import load_dotenv

    load_dotenv()  # reads .env in project root
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ------------------------------
# Helper: Get profile by user ID
# ------------------------------
def get_profile(user_id):
    """
    Fetch the profile of a logged-in user from the 'profiles' table using their auth user ID.
    Returns a dictionary with profile data or None if not found.
    """
    try:
        res = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return None

def get_courses(program_id):
          
          return supabase.table("course_master")\
                .select("id, name, code")\
                .eq("type", "course")\
                .eq("parent_id", program_id)\
                .order("name")\
                .execute().data

def get_programs():
    return supabase.table("course_master")\
        .select("id, name, code")\
        .eq("type", "program")\
        .order("name")\
        .execute().data


def get_universities():
    return supabase.table("univ_courses")\
        .select("id, name, code")\
        .eq("type", "university")\
        .order("name")\
        .execute().data


