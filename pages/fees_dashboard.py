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
def fetch_all_rows(table, order_col="receipt_no"):
    # Supabase returns at most 1000 rows per request, so page through the table/view
    rows, start, page_size = [], 0, 1000
    while True:
        batch = (
            supabase.table(table)
            .select("*")
            .order(order_col)
            .range(start, start + page_size - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return rows

data = fetch_all_rows("all_table_view")  # List of dictionaries

if not data:
    st.info("No data found in the table/view.")
    st.stop()

# ======================
# FEES KPI DASHBOARD (selected year)
# ======================
st.subheader("💰 Fees KPI Dashboard")

students_df = pd.DataFrame(fetch_all_rows("student_data", "s_no"))
students_df["year"] = students_df["year"].fillna("Not Set").astype(str)
students_df["program_name"] = students_df["program_name"].fillna("Not Set")

kpi_df = pd.DataFrame(data)
kpi_df["year"] = kpi_df["year"].fillna("Not Set").astype(str)
kpi_df["fee_type"] = kpi_df["fee_type"].fillna("").astype(str).str.upper()
kpi_df["program_name"] = kpi_df["program_name"].fillna("Not Set")
kpi_df["course_year"] = pd.to_numeric(kpi_df["fees_course_year"], errors="coerce")

kpi_years = sorted(set(students_df["year"]) | set(kpi_df["year"]))
kpi_year = st.selectbox(
    "Select Year for Fees KPIs", kpi_years, index=len(kpi_years) - 1, key="fees_kpi_year"
)
yr = kpi_df[kpi_df["year"] == kpi_year]
year_students = students_df[students_df["year"] == kpi_year]

def student_count(frame):
    return int(frame["student_id"].nunique())

st.metric("Total Students Registered", int(year_students["s_no"].nunique()))

st.markdown("### Fees paid by program and year (number of students)")

YEAR_LABELS = {1: "First Year", 2: "Second Year", 3: "Third Year"}

for prog in sorted(year_students["program_name"].unique()):
    registered = int(year_students.loc[year_students["program_name"] == prog, "s_no"].nunique())
    st.markdown(f"#### {prog}")
    st.caption(f"Registered in {kpi_year}: {registered}")

    prog_yr = yr[yr["program_name"] == prog]
    year_cols = st.columns(3)
    for i, n in enumerate([1, 2, 3]):
        year_rows = prog_yr[prog_yr["course_year"] == n]
        with year_cols[i]:
            st.markdown(f"**{YEAR_LABELS[n]}**")
            st.metric("Course Fees Paid", student_count(year_rows[year_rows["fee_type"] == "COURSE FEES"]))
            st.metric("Exam Fees Paid", student_count(year_rows[year_rows["fee_type"].str.contains("EXAM")]))

st.divider()

# ======================
# FEE STATUS BY PROGRAM (selected year)
# Paid = student has a payment for the fee type
# Not paid = enrolled in the year (student_data) with no payment for the fee type
# ======================
FEE_TYPES = [
    "APPLICATION FEES", "AREAR FEES", "ASSIGNMENT FEES", "BONAFIED CERTIFICATE FEES", "BOOK FEES",
    "CHANGE OF CENTRE FEES", "CONCESSION FEES", "CONSOLIDATE MARKSHEET FEES",
    "COURSE FEES", "COURSE FEES PENALTY", "COURSE COMPLETION CERT FEES", "DEGREE FEES",
    "ELIGIBILITY CERTIFICATE FEES", "EXAM CENTER FEES", "EXAM FEES",
    "EXAM FEES PENALTY", "EXAM WRITING FEES", "ID CARD FEES", "PENALTY",
    "PROVISIONAL FEES", "PRACTICAL FEES", "PSTM CERTIFICATE FEES",
    "REVALUATION FEES", "RE-DO ORDER FEEES", "TC FEES", "OTHER FEES",
]

st.subheader(f"🧾 Fee Status by Program — {kpi_year}")

fee_type_choice = st.selectbox("Select Fee Type", FEE_TYPES, key="fee_status_type")

def paid_ids_for(fee_type):
    return set(yr.loc[yr["fee_type"] == fee_type, "student_id"])

def split_students(fee_type, program):
    prog_students = year_students[year_students["program_name"] == program]
    paid_mask = prog_students["s_no"].isin(paid_ids_for(fee_type))
    return prog_students[paid_mask], prog_students[~paid_mask]

header = st.columns([3, 2, 2])
header[0].markdown("**Program**")
header[1].markdown("**Paid** (click number)")
header[2].markdown("**Not paid** (click number)")

for prog in sorted(year_students["program_name"].unique()):
    paid_list, not_list = split_students(fee_type_choice, prog)
    row = st.columns([3, 2, 2])
    row[0].write(prog)
    if row[1].button(str(len(paid_list)), key=f"paid_{fee_type_choice}_{prog}"):
        st.session_state.fee_list_sel = ("Paid", fee_type_choice, prog)
    if row[2].button(str(len(not_list)), key=f"notpaid_{fee_type_choice}_{prog}"):
        st.session_state.fee_list_sel = ("Not paid", fee_type_choice, prog)

sel = st.session_state.get("fee_list_sel")
if sel:
    status, sel_fee, sel_prog = sel
    paid_list, not_list = split_students(sel_fee, sel_prog)
    shown = paid_list if status == "Paid" else not_list
    st.markdown(f"**{status} — {sel_fee} — {sel_prog}** ({len(shown)} students)")
    st.dataframe(
        shown[["name", "mobile", "program_name", "course_name"]].rename(columns={
            "name": "Name", "mobile": "Mobile", "program_name": "Program", "course_name": "Course",
        }),
        hide_index=True,
    )

st.divider()

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
    st.dataframe(df[columns_to_show], width="stretch")
    
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
                st.header(f"Details of students paid: {selected_fees_type}")
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
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No student_id column found — cannot calculate course-wise counts.")

except Exception as e:
    st.error(f"An error occurred while displaying the dashboard: {e}")