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
    "name", "mobile", "admission_type","pattern",
    "registration_no", "reference_centre", "ref_centre_mobile",

    # Academic info
    "year", "university_name", "program_name", "course_name",

    # Fee structure
    "batch_year", "fees_course_year",
    "due_date", "paid_amount", "payment_date","payment_mode",

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

#dashboard

try:
    # Convert filtered students to DataFrame
    df = pd.DataFrame(filtered_students)
    
    if df.empty:
        st.info("No students found with the selected filters.")
    else:
        # Clean column names
        df.columns = df.columns.astype(str).str.strip().str.lower()
        st.title("📊 Course-wise Student Dashboard")
        
        # -------------------------
        # Year Filter (if column exists)
        # -------------------------
        if "fees_course_year" in df.columns:
            year_col = "fees_course_year"
            courseyears = sorted(df[year_col].dropna().unique())
            default_years = [courseyears[0]] if courseyears else []
            selected_years = st.multiselect("Select Years/Semester", courseyears, default=default_years)
            filtered_df = df[df[year_col].isin(selected_years)]
            
            if filtered_df.empty:
                st.info("No students found for the selected year(s).")
                filtered_df = None
        else:
            st.warning("⚠️ No year column found for the selected program.")
            filtered_df = df.copy()
        
        # -------------------------
        # Course-wise student count
        # -------------------------
        if filtered_df is not None:
            if "student_id" in filtered_df.columns:
                course_students = (
                    filtered_df.groupby("course_name")["student_id"]
                    .nunique()
                    .reset_index(name="No_of_Students")
                )
                total_students = course_students["No_of_Students"].sum()
                
                st.subheader(f"Students Count: {total_students}")
                st.dataframe(course_students)
                
                # Bar chart
                fig = px.bar(
                    course_students,
                    x="course_name",
                    y="No_of_Students",
                    color="course_name",
                    text="No_of_Students",
                    title="Students per Course"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No student_id column found — cannot calculate course-wise counts.")

except Exception as e:
    st.error(f"An error occurred while displaying the dashboard: {e}")