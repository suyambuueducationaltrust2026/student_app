import streamlit as st
import pandas as pd
import time
import plotly.express as px
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

#chart


df = df1.copy()
df.columns = df.columns.str.strip().str.lower()

st.title("Student Admission Details")

# -------------------------
# Year and Program Filters
# -------------------------
col1, col2 = st.columns(2)

with col1:
    years = sorted(df["year"].dropna().unique())
    selected_years = st.multiselect("Select Years", years, default=years)

with col2:
    programs = sorted(df["program_name"].dropna().unique())
    selected_program = st.selectbox("Select Program", programs,index=programs.index("UG"))

# -------------------------
# Filter Data
# -------------------------
filtered_df = df[
    (df["year"].isin(selected_years)) &
    (df["program_name"] == selected_program)
]

# =========================
# Chart 1: Students per Program
# =========================
program_students = (
    filtered_df.groupby("course_name")["s_no"]
    .nunique()
    .reset_index(name="No_of_Students")
)
total_students = program_students["No_of_Students"].sum()

# Display the total
st.write(f"**Total Students in this selected program:** {total_students}")
st.subheader(f"Student Count by Course")
st.dataframe(program_students)

fig1 = px.bar(
    program_students,
    x="course_name",
    y="No_of_Students",
    color="course_name",
    text="No_of_Students",
    title="Students per course"
)

st.plotly_chart(fig1, use_container_width=True)


#FEES DASHBOARD

if profile["role_code"] in [1,2]:

    st.title("ALL RECEIPT TABLE VIEW")

    response2 = supabase.table("full_fee_payment_view").select("*").execute()

# Convert to DataFrame
    df2 = pd.DataFrame(response2.data)

# Display in Streamlit
    st.dataframe(df2)    



  
