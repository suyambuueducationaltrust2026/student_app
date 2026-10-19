import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root when running locally (no-op if missing)

def get_setting(name):
    # Streamlit Cloud provides secrets; locally they come from .env
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name)

SUPABASE_URL = get_setting("SUPABASE_URL")
SUPABASE_KEY = get_setting("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase settings missing. Add SUPABASE_URL and SUPABASE_KEY to .env (local) or Streamlit secrets (cloud).")
    st.stop()

# --- Create Supabase client ---
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


