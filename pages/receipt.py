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

query = supabase.table("payment_session").select("""
    id, receipt_no, payment_date, total_amount, payment_mode,
    manual_bill_no, reference_number, remarks,
    yearfees_master(
        course_year,
        student_data(name, mobile, university_name, admission_type, pattern, program_name, course_name, year, registration_no)
    )
""").order("id", desc=True)

# ======================
# DATABASE SEARCH (all receipts, not just the latest 50)
# ======================
term = search.strip().replace(",", " ").replace("(", " ").replace(")", " ")

if term:
    # 1. Students matching name / mobile / course
    student_res = supabase.table("student_data") \
        .select("s_no") \
        .or_(f"name.ilike.%{term}%,mobile.ilike.%{term}%,course_name.ilike.%{term}%") \
        .execute()
    student_ids = [s["s_no"] for s in student_res.data or []]

    # 2. Their fee records (yearfees_master)
    yearfees_ids = []
    if student_ids:
        yearfees_res = supabase.table("yearfees_master") \
            .select("id") \
            .in_("student_id", student_ids) \
            .execute()
        yearfees_ids = [y["id"] for y in yearfees_res.data or []]

    # 3. Receipts for those fee records, or a matching receipt number
    conditions = []
    if yearfees_ids:
        ids_text = ",".join(str(i) for i in yearfees_ids)
        conditions.append(f"yearfees_master_id.in.({ids_text})")
    if term.isdigit():
        conditions.append(f"receipt_no.eq.{term}")

    if not conditions:
        st.info("No receipts found")
        st.stop()

    query = query.or_(",".join(conditions)).limit(200)
else:
    query = query.limit(50)

res = query.execute()
data = res.data or []

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
**University Name:** {student['university_name']} 
**Admission type:** {student['admission_type']}  
**Pattern:** {student['pattern']}
**program Name:** {student['program_name']} 
**Course:** {student['course_name']}
**Course Year:** {receipt['yearfees_master']['course_year']}
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
**Reference No:** {receipt['reference_number']} 
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