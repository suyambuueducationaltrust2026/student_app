import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
from utils import supabase, get_universities, get_programs, get_courses

# ----------------------
if "profile" not in st.session_state:
    st.error("⚠️ Session expired. Please login again.")
    st.stop()

profile = st.session_state.profile

# ----------------------
# ROLE CHECK
# ----------------------
if profile["role_code"] in [1,2,3]:

    st.title("👤 Student Dashboard")

    response1 = supabase.table("student_data").select("*").limit(10).execute()

# Convert to DataFrame
    df1 = pd.DataFrame(response1.data)

# Display in Streamlit
    st.dataframe(df1)    