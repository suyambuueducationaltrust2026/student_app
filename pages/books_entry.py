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

# Only admin/allowed roles
if profile["role_code"] not in [1, 2]:
    st.warning("Unauthorized access")
    st.stop()

# ======================
# PAGE TITLE
# ======================
st.header("📊 All Fees Dashboard")

# ======================
# FETCH DATA FROM VIEW
# ======================
response = supabase.table("all_table_view").select("*").execute()
data = response.data  # List of dictionaries

if not data:
    st.info("No data found in the table/view.")
    st.stop()

# ======================
# FILTER DROPDOWNS
# ======================
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    selected_univ = st.selectbox(
        "University",
        ["All"] + sorted({r["university_name"] for r in data})
    )

with col2:
    selected_pattern = st.selectbox(
        "Pattern",
        ["All"] + sorted({r["pattern"] for r in data})
    )

with col3:
    selected_program = st.selectbox(
        "Program",
        ["All"] + sorted({r["program_name"] for r in data})
    )

with col4:
    selected_course = st.selectbox(
        "Course",
        ["All"] + sorted({r["course_name"] for r in data})
    )

with col5:
    selected_year = st.selectbox(
        "Year",
        ["All"] + sorted({r["year"] for r in data})
    )
with col6:
    selected_fees_type = st.selectbox(
        "Type of Fees",
        ["All"] + sorted({r["fee_type"] for r in data})
    )

# ======================
# FILTER DATA BASED ON SELECTIONS
# ======================
filtered_students = [
    r for r in data
    if (selected_univ == "All" or r["university_name"] == selected_univ)
    and (selected_pattern == "All" or r["pattern"] == selected_pattern)
    and (selected_program == "All" or r["program_name"] == selected_program)
    and (selected_course == "All" or r["course_name"] == selected_course)
    and (selected_year == "All" or r["year"] == selected_year)
    and (selected_fees_type == "All" or r["fee_type"] == selected_fees_type)
]

# ======================
# DISPLAY DATA
# ======================
if filtered_students:
    df = pd.DataFrame(filtered_students)
    
    # Optional: Only show relevant columns
    columns_to_show = [
    # Student info
    "name", "mobile", "whatsapp", "admission_type",
    "registration_no", "reference_centre", "ref_centre_mobile",

    # Academic info
    "year", "university_name", "program_name", "course_name",

    # Fee structure
    "yf_id", "student_id", "batch_year", "fees_course_year",
    "due_date", "paid_amount",

    # Payment info
    "receipt_no", "fee_type", "amount"
    ]
    st.dataframe(df[columns_to_show], use_container_width=True)
    
    # ======================
    # DOWNLOAD BUTTON
    # ======================
    csv = df[columns_to_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇ Download CSV",
        data=csv,
        file_name="filtered_students.csv",
        mime="text/csv"
    )
else:
    st.info("No students found with the selected filters.")