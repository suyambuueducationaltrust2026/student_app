import streamlit as st
from datetime import date
from utils import supabase

# ======================
# SESSION CHECK
# ======================
if "profile" not in st.session_state or st.session_state.profile is None:
    st.warning("Please log in first.")
    st.stop()

profile = st.session_state.profile

if profile["role_code"] not in [2, 3]:
    st.warning("Unauthorized access")
    st.stop()

st.title("✏️ Edit Student Details")

# ======================
# SEARCH
# ======================
SEARCH_FIELDS = [
    "name", "mobile", "course_name", "program_name",
    "university_name", "year", "registration_no",
]

search = st.text_input(
    "Search by Name / Mobile / Course / Program / University / Year / Registration No"
)

# Commas and brackets would break the search filter, so strip them
search_clean = search.strip().replace(",", " ").replace("(", " ").replace(")", " ")

if not search_clean:
    st.info("Type a search term to find a student.")
    st.stop()

res = (
    supabase.table("student_data")
    .select("*")
    .or_(",".join(f"{field}.ilike.%{search_clean}%" for field in SEARCH_FIELDS))
    .limit(100)
    .execute()
)
students = res.data or []

if not students:
    st.info("No students found.")
    st.stop()

if len(students) == 100:
    st.caption("Showing the first 100 matches. Type more of the name or details to narrow down.")

# ======================
# SELECT STUDENT
# ======================
student_map = {
    f"[{s['s_no']}] {s['name']} | {s['mobile']} | {s['course_name']} | "
    f"{s['program_name']} | {s['university_name']} | {s['year']} | {s['registration_no']}": s
    for s in students
}

selected_label = st.selectbox("Select Student", list(student_map.keys()))
student = student_map[selected_label]
sid = student["s_no"]


# ======================
# HELPERS
# ======================
def text_value(field):
    v = student.get(field)
    return "" if v is None else str(v)


def select_box(label, base_options, field, key):
    # Keep the saved value even if it isn't in the usual list
    current = student.get(field)
    options = list(base_options)
    if current not in options and current is not None:
        options.append(current)
    index = options.index(current) if current in options else 0
    return st.selectbox(label, options, index=index, key=key)


def date_value(field, default):
    try:
        return date.fromisoformat(str(student.get(field))[:10])
    except (TypeError, ValueError):
        return default


# ======================
# EDIT FORM
# ======================
st.markdown("### 🎓 Academic details (read-only)")
st.caption("These are linked to fee records, so they are not edited here.")

ro1, ro2, ro3 = st.columns(3)
ro1.text_input("Admission Type", text_value("admission_type"), disabled=True, key=f"ro_adm_{sid}")
ro1.text_input("Pattern", text_value("pattern"), disabled=True, key=f"ro_pat_{sid}")
ro2.text_input("University", text_value("university_name"), disabled=True, key=f"ro_univ_{sid}")
ro2.text_input("Program", text_value("program_name"), disabled=True, key=f"ro_prog_{sid}")
ro3.text_input("Course", text_value("course_name"), disabled=True, key=f"ro_course_{sid}")
ro3.text_input("Year", text_value("year"), disabled=True, key=f"ro_year_{sid}")

with st.form(f"edit_student_form_{sid}"):

    st.markdown("### 👤 Personal details")
    c1, c2 = st.columns(2)

    with c1:
        name = st.text_input("Student Name", text_value("name"), key=f"name_{sid}")
        parent_name = st.text_input("Parent/Guardian Name", text_value("parent_guardian_name"), key=f"parent_{sid}")
        aadhaar = st.text_input("Aadhaar Number", text_value("aadhaar"), max_chars=12, key=f"aadhaar_{sid}")
        mobile = st.text_input("Mobile Number", text_value("mobile"), max_chars=10, key=f"mobile_{sid}")
        whatsapp = st.text_input("WhatsApp No", text_value("whatsapp"), max_chars=10, key=f"whatsapp_{sid}")
        email = st.text_input("Email ID", text_value("email"), key=f"email_{sid}")
        location_type = select_box("Location Type", ["Rural", "Urban"], "location_type", f"loc_{sid}")
        address = st.text_area("Address", text_value("address"), key=f"address_{sid}")
        abc_id = st.text_input("ABC ID", text_value("abc_id"), key=f"abc_{sid}")
        mother_tongue = st.text_input("Mother Tongue", text_value("mother_tongue"), key=f"tongue_{sid}")

    with c2:
        gender = select_box("Gender", ["Male", "Female", "Other"], "gender", f"gender_{sid}")
        dob = st.date_input(
            "Date of Birth",
            value=date_value("date_of_birth", date(2000, 1, 1)),
            min_value=date(1950, 1, 1),
            max_value=date.today(),
            key=f"dob_{sid}",
        )
        religion = select_box("Religion", ["HINDU", "CHRISTIAN", "ISLAM", "Other"], "religion", f"religion_{sid}")
        community = select_box("Community", ["BC", "MBC", "SC", "ST", "FC", "Other"], "community", f"community_{sid}")
        caste = st.text_input("Caste", text_value("caste"), key=f"caste_{sid}")
        working_status = select_box(
            "Working Status", ["Not Working", "Govt Job", "Private Job"], "working_status", f"work_{sid}"
        )
        marital_status = select_box(
            "Marital Status", ["Not Married", "Married"], "marital_status", f"marital_{sid}"
        )
        deb_id = st.text_input("DEB ID", text_value("deb_id"), key=f"deb_{sid}")
        differently_abled = select_box(
            "Differently Abled/Disability", ["NO", "YES"], "differently_abled", f"disabled_{sid}"
        )
        medium = select_box("Medium of study", ["OTHER", "TAMIL", "ENGLISH"], "medium", f"medium_{sid}")
        part1_subject = select_box(
            "PART1 Subject",
            ["HINDI", "TAMIL", "ENGLISH", "ARABIC", "URUDHU", "MALAYALAM"],
            "part1_subject",
            f"part1_{sid}",
        )

    st.divider()
    st.markdown("### 📝 Qualification and application")
    q1, q2 = st.columns(2)

    with q1:
        qualifying_exam = st.text_input("Qualifying Exam", text_value("qualifying_exam_1"), key=f"qual_{sid}")
        cert_no = st.text_input("Certificate No", text_value("certificate_no_1"), key=f"cert_{sid}")
        passing_year = st.date_input(
            "Year of Passing",
            value=date_value("passing_year_1", date(2020, 1, 1)),
            min_value=date(1985, 1, 1),
            max_value=date.today(),
            key=f"passyr_{sid}",
        )

    with q2:
        appln_date = st.date_input(
            "Date of Application",
            value=date_value("appln_date", date.today()),
            min_value=date(2000, 1, 1),
            max_value=date(2100, 12, 31),
            key=f"applndate_{sid}",
        )
        application_no = st.text_input("Application No", text_value("application_no"), key=f"appno_{sid}")
        registration_no = st.text_input("Registration No", text_value("registration_no"), key=f"regno_{sid}")
        app_status = st.text_input("Application Status", text_value("app_status"), key=f"status_{sid}")

    st.divider()
    st.markdown("### 🤝 Reference")
    r1, r2, r3 = st.columns(3)

    with r1:
        reference_type = select_box("Student Reference Type", ["CENTRE", "SELF", "OTHER"], "reference_type", f"reftype_{sid}")
    with r2:
        reference_name = st.text_input(
            "Reference Person Name/Centre Name", text_value("reference_centre"), key=f"refname_{sid}"
        )
    with r3:
        reference_mobile = st.text_input(
            "Reference Centre/Person Mobile Number", text_value("ref_centre_mobile"),
            max_chars=10, key=f"refmobile_{sid}",
        )

    submitted = st.form_submit_button("💾 Save Changes")

    if submitted:
        errors = []

        if not name.strip():
            errors.append("Name required")
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            errors.append("Aadhaar must be 12 digits")
        if not mobile.isdigit() or len(mobile) != 10:
            errors.append("Mobile must be 10 digits")
        if whatsapp and (not whatsapp.isdigit() or len(whatsapp) != 10):
            errors.append("WhatsApp must be 10 digits")
        if reference_mobile and (not reference_mobile.isdigit() or len(reference_mobile) != 10):
            errors.append("Reference mobile must be 10 digits")

        if errors:
            for e in errors:
                st.error(e)
        else:
            if not whatsapp:
                whatsapp = mobile

            updates = {
                "name": name.strip(),
                "parent_guardian_name": parent_name,
                "aadhaar": aadhaar,
                "mobile": mobile,
                "whatsapp": whatsapp,
                "email": email,
                "location_type": location_type,
                "address": address,
                "abc_id": abc_id,
                "mother_tongue": mother_tongue,
                "gender": gender,
                "date_of_birth": dob.isoformat(),
                "religion": religion,
                "community": community,
                "caste": caste,
                "working_status": working_status,
                "marital_status": marital_status,
                "deb_id": deb_id,
                "differently_abled": differently_abled,
                "medium": medium,
                "part1_subject": part1_subject,
                "qualifying_exam_1": qualifying_exam,
                "certificate_no_1": cert_no,
                "passing_year_1": passing_year.isoformat(),
                "appln_date": appln_date.isoformat(),
                "application_no": application_no,
                "registration_no": registration_no,
                "app_status": app_status,
                "reference_type": reference_type,
                "reference_centre": reference_name,
                "ref_centre_mobile": reference_mobile,
            }

            try:
                supabase.table("student_data").update(updates).eq("s_no", sid).execute()
                st.success("✅ Student details saved. Search again to see the updated values.")
            except Exception as e:
                st.error(f"DB Error: {e}")
