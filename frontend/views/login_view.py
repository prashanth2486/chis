import requests
import streamlit as st

from views.config import API_URL


def _login(user_id: str, password: str, role: str) -> None:
    try:
        res = requests.post(
            f"{API_URL}/login",
            json={
                "user_id": user_id,
                "password": password,
                "role": role,
            },
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state["user_id"] = data["user_id"]
            st.session_state["user_role"] = data["role"]
            st.session_state["user_name"] = data["name"]
            st.session_state["auth_token"] = data.get("access_token", "")
            if data["role"] == "farmer":
                st.session_state["farmer_id"] = data["user_id"]
            st.success(f"Welcome, {data['name']}!")
            st.rerun()
        else:
            st.error(res.json().get("detail", "Invalid credentials."))
    except Exception:
        st.error("Could not connect to the backend server.")


def _register_farmer(new_id: str, name: str, contact: str, address: str, new_pass: str) -> None:
    try:
        res = requests.post(
            f"{API_URL}/register/farmer",
            json={
                "farmer_id": new_id,
                "password": new_pass,
                "name": name,
                "contact_no": contact,
                "address": address,
            },
        )
        if res.status_code == 200:
            st.success("Farmer registration successful. You can log in now.")
        else:
            st.error(res.json().get("detail", "Registration failed."))
    except Exception:
        st.error("Could not connect to the backend server.")


def _register_doctor(new_id: str, name: str, email: str, contact: str, city: str, address: str, new_pass: str) -> None:
    try:
        res = requests.post(
            f"{API_URL}/register/vdoctor",
            json={
                "ic_id": new_id,
                "password": new_pass,
                "name": name,
                "address": address,
                "contact_no": contact,
                "email_id": email,
                "city_name": city,
            },
        )
        if res.status_code == 200:
            st.success("Doctor registration successful. You can log in now.")
        else:
            st.error(res.json().get("detail", "Registration failed."))
    except Exception:
        st.error("Could not connect to the backend server.")


def _hero() -> None:
    st.markdown(
        """
        <style>
            .visitor-shell {
                background:
                    radial-gradient(circle at top left, rgba(233, 117, 85, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(44, 96, 78, 0.16), transparent 24%),
                    linear-gradient(135deg, #fbf6ef 0%, #fffdf9 55%, #f2f7f3 100%);
                border: 1px solid rgba(32, 63, 52, 0.08);
                border-radius: 28px;
                padding: 2.4rem 2.2rem 1.9rem 2.2rem;
                box-shadow: 0 22px 65px rgba(35, 41, 49, 0.08);
                margin-bottom: 1.6rem;
            }
            .visitor-kicker {
                display: inline-block;
                padding: 0.35rem 0.8rem;
                border-radius: 999px;
                background: rgba(32, 63, 52, 0.08);
                color: #214535;
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            .visitor-title {
                margin: 1rem 0 0.4rem 0;
                color: #1f2933;
                font-size: 3rem;
                line-height: 1.05;
                font-weight: 800;
            }
            .visitor-subtitle {
                color: #52606d;
                font-size: 1.08rem;
                max-width: 850px;
                margin-bottom: 1.5rem;
            }
            .public-section {
                background: rgba(255,255,255,0.76);
                border: 1px solid rgba(31, 41, 51, 0.08);
                border-radius: 24px;
                padding: 1.4rem;
                box-shadow: 0 18px 55px rgba(35, 41, 49, 0.06);
            }
            .mini-banner {
                border-radius: 22px;
                padding: 1.1rem 1.2rem;
                background: linear-gradient(135deg, rgba(33,69,53,0.08), rgba(233,117,85,0.08));
                border: 1px solid rgba(31, 41, 51, 0.08);
                margin-bottom: 1rem;
            }
            @media (max-width: 900px) {
                .visitor-title {
                    font-size: 2.3rem;
                }
            }
        </style>
        <div class="visitor-shell">
            <div class="visitor-kicker">Digital Veterinary Intelligence</div>
            <div class="visitor-title">Cattle Health Intelligence System</div>
            <div class="visitor-subtitle">
                Cattle disease prediction and treatment recommendation platform for farmers, veterinary doctors, and administrators.
                Built to support faster decisions, cleaner case handling, and better cattle care in the real world.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    _hero()

    tabs = st.tabs(["Home", "Farmer", "Doctor", "Admin", "About"])

    with tabs[0]:
        st.markdown('<div class="public-section">', unsafe_allow_html=True)
        st.markdown("### Smarter cattle care, designed for field use")
        st.markdown(
            """
            This platform brings cattle health operations into one connected workflow.

            - Farmers can enter symptoms, get quick disease guidance, and maintain case history.
            - Veterinary doctors can manage case sheets, treatment plans, lab uploads, and query handling.
            - Admin users can monitor adoption, control user access, and run deeper data analysis tools.
            """
        )

        col1, col2 = st.columns([1.1, 0.9])
        with col1:
            st.markdown(
                """
                #### What this project can do
                - Predict likely cattle disease from symptom combinations
                - Recommend treatment guidance from the configured medical logic
                - Preserve farmer-side prediction history and doctor communication
                - Support doctor workflows such as case documentation and prescription creation
                - Discover historical data patterns using Eclat pattern mining
                """
            )
        with col2:
            st.markdown(
                """
                <div class="mini-banner">
                    <h4 style="margin:0;color:#1f2933;">Real-world use cases</h4>
                    <p style="margin:0.4rem 0 0 0;color:#52606d;">
                        Early cattle health screening, veterinary triage, disease trend observation, structured record keeping,
                        and practical support for rural livestock care teams.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info("Designed for cattle-focused use today, with a workflow that can grow into a larger livestock health platform.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="public-section">', unsafe_allow_html=True)
        st.markdown("### Farmer Portal")
        st.markdown(
            """
            Farmers use this portal to report cattle symptoms, receive instant prediction support,
            review previous cases, and communicate with veterinary doctors.
            """
        )
        st.markdown(
            """
            #### Farmer role in this project
            - Register and maintain access to the platform
            - Enter cattle symptoms for rapid disease prediction
            - Track past predictions and treatment suggestions
            - Ask questions to doctors and receive guidance
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Farmer Login")
            with st.form("farmer_login_form"):
                farmer_login_id = st.text_input("Farmer ID")
                farmer_login_password = st.text_input("Password", type="password")
                farmer_login_submit = st.form_submit_button("Login as Farmer")
                if farmer_login_submit and farmer_login_id and farmer_login_password:
                    _login(farmer_login_id, farmer_login_password, "farmer")

        with col2:
            st.markdown("#### Register as Farmer")
            with st.form("register_farmer_form"):
                new_id = st.text_input("Choose Farmer ID")
                name = st.text_input("Full Name")
                contact = st.text_input("Contact Number")
                address = st.text_area("Address")
                new_pass = st.text_input("Password", type="password")
                reg_submit = st.form_submit_button("Create Farmer Account")
                if reg_submit and new_id and name and new_pass:
                    _register_farmer(new_id, name, contact, address, new_pass)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="public-section">', unsafe_allow_html=True)
        st.markdown("### Doctor Portal")
        st.markdown(
            """
            Veterinary doctors use this workspace to manage cattle cases, respond to farmer issues,
            maintain prescription-quality records, and review analytical pattern outputs.
            """
        )
        st.markdown(
            """
            #### Doctor role in this project
            - Register and access the veterinary dashboard
            - Review farmer-reported health problems
            - Create cattle case sheets and treatment plans
            - Upload lab evidence and maintain structured records
            - Use Eclat mining to understand repeated symptom or disease patterns
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Doctor Login")
            with st.form("doctor_login_form"):
                doctor_login_id = st.text_input("Doctor ID")
                doctor_login_password = st.text_input("Password", type="password")
                doctor_login_submit = st.form_submit_button("Login as Doctor")
                if doctor_login_submit and doctor_login_id and doctor_login_password:
                    _login(doctor_login_id, doctor_login_password, "doctor")

        with col2:
            st.markdown("#### Register as Doctor")
            with st.form("register_doctor_form"):
                new_id = st.text_input("Choose Doctor ID")
                name = st.text_input("Full Name", key="doctor_name")
                email = st.text_input("Email Address")
                contact = st.text_input("Contact Number", key="doctor_contact")
                city = st.text_input("City Name")
                address = st.text_area("Clinic / Address", key="doctor_address")
                new_pass = st.text_input("Password", type="password", key="doctor_password")
                reg_submit = st.form_submit_button("Create Doctor Account")
                if reg_submit and new_id and name and new_pass and city:
                    _register_doctor(new_id, name, email, contact, city, address, new_pass)
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="public-section">', unsafe_allow_html=True)
        st.markdown("### Admin Console")
        st.markdown(
            """
            The admin area has overall control of the platform. It is intended for project owners,
            supervisors, or operational administrators.
            """
        )
        st.markdown(
            """
            #### What admin can control
            - User access across farmers and doctors
            - System-level dashboards and utilization metrics
            - Dataset uploads and mining workflows
            - Platform visibility, operational monitoring, and governance
            """
        )

        with st.form("admin_login_form"):
            admin_login_id = st.text_input("Admin ID", value="admin")
            admin_login_password = st.text_input("Admin Password", type="password")
            admin_login_submit = st.form_submit_button("Login as Admin")
            if admin_login_submit and admin_login_id and admin_login_password:
                _login(admin_login_id, admin_login_password, "admin")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="public-section">', unsafe_allow_html=True)
        st.markdown("### About Our Services")
        st.markdown(
            """
            We provide digital support for cattle health management with a focus on practical field use,
            veterinary coordination, and faster information flow between farmers and doctors.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                #### Services
                - Cattle disease prediction support
                - Treatment recommendation guidance
                - Farmer-to-doctor communication workflow
                - Veterinary case record management
                - Historical data analysis and pattern mining
                - Admin monitoring and operational control
                """
            )
        with col2:
            st.markdown(
                """
                #### Contact
                - Support Desk: `+91 98765 43210`
                - Veterinary Coordination: `+91 91234 56789`
                - Email: `care@cattlehealthintelligence.com`
                - Service Hours: `Mon-Sat, 9:00 AM to 6:00 PM`
                - Location: `Livestock Digital Health Centre, India`
                """
            )

        st.markdown(
            """
            #### Why this platform matters
            Better cattle health outcomes depend on faster reporting, clearer case records, and stronger coordination
            between farm owners and veterinary professionals. This platform is designed to support that journey with
            a modern digital workflow.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)
