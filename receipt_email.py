import smtplib
from email.message import EmailMessage

import streamlit as st

from receipt_pdf import generate_receipt_pdf
from utils import get_setting

# Every saved receipt is sent to this school address
SCHOOL_EMAIL = "suyambuueducationaltrust2026@gmail.com"


def is_valid_email(address):
    return bool(address) and "@" in address and "." in address.split("@")[-1]


def send_pdf_email(to_address, pdf_bytes, receipt_no, greeting, student_name):
    smtp_user = get_setting("SMTP_USER")
    smtp_password = get_setting("SMTP_APP_PASSWORD")
    smtp_host = get_setting("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(get_setting("SMTP_PORT") or 587)

    if not smtp_user or not smtp_password:
        raise RuntimeError(
            "Email settings missing. Add SMTP_USER and SMTP_APP_PASSWORD "
            "to .env (local) or Streamlit secrets (cloud)."
        )

    msg = EmailMessage()
    msg["Subject"] = f"Fee Receipt {receipt_no} - {student_name}"
    msg["From"] = f"Suyambuu Educational Trust <{smtp_user}>"
    msg["To"] = to_address
    msg.set_content(
        f"{greeting},\n\n"
        f"Please find attached the fee receipt No. {receipt_no}.\n\n"
        "Suyambuu Educational Trust"
    )
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"Receipt_{receipt_no}.pdf",
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


@st.dialog("📧 Send receipt by email", dismissible=False)
def send_receipt_dialog(payload):
    receipt = payload["receipt"]
    student = payload["student"]
    receipt_no = receipt["receipt_no"]

    st.write(f"Receipt **{receipt_no}** saved for **{student['name']}**.")

    # School copy is always sent (not optional, cannot be removed)
    st.info(f"📨 Receipt copy to school (always sent): **{SCHOOL_EMAIL}**")

    student_email = st.text_input(
        "Student email (optional)",
        value=student.get("email") or "",
        key=f"student_mail_{receipt_no}",
    ).strip()

    if st.button("📧 Send receipt", key=f"send_{receipt_no}", type="primary"):
        recipients = [(SCHOOL_EMAIL, "Dear Sir/Madam")]

        if student_email:
            if not is_valid_email(student_email):
                st.error("The student email is not valid. Correct it, or clear it to skip.")
                return
            if student_email.lower() != SCHOOL_EMAIL:
                recipients.append((student_email, f"Dear {student['name']}"))

        pdf_bytes = generate_receipt_pdf(receipt, student, payload["fees"]).getvalue()

        all_sent = True
        with st.spinner("Sending receipt..."):
            for address, greeting in recipients:
                try:
                    send_pdf_email(address, pdf_bytes, receipt_no, greeting, student["name"])
                    st.success(f"Receipt {receipt_no} sent to {address}")
                except Exception as e:
                    all_sent = False
                    st.error(f"Could not send to {address}: {e}")

        st.session_state[f"receipt_sent_{receipt_no}"] = all_sent

    # Close only after the school copy has been sent
    if st.session_state.get(f"receipt_sent_{receipt_no}"):
        if st.button("Close", key=f"close_{receipt_no}"):
            st.rerun()
