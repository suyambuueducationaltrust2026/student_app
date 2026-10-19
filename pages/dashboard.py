import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
import streamlit.components.v1 as components
from receipt_pdf import generate_receipt_pdf
from utils import supabase

# ----------------------
# SESSION CHECK
# ----------------------
if "profile" not in st.session_state or st.session_state.profile is None:
    st.error("⚠️ Session expired. Please login again.")
    st.stop()

profile = st.session_state.profile

# ----------------------
# ROLE CHECK
# ----------------------
if profile["role_code"] not in [1, 2, 3]:
    st.warning("Unauthorized access")
    st.stop()

st.title("👤 Student Dashboard")

# ----------------------
# LOAD ALL STUDENTS
# Supabase returns at most 1000 rows per request, so page through the table.
# ----------------------
def fetch_all_students():
    rows, start, page_size = [], 0, 1000
    while True:
        batch = (
            supabase.table("student_data")
            .select("*")
            .order("s_no")
            .range(start, start + page_size - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return rows

df = pd.DataFrame(fetch_all_students())

if df.empty:
    st.info("No student records found.")
    st.stop()

# -------------------------
# KPI dashboard for a selected year
# -------------------------
st.subheader("📊 Year KPI Dashboard")

year_text = df["year"].fillna("Not Set").astype(str)
kpi_years = sorted(year_text.unique())
kpi_year = st.selectbox("Select Year for KPIs", kpi_years, index=len(kpi_years) - 1)

ky = df[year_text == kpi_year]

def upper_text(col):
    return ky[col].fillna("").astype(str).str.strip().str.upper()

total_students = ky["s_no"].nunique()
male = int((upper_text("gender") == "MALE").sum())
female = int((upper_text("gender") == "FEMALE").sum())
rural = int((upper_text("location_type") == "RURAL").sum())
urban = int((upper_text("location_type") == "URBAN").sum())
programs_count = ky["program_name"].nunique()
courses_count = ky["course_name"].nunique()
universities_count = ky["university_name"].nunique()
centres_count = ky.loc[ky["reference_centre"] != "Not Assigned", "reference_centre"].nunique()
disabled = int((upper_text("differently_abled") == "YES").sum())
pending = int((upper_text("app_status") == "PENDING").sum())

kpi_row1 = st.columns(5)
kpi_row1[0].metric("Total Students", int(total_students))
kpi_row1[1].metric("Male", male)
kpi_row1[2].metric("Female", female)
kpi_row1[3].metric("Rural", rural)
kpi_row1[4].metric("Urban", urban)

kpi_row2 = st.columns(6)
kpi_row2[0].metric("Programs", int(programs_count))
kpi_row2[1].metric("Courses", int(courses_count))
kpi_row2[2].metric("Universities", int(universities_count))
kpi_row2[3].metric("Centres", int(centres_count))
kpi_row2[4].metric("Differently Abled", disabled)
kpi_row2[5].metric("Pending Applications", pending)

st.divider()

# Full student table (supabase.table("student_data").select("*"))
st.dataframe(df)

# Excel download of the full table
excel_buffer = BytesIO()
df.to_excel(excel_buffer, index=False, sheet_name="student_data")
st.download_button(
    "⬇ Download Excel",
    data=excel_buffer.getvalue(),
    file_name="student_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

df.columns = df.columns.str.strip().str.lower()
df["reference_centre"] = df["reference_centre"].fillna("Not Assigned")

# -------------------------
# Download selected students
# -------------------------
st.subheader("⬇ Download Selected Students")

def as_text(col):
    return df[col].fillna("Not Set").astype(str)

download_filters = [
    ("year", "Year"),
    ("university_name", "University"),
    ("program_name", "Program"),
    ("pattern", "Pattern"),
]

dl_cols = st.columns(4)
dl_selected = {}
for i, (col, label) in enumerate(download_filters):
    options = sorted(as_text(col).unique())
    with dl_cols[i]:
        dl_selected[col] = st.multiselect(
            label, options, default=[], placeholder="All", key=f"dl_{col}"
        )

# Empty dropdown = no filter on that field
dl_mask = pd.Series(True, index=df.index)
for col, chosen in dl_selected.items():
    if chosen:
        dl_mask &= as_text(col).isin(chosen)
dl_df = df[dl_mask]

st.write(f"**Students selected for download:** {len(dl_df)}")

dl_buffer = BytesIO()
dl_df.to_excel(dl_buffer, index=False, sheet_name="student_data")
st.download_button(
    "⬇ Download Selected Excel",
    data=dl_buffer.getvalue(),
    file_name="selected_students.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    disabled=dl_df.empty,
)

st.title("Student Admission Details")

# -------------------------
# Year and Program Filters
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    years = sorted(df["year"].dropna().unique())
    selected_years = st.multiselect("Select Years", years, default=[], placeholder="All")

with col2:
    programs = sorted(df["program_name"].dropna().unique())
    if not programs:
        st.info("No programs found.")
        st.stop()
    default_program = programs.index("UG") if "UG" in programs else 0
    selected_program = st.selectbox("Select Program", programs, index=default_program)

with col3:
    centre = sorted(df["reference_centre"].unique())
    selected_centre = st.multiselect("Selected Centres", centre, default=[], placeholder="All")

# -------------------------
# Filter Data (empty year/centre = no filter)
# -------------------------
chart_mask = df["program_name"] == selected_program
if selected_years:
    chart_mask &= df["year"].isin(selected_years)
if selected_centre:
    chart_mask &= df["reference_centre"].isin(selected_centre)
filtered_df = df[chart_mask]

# =========================
# Chart 1: Students per Course
# =========================
program_students = (
    filtered_df.groupby("course_name")["s_no"]
    .nunique()
    .reset_index(name="No_of_Students")
)
total_students = int(program_students["No_of_Students"].sum())

st.write(f"**Total Students in this selected program:** {total_students}")
st.subheader("Student Count by Course")
st.dataframe(program_students)

fig1 = px.bar(
    program_students,
    x="course_name",
    y="No_of_Students",
    color="course_name",
    text="No_of_Students",
    title="Students per course"
)

st.plotly_chart(fig1, width="stretch")


# =========================
# FEES DASHBOARD
# =========================
if profile["role_code"] in [1, 2]:

    st.title("ALL RECEIPT TABLE VIEW")

    def fetch_receipts():
        """Receipts joined to their fee lines and students (one row per receipt)."""
        rows, start, page_size = [], 0, 1000
        while True:
            batch = (
                supabase.table("payment_session")
                .select("""
                    id, receipt_no, receipt_date, payment_date, total_amount, payment_mode,
                    reference_number, manual_bill_no, is_late_payment, fine_amount,
                    yearfees_master(
                        course_year, batch_year, pattern, total_fee, paid_amount, balance, status, due_date,
                        student_data(s_no, name, mobile, registration_no, application_no,
                                     university_name, program_name, course_name, year, reference_centre)
                    ),
                    fees_payment(fee_type, amount)
                """)
                .order("id")
                .range(start, start + page_size - 1)
                .execute()
                .data
            )
            rows.extend(batch)
            if len(batch) < page_size:
                break
            start += page_size
        return rows

    def receipts_frame(rows):
        out = []
        for r in rows:
            yf = r.get("yearfees_master") or {}
            sd = yf.get("student_data") or {}
            fees = r.get("fees_payment") or []
            out.append({
                "receipt_no": r["receipt_no"],
                "payment_date": r["payment_date"],
                "name": sd.get("name"),
                "mobile": sd.get("mobile"),
                "registration_no": sd.get("registration_no"),
                "application_no": sd.get("application_no"),
                "university_name": sd.get("university_name"),
                "program_name": sd.get("program_name"),
                "course_name": sd.get("course_name"),
                "year": sd.get("year"),
                "pattern": yf.get("pattern"),
                "course_year": yf.get("course_year"),
                "fee_types": ", ".join(f["fee_type"] for f in fees),
                "total_paid": r["total_amount"],
                "payment_mode": r["payment_mode"],
                "reference_number": r["reference_number"],
                "manual_bill_no": r["manual_bill_no"],
            })
        return pd.DataFrame(out)

    df2 = receipts_frame(fetch_receipts())

    def load_receipt_pdf(receipt_no):
        """Rebuild the PDF for one receipt from the database."""
        res = supabase.table("payment_session").select("""
            id, receipt_no, payment_date, total_amount, payment_mode,
            manual_bill_no, reference_number, remarks,
            yearfees_master(
                course_year,
                student_data(name, mobile, university_name, admission_type, pattern,
                             program_name, course_name, year, registration_no, application_no)
            )
        """).eq("receipt_no", str(receipt_no)).limit(1).execute()

        if not res.data or not res.data[0].get("yearfees_master"):
            return None

        receipt = res.data[0]
        fees = (
            supabase.table("fees_payment")
            .select("*")
            .eq("payment_session_id", receipt["id"])
            .execute()
            .data
            or []
        )
        student = receipt["yearfees_master"]["student_data"]
        return generate_receipt_pdf(receipt, student, fees).getvalue()

    def print_button(pdf_bytes):
        """Button that opens the receipt in a new window and sends it to the printer."""
        b64 = base64.b64encode(pdf_bytes).decode()
        html = """
        <button id="print-receipt" style="padding:8px 16px;font-size:15px;cursor:pointer;
                border-radius:6px;border:1px solid #3730A3;background:#3730A3;color:white;
                width:100%;">🖨 Print receipt</button>
        <script>
        const pdfB64 = "__PDF__";
        document.getElementById("print-receipt").onclick = () => {
            const bin = atob(pdfB64);
            const bytes = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
            const url = URL.createObjectURL(new Blob([bytes], {type: "application/pdf"}));
            const w = window.open(url);
            if (w) { w.onload = () => setTimeout(() => w.print(), 500); }
        };
        </script>
        """.replace("__PDF__", b64)
        components.html(html, height=60)

    event = st.dataframe(
        df2,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        key="receipt_table",
    )
    st.caption("Click a row to view, print or download that receipt.")

    selected_rows = event.selection.rows
    if selected_rows:
        receipt_no = df2.iloc[selected_rows[0]]["receipt_no"]
        receipt_pdf_bytes = load_receipt_pdf(receipt_no)

        if receipt_pdf_bytes is None:
            st.error(f"Receipt {receipt_no} not found in the payment records.")
        else:
            st.subheader(f"🧾 Receipt {receipt_no}")
            b1, b2 = st.columns(2)
            with b1:
                print_button(receipt_pdf_bytes)
            with b2:
                st.download_button(
                    "⬇ Download PDF",
                    data=receipt_pdf_bytes,
                    file_name=f"Receipt_{receipt_no}.pdf",
                    mime="application/pdf",
                )
            st.pdf(receipt_pdf_bytes, height=700)
