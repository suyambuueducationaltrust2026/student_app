import streamlit as st
from utils import supabase
from receipt_pdf import generate_receipt_pdf

# ======================
# SESSION CHECK
# ======================
if "profile" not in st.session_state:
    st.error("Session expired")
    st.stop()

profile = st.session_state.profile

if profile["role_code"] != 2:
    st.stop()

st.title("🧾 Receipts")

# ======================
# FILTERS
# ======================
search = st.text_input("Search (Name / Mobile / Receipt No)")

query = supabase.table("payment_session") \
    .select("""
        id, receipt_no, payment_date, total_amount, payment_mode,
        manual_bill_no, remarks,
        yearfees_master(
            course_year,
            student_data(name, mobile, course_name, year)
        )
    """)
if search:
    search_pattern = f"%{search}%"

    query = (
        query.or_(f"receipt_no.ilike.{search_pattern}")
        .or_(f"yearfees_master.student_data.name.ilike.{search_pattern}")
        .or_(f"yearfees_master.student_data.mobile.ilike.{search_pattern}")
        .or_(f"yearfees_master.student_data.course_name.ilike.{search_pattern}")
    )


res = query.order("id", desc=True).limit(50).execute()
data = res.data

if not data:
    st.info("No receipts found")
    st.stop()

# ======================
# RECEIPT LIST
# ======================
st.subheader("📋 Receipt List")

receipt_map = {}

for r in data:
    student = r["yearfees_master"]["student_data"]

    label = f"Receipt #{r['receipt_no']} | {student['name']} | ₹{r['total_amount']} | {r['payment_date']}"
    receipt_map[label] = r

selected_label = st.selectbox("Select Receipt", list(receipt_map.keys()))
receipt = receipt_map[selected_label]

# ======================
# FETCH FEE BREAKDOWN
# ======================
fees_res = supabase.table("fees_payment") \
    .select("*") \
    .eq("payment_session_id", receipt["id"]) \
    .execute()

fees = fees_res.data

student = receipt["yearfees_master"]["student_data"]

# ======================
# RECEIPT PREVIEW
# ======================
st.subheader("🧾 Receipt Preview")
st.markdown(f"""
### 🎓 Student Details
**Name:** {student['name']}  
**Registration Number:** {student['registration_no']}
**University Name:** {student['univ_name']}  
**Pattern:** {student['pattern_name']}
**program Name:** {student['program_name']} 
**Course:** {student['course_name']}
**Batch:** {student['year']}  
**Mobile:** {student['mobile']}  

---

### 💰 Fee Breakdown
""")

for f in fees:
    st.write(f"{f['fee_type']} : ₹ {f['amount']}")

st.markdown(f"""
---
### 💵 Payment Summary

**Total Paid:** ₹ {receipt['total_amount']}  

---

### 📄 Payment Info

**Receipt No:** {receipt['receipt_no']}  
**Payment Date:** {receipt['payment_date']}  
**Mode:** {receipt['payment_mode']}  
**Manual Bill No:** {receipt['manual_bill_no']}  

**Remarks:** {receipt['remarks']}
""")

# ======================
# PRINT BUTTON
# ======================
st.divider()

pdf = generate_receipt_pdf(receipt, student, fees)

st.download_button(
    "📄 Download PDF Receipt",
    data=pdf,
    file_name=f"Receipt_{receipt['receipt_no']}.pdf",
    mime="application/pdf"
)