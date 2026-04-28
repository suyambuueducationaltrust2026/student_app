import streamlit as st
from datetime import date, datetime
from utils import supabase

# ======================
# SESSION INIT
# ======================
if "profile" not in st.session_state or st.session_state.profile is None:
    st.warning("Please log in first.")
    st.stop()

profile = st.session_state.profile

if "role_code" not in profile or profile["role_code"] != 2:
    st.warning("Unauthorized access")
    st.stop()
    
# Page state
if "page" not in st.session_state:
    st.session_state.page = "search"

if "selected_student" not in st.session_state:
    st.session_state.selected_student = None

# Reset toggle (for clearing form)
if "reset_flag" not in st.session_state:
    st.session_state.reset_flag = False

# ======================
# 🔍 SEARCH PAGE
# ======================
if st.session_state.page == "search":

    st.title("🔍 Student Search")

    search = st.text_input("Search by Name / Mobile / Aadhaar")

    students = []

    if search:
        res = supabase.table("student_data") \
            .select("*") \
            .or_(f"name.ilike.%{search}%,mobile.ilike.%{search}%,aadhaar.ilike.%{search}%") \
            .execute()

        students = res.data

    if not students:
        st.info("Search student first")
        st.stop()

    student_map = {
        f"{s['name']} | {s['mobile']} | {s['course_name']} | {s['year']}": s
        for s in students
    }

    selected = st.selectbox("Select Student", list(student_map.keys()))
    student = student_map[selected]

    if st.button("➡️ Proceed to Fees Entry"):
        st.session_state.selected_student = student
        st.session_state.page = "payment"
        st.rerun()

# ======================
# 💰 PAYMENT PAGE
# ======================
elif st.session_state.page == "payment":

    student = st.session_state.selected_student

    if not student:
        st.warning("Select student first")
        st.session_state.page = "search"
        st.rerun()

    st.title("💰 Fees Entry")

    st.success(f"{student['name']} | {student['course_name']}")

    # ======================
    # YEAR FEES MASTER
    # ======================
    batch_year = student["year"]
    pattern = student["pattern"]
    course_duration = student["course_duration"]

    course_year = st.selectbox(
        "Fees Year / Semester",
        list(range(1, course_duration + 1)),
        key=f"course_year_{st.session_state.reset_flag}"
    )

    due_date = st.date_input(
        "Due Date",
        value=date.today(),
        key=f"due_{st.session_state.reset_flag}"
    )

    res = supabase.table("yearfees_master") \
        .select("*") \
        .eq("student_id", student["s_no"]) \
        .eq("course_year", course_year) \
        .execute()

    yearfees = res.data[0] if res.data else None

    if not yearfees:
        insert = supabase.table("yearfees_master").insert({
            "student_id": student["s_no"],
            "pattern": pattern,
            "batch_year": batch_year,
            "course_year": course_year,
            "total_fee": 0,
            "paid_amount": 0,
            "balance": 0,
            "status": "Partially Paid",
            "due_date": str(due_date)
        }).execute()

        yearfees = insert.data[0]

    # ======================
    # FEE SELECTION
    # ======================
    st.subheader("💰 Select Fees")

    fee_types = [
        "APPLICATION FEES", "AREAR FEES", "ASSIGNMENT FEES", "BOOK FEES",
        "CHANGE OF CENTRE FEES", "CONCESSION FEES", "CONSOLIDATE MARKSHEET FEES",
        "COURSE FEES", "COURSE FEES PENALTY", "DEGREE FEES",
        "ELIGIBILITY CERTIFICATE FEES", "EXAM CENTER FEES", "EXAM FEES",
        "EXAM FEES PENALTY", "EXAM WRITING FEES", "PENALTY",
        "PROVISIONAL FEES", "PSTM CERTIFICATE FEES",
        "REVALUATION FEES", "TC FEES", "OTHER FEES"
    ]

    st.markdown("### 🔼 Fee Selection")

    selected_flags = {}
    cols = st.columns(4)

    for i, fee in enumerate(fee_types):
        selected_flags[fee] = cols[i % 4].checkbox(
            fee,
            key=f"{fee}_{st.session_state.reset_flag}"
        )

    st.divider()

    st.markdown("### 🔽 Enter Fee Amounts")

    selected_fees = {}

    for fee, is_selected in selected_flags.items():
        if is_selected:
            amount = st.number_input(
                f"{fee} Amount",
                min_value=0,
                step=100,
                key=f"{fee}_amt_{st.session_state.reset_flag}"
            )

            if amount > 0:
                selected_fees[fee] = amount

    total_selected_amount = sum(selected_fees.values())
    st.markdown("### 💵 Total Amount")
    st.success(f"₹ {total_selected_amount}")

    # ======================
    # PAYMENT DETAILS
    # ======================
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        payment_date = st.date_input(
            "Payment Date",
            value=date.today(),
            key=f"pay_{st.session_state.reset_flag}"
        )

    with col2:
        receipt_date = st.date_input(
            "Receipt Date",
            value=date.today(),
            key=f"rec_{st.session_state.reset_flag}"
        )

    with col3:
        manual_bill_no = st.text_input(
            "Manual Bill No",
            key=f"bill_{st.session_state.reset_flag}"
        )

    with col4:
        payment_mode = st.selectbox(
            "Payment Mode",
            ["Cash", "UPI", "NetBanking"],
            key=f"mode_{st.session_state.reset_flag}"
        )

    # ======================
    # LATE PAYMENT
    # ======================
    st.subheader("⚠️ Late Payment")

    is_late = st.radio(
        "Is this a late payment?",
        ["No", "Yes"],
        key=f"late_{st.session_state.reset_flag}"
    )

    fine_amount = 0

    if is_late == "Yes":
        fine_amount = st.number_input(
            "Fine Amount",
            min_value=0,
            step=50,
            key=f"fine_{st.session_state.reset_flag}"
        )

    remarks = st.text_area(
        "Remarks",
        key=f"remarks_{st.session_state.reset_flag}"
    )

    # ======================
    # SAVE PAYMENT
    # ======================
    if st.button("💾 Save Payment"):

        if not selected_fees:
            st.warning("Select at least one fee")
            st.stop()

        total_amount = sum(selected_fees.values())
        final_total = total_amount + fine_amount

        session = supabase.table("payment_session").insert({
            "yearfees_master_id": yearfees["id"],
            "manual_bill_no": manual_bill_no,
            "receipt_date": str(receipt_date),
            "payment_date": str(payment_date),
            "is_late_payment": is_late == "Yes",
            "fine_amount": fine_amount,
            "remarks": remarks,
            "total_amount": final_total,
            "payment_mode": payment_mode
        }).execute()

        session_id = session.data[0]["id"]
        receipt_no = session.data[0]["receipt_no"]

        for fee, amt in selected_fees.items():
            supabase.table("fees_payment").insert({
                "payment_session_id": session_id,
                "yearfees_master_id": yearfees["id"],
                "fee_type": fee,
                "amount": amt
            }).execute()

        updated_paid = (yearfees["paid_amount"] or 0) + final_total
        balance = (yearfees["total_fee"] or 0) - updated_paid
        status = "Fully Paid" if balance <= 0 else "Partially Paid"

        supabase.table("yearfees_master").update({
            "paid_amount": updated_paid,
            "balance": balance,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("id", yearfees["id"]).execute()

        st.success(f"Payment Saved! Receipt No: {receipt_no}")

    # ======================
    # NAVIGATION BUTTONS
    # ======================
    st.divider()

    colA, colB = st.columns(2)

    with colA:
        if st.button("🔄 Reset Payment"):
            st.session_state.reset_flag = not st.session_state.reset_flag
            st.rerun()

    with colB:
        if st.button("⬅ ENTER NEW STUDENT "):
            st.session_state.page = "search"
            st.session_state.selected_student = None
            st.rerun()