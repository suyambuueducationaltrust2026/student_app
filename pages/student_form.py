import streamlit as st
import time
from datetime import date, datetime
from utils import supabase, get_universities, get_programs, get_courses

# ----------------------
# SESSION CHECK
# ----------------------
if "profile" not in st.session_state:
    st.error("⚠️ Session expired. Please login again.")
    st.stop()

profile = st.session_state.profile

# ----------------------
# ROLE CHECK
# ----------------------
if profile["role_code"] in [2, 3]:

    st.title("👤 Student Registration")

    # ----------------------
    # Fetch all year data
    # ----------------------
    @st.cache_data
    def get_univ_year():
        return supabase.table("univ_year") \
            .select("name, code, type, parent_id") \
            .execute().data

    all_data = get_univ_year()

    def filter_by_type_and_parent(data, type_name, parent_code):
        return [row for row in data if row["type"] == type_name and row["parent_id"] == parent_code]

    # ----------------------
    # Admission Section
    # ----------------------
    st.subheader("📅 Admission Details")

    col1, col2, col3 = st.columns(3)

    # Admission
    with col1:
        admission_data = [row for row in all_data if row["type"] == "admission_type"]
        admission_dict = {a["name"]: a["code"] for a in admission_data}

        admission_type_name = st.selectbox("Admission Type", list(admission_dict.keys()))
        admission_code = admission_dict[admission_type_name]

    # Pattern
    with col2:
        pattern_data = filter_by_type_and_parent(all_data, "pattern", admission_code)
        pattern_dict = {p["name"]: p["code"] for p in pattern_data}

        pattern_name = st.selectbox("Pattern", list(pattern_dict.keys()))
        pattern_code = pattern_dict.get(pattern_name)

    # Year
    with col3:
        if admission_type_name.lower() == "academic year":
            year_type = "academic_year"
        elif admission_type_name.lower() == "calendar year":
            year_type = "calendar_year"
        else:
            year_type = None

        if year_type:
            year_data = filter_by_type_and_parent(all_data, year_type, admission_code)
            year_dict = {y["name"]: y["code"] for y in year_data}

            year_name = st.selectbox("Year", list(year_dict.keys()))
            year_code = year_dict.get(year_name)
        else:
            year_name, year_code = None, None
            st.warning("No year available")

    # ----------------------
    # Course Section
    # ----------------------
    st.subheader("🎓 Course Selection")
    courcol1, courcol2 = st.columns(2)

    with courcol1:
        universities = get_universities()
        uni_dict = {u["name"]: (u["id"], u["code"]) for u in universities}

        univ_name = st.selectbox("University", list(uni_dict.keys()))
        univ_id, univ_code = uni_dict[univ_name]

        programs = get_programs()
        program_dict = {p["name"]: (p["id"], p["code"]) for p in programs}

        program_name = st.selectbox("Program", list(program_dict.keys()))
        program_id, program_code = program_dict[program_name]

        courses = get_courses(program_id)

        if courses:
            course_dict = {c["name"]: (c["id"], c["code"]) for c in courses}
            course_name = st.selectbox("Course", list(course_dict.keys()))
            course_id, course_code = course_dict[course_name]
        else:
            course_name, course_id, course_code = None, None, None
            st.warning("No courses found")

    with courcol2:
        medium = st.selectbox("Medium of study", ["OTHER", "TAMIL", "ENGLISH"])
        courseduration = st.selectbox("Course Duration", ["1", "2", "3", "4"])
        part1lang = st.selectbox("PART1 Subject", ["HINDI","TAMIL","ENGLISH","ARABIC","URUDHU","MALAYALAM"])

    # ----------------------
    # FORM
    # ----------------------
    st.subheader("📝 Student Details")

    with st.form("student_form"):

        col1, col2 = st.columns(2)

        # Personal
        with col1:
            name = st.text_input("Student Name")
            parentname = st.text_input("Parent/Guardian Name")
            aadhaar = st.text_input("Aadhaar Number", max_chars=12)
            mobile = st.text_input("Mobile Number", max_chars=10)
            whatsapp = st.text_input("WhatsApp No", max_chars=10)
            location_type = st.selectbox("Location Type", ["Rural","Urban"])
            address = st.text_area("Address")
            abc_id = st.text_input("ABC ID")

        with col2:
            gender = st.selectbox("Gender", ["Male","Female","Other"])
            Dob = st.date_input("Date of Birth", value=date(1985,1,1))
            religion = st.selectbox("Religion",["HINDU","CHRISTIAN","ISLAM","Other"])
            community = st.selectbox("Community", ["BC","MBC","SC","ST","FC","Other"])
            caste = st.text_input("Caste")
            email = st.text_input("Email ID")
            workstatus = st.selectbox("Working Status",["Not Working","Govt Job","Private Job"])
            Maritalstatus = st.selectbox("Marital Status",["Not Married","Married"])
            deb_id = st.text_input("DEB ID")

        # Academic
        col3, col4 = st.columns(2)
        with col3:
            qualifying_exam1 = st.text_input("Qualifying Exam")
            qualicertno1 = st.text_input("Certificate No")
        with col4:
            qualipass_year1 = st.date_input("Year of Passing", value=date(2020,1,1),min_value=date(1985,1,1),max_value=date.today())
            applndate = st.date_input("Date of Application", value=date.today())

        submitted = st.form_submit_button("Submit")

        if submitted:

            errors = []

            # ----------------------
            # VALIDATION
            # ----------------------
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                errors.append("Aadhaar must be 12 digits")

            if not mobile.isdigit() or len(mobile) != 10:
                errors.append("Mobile must be 10 digits")

            if whatsapp and (not whatsapp.isdigit() or len(whatsapp) != 10):
                errors.append("WhatsApp must be 10 digits")

            if not name:
                errors.append("Name required")

            if not course_name:
                errors.append("Course required")

            if errors:
                for e in errors:
                    st.error(e)
                st.stop()

            if not whatsapp:
                whatsapp = mobile

            # ----------------------
            # DUPLICATE CHECK
            # ----------------------
            duplicate = supabase.table("student_data") \
                .select("s_no") \
                .eq("aadhaar", aadhaar) \
                .eq("year_code", year_code) \
                .eq("pattern_code", pattern_code) \
                .eq("university_id", univ_id) \
                .eq("program_id", program_id) \
                .limit(1) \
                .execute()

            if duplicate.data:
                st.warning("⚠️ Student already registered for this combination")
                st.stop()

            # ----------------------
            # INSERT
            # ----------------------
            student_data = {
                "name": name,
                "aadhaar": aadhaar,
                "mobile": mobile,
                "whatsapp": whatsapp,
                "admission_type": admission_type_name,
                "admission_code": admission_code,
                "pattern": pattern_name,
                "pattern_code": pattern_code,
                "year": year_name,
                "year_code": year_code,
                "university_name": univ_name,
                "university_id": univ_id,
                "program_name": program_name,
                "program_id": program_id,
                "course_name": course_name,
                "course_id": course_id,
                "course_code": course_code,
                "role_name": profile.get("name"),
                "role_code": profile.get("role_code"),
                "gender": gender,
                "date_of_birth": Dob.isoformat(),
                "religion": religion,
                "community": community,
                "caste": caste,
                "qualifying_exam_1": qualifying_exam1,
                "certificate_no_1": qualicertno1,
                "passing_year_1": qualipass_year1.isoformat(),
                "parent_guardian_name": parentname,
                "location_type": location_type,
                "address": address,
                "email": email,
                "medium": medium,
                "course_duration": int(courseduration),
                "working_status": workstatus,
                "marital_status": Maritalstatus,
                "deb_id": deb_id,
                "abc_id": abc_id,
                "part1_subject": part1lang,
                "registration_no": None,
                "application_no": None,
                "app_status": "pending",
                "appln_date": applndate.isoformat(),
                "entry_date": datetime.now().isoformat()
            }

            try:
                supabase.table("student_data").insert(student_data).execute()
                st.success("✅ Student Registered Successfully")
                time.sleep(2)
                st.success("💾 Saved to database")

                # 🔄 Reset form
                st.rerun()

            except Exception as e:
                st.error(f"DB Error: {e}")