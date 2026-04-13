import pandas as pd
import requests
import streamlit as st

from views.config import API_URL, auth_headers


def _get(path: str, params: dict | None = None):
    try:
        response = requests.get(f"{API_URL}{path}", params=params, headers=auth_headers())
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        pass
    return None


def _post(path: str, json: dict | None = None, files=None, params: dict | None = None):
    try:
        response = requests.post(f"{API_URL}{path}", json=json, files=files, params=params, headers=auth_headers())
        return response
    except requests.exceptions.ConnectionError:
        return None


def render():
    st.title("👨‍⚕️ Veterinary Doctor Dashboard")
    st.markdown("Real-world cattle case management, follow-up tracking, and clinical decision support.")

    doctor_id = st.session_state.get("user_id", "")
    users = _get("/users") or {"farmers": [], "doctors": []}
    farmers = users.get("farmers", [])
    farmer_options = {farmer["farmer_id"]: f'{farmer["farmer_id"]} - {farmer["name"]}' for farmer in farmers}

    tabs = st.tabs([
        "Cattle Registry",
        "Case Sheet & Prescription",
        "Patient History",
        "Query Management",
        "Lab Reports",
        "Eclat Mining",
    ])

    with tabs[0]:
        st.subheader("Cattle Registry")
        st.caption("Register cattle profiles under a farmer before creating case sheets.")

        if not farmer_options:
            st.info("Register at least one farmer before adding cattle profiles.")
        else:
            with st.form("cattle_registry_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    farmer_id = st.selectbox("Farmer", options=list(farmer_options.keys()), format_func=lambda x: farmer_options.get(x, x))
                    animal_tag = st.text_input("Animal Tag")
                    animal_name = st.text_input("Animal Name")
                    breed = st.text_input("Breed")
                with col2:
                    age_years = st.number_input("Age (years)", min_value=0.0, step=0.5)
                    weight_kg = st.number_input("Weight (kg)", min_value=0.0, step=1.0)
                    gender = st.selectbox("Gender", ["female", "male"])
                    pregnancy_status = st.selectbox("Pregnancy Status", ["not_applicable", "pregnant", "not_pregnant", "unknown"])
                with col3:
                    milk_yield_liters = st.number_input("Milk Yield (liters/day)", min_value=0.0, step=0.5)
                    village = st.text_input("Village")
                    notes = st.text_area("Notes")

                submitted = st.form_submit_button("Save Cattle Profile")
                if submitted and farmer_id and animal_tag and animal_name:
                    response = _post("/cattle", json={
                        "farmer_id": farmer_id,
                        "animal_tag": animal_tag,
                        "animal_name": animal_name,
                        "breed": breed,
                        "age_years": age_years or None,
                        "weight_kg": weight_kg or None,
                        "gender": gender,
                        "pregnancy_status": pregnancy_status,
                        "milk_yield_liters": milk_yield_liters or None,
                        "village": village,
                        "notes": notes,
                    })
                    if response and response.status_code == 200:
                        st.success("Cattle profile created.")
                        st.rerun()
                    else:
                        st.error("Failed to save cattle profile.")

        cattle_profiles = _get("/cattle") or []
        if cattle_profiles:
            st.dataframe(pd.DataFrame(cattle_profiles), use_container_width=True)
        else:
            st.info("No cattle profiles added yet.")

    cattle_profiles = _get("/cattle") or []
    cattle_options = {item["id"]: f'{item["animal_tag"]} - {item["animal_name"]} ({item["farmer_id"]})' for item in cattle_profiles}

    with tabs[1]:
        st.subheader("Case Sheet Entry & Prescription Generator")
        st.caption("Record symptoms, diagnosis, treatment, notes, recovery progress, and follow-up date for a cattle case.")

        if not cattle_options:
            st.info("Create at least one cattle profile first.")
        else:
            with st.form("case_sheet_form"):
                cattle_id = st.selectbox("Cattle", options=list(cattle_options.keys()), format_func=lambda x: cattle_options.get(x, str(x)))
                cattle_profile = next((item for item in cattle_profiles if item["id"] == cattle_id), None)
                col1, col2 = st.columns(2)
                with col1:
                    symptoms = st.text_area("Symptoms")
                    diagnosis = st.text_input("Initial Diagnosis")
                    confirmed_disease = st.text_input("Doctor Confirmed Disease")
                    treatment = st.text_area("Treatment / Medicines")
                with col2:
                    dosage_notes = st.text_area("Dosage Notes")
                    follow_up_date = st.date_input("Follow-Up Date")
                    recovery_progress = st.selectbox("Recovery Progress", ["under_treatment", "stable", "improving", "critical", "recovered"])
                    case_status = st.selectbox("Case Status", ["open", "under_review", "closed"])
                    emergency_flag = st.checkbox("Emergency Alert")
                notes = st.text_area("Clinical Notes")

                submitted = st.form_submit_button("Save Case Sheet")
                if submitted and cattle_profile and symptoms and diagnosis and treatment:
                    payload = {
                        "cattle_id": cattle_id,
                        "farmer_id": cattle_profile["farmer_id"],
                        "doctor_id": doctor_id,
                        "symptoms": symptoms,
                        "diagnosis": diagnosis,
                        "confirmed_disease": confirmed_disease or None,
                        "treatment": treatment,
                        "dosage_notes": dosage_notes,
                        "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
                        "notes": notes,
                        "recovery_progress": recovery_progress,
                        "emergency_flag": emergency_flag,
                        "case_status": case_status,
                    }
                    response = _post("/case-sheets", json=payload)
                    if response and response.status_code == 200:
                        result = response.json()
                        st.success("Case sheet saved.")
                        prescription = result["prescription"]
                        st.code(
                            "\n".join([
                                "Prescription Sheet",
                                f"Animal: {prescription['animal']} ({prescription['animal_tag']})",
                                f"Diagnosis: {prescription['diagnosis']}",
                                f"Treatment: {prescription['treatment']}",
                                f"Dosage Notes: {prescription['dosage_notes']}",
                                f"Follow-Up: {prescription['follow_up_date']}",
                            ]),
                            language="text",
                        )
                    else:
                        st.error("Failed to save case sheet.")

    with tabs[2]:
        st.subheader("Patient History")
        farmer_filter = st.selectbox("Filter by Farmer", options=["All"] + list(farmer_options.keys()), format_func=lambda x: "All Farmers" if x == "All" else farmer_options.get(x, x), key="history_farmer")
        case_history = _get("/case-sheets", params={"farmer_id": None if farmer_filter == "All" else farmer_filter}) or []
        if case_history:
            st.dataframe(pd.DataFrame(case_history), use_container_width=True)
        else:
            st.info("No case history found.")

    with tabs[3]:
        st.subheader("Farmer Query Management")
        queries = _get("/doctor/queries") or []
        if queries:
            for query in queries:
                title = f"{query['farmer_id']} - {query['status'].title()} - {query['query_text'][:45]}..."
                with st.expander(title):
                    st.write(f"**Question:** {query['query_text']}")
                    st.write(f"**Priority:** {query['priority']}")
                    st.write(f"**Current Status:** {query['status']}")
                    triage_col1, triage_col2 = st.columns(2)
                    with triage_col1:
                        priority = st.selectbox("Priority", ["normal", "urgent", "critical"], index=["normal", "urgent", "critical"].index(query["priority"]) if query["priority"] in ["normal", "urgent", "critical"] else 0, key=f"priority_{query['id']}")
                        status = st.selectbox("Status", ["pending", "answered", "follow_up_needed", "closed"], index=["pending", "answered", "follow_up_needed", "closed"].index(query["status"]) if query["status"] in ["pending", "answered", "follow_up_needed", "closed"] else 0, key=f"status_{query['id']}")
                    with triage_col2:
                        follow_up_needed = st.checkbox("Follow-Up Needed", value=query["follow_up_needed"], key=f"followup_{query['id']}")
                        doctor_notes = st.text_area("Doctor Notes", value=query["doctor_notes"], key=f"notes_{query['id']}")
                    if st.button("Save Triage", key=f"triage_btn_{query['id']}"):
                        response = _post(f"/doctor/queries/{query['id']}/triage", json={
                            "doctor_id": doctor_id,
                            "priority": priority,
                            "status": status,
                            "follow_up_needed": follow_up_needed,
                            "notes": doctor_notes,
                        })
                        if response and response.status_code == 200:
                            st.success("Query triage updated.")
                            st.rerun()
                    reply_text = st.text_area("Reply to Farmer", value=query.get("reply_text") or "", key=f"reply_{query['id']}")
                    if st.button("Send Reply", key=f"reply_btn_{query['id']}") and reply_text:
                        response = _post(f"/queries/{query['id']}/reply", json={"reply_text": reply_text})
                        if response and response.status_code == 200:
                            st.success("Reply sent.")
                            st.rerun()
        else:
            st.info("No farmer queries available.")

    with tabs[4]:
        st.subheader("Lab Report Upload")
        if not cattle_options:
            st.info("Create cattle profiles first.")
        else:
            with st.form("lab_report_form"):
                cattle_id = st.selectbox("Cattle", options=list(cattle_options.keys()), format_func=lambda x: cattle_options.get(x, str(x)), key="lab_cattle")
                report_type = st.selectbox("Report Type", ["blood_test", "scan", "wound_image", "other"])
                notes = st.text_area("Report Notes", key="lab_notes")
                file = st.file_uploader("Attach lab report", type=None, key="lab_file")
                submitted = st.form_submit_button("Upload Report")
                if submitted and file is not None:
                    files = {"file": (file.name, file.getvalue(), "application/octet-stream")}
                    response = _post("/lab-reports", files=files, params={
                        "cattle_id": cattle_id,
                        "report_type": report_type,
                        "notes": notes,
                    })
                    if response and response.status_code == 200:
                        st.success("Lab report uploaded.")
                        st.rerun()
                    else:
                        st.error("Failed to upload lab report.")

        reports = _get("/lab-reports") or []
        if reports:
            st.dataframe(pd.DataFrame(reports), use_container_width=True)

    with tabs[5]:
        st.markdown("### 🧬 Eclat Pattern Discovery Hub")
        st.markdown("""
        Upload historical medical records (Excel/CSV) to discover **Frequent Itemsets (common combinations)** and extract **Strong Association Rules (likely relationships)** between Symptoms, Diseases, and Drugs.
        """)

        st.sidebar.header("Algorithm Parameters")
        min_support = st.sidebar.slider("Minimum Support (%) (how common a pattern must be)", 1.0, 20.0, 4.0, 0.5) / 100.0
        min_confidence = st.sidebar.slider("Minimum Confidence (%) (how reliable a rule must be)", 10.0, 100.0, 50.0, 1.0) / 100.0

        uploaded_file = st.file_uploader("Upload Training Dataset (.xls, .xlsx, or .csv)", type=["xls", "xlsx", "csv"], key="doctor_eclat_file")

        if uploaded_file is not None:
            st.info(f"File uploaded: {uploaded_file.name}")

            if st.button("Run Eclat Algorithm", type="primary", key="doctor_eclat_run"):
                with st.spinner("Running high-performance Eclat tracking..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.ms-excel")}
                    response = _post("/eclat/run", files=files, params={"min_support": min_support, "min_confidence": min_confidence})
                    if response and response.status_code == 200:
                        result = response.json()
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Transactions", result["transaction_count"])
                        col2.metric("Frequent Itemsets Found", result["frequent_items_count"])
                        col3.metric("Strong Rules Extracted", result["rules_count"])

                        subtab1, subtab2 = st.tabs(["Strong Rules (likely relationships)", "Frequent Itemsets (common combinations)"])
                        with subtab1:
                            if result["rules_count"] > 0:
                                df_rules = pd.DataFrame(result["strong_rules"])
                                df_rules["confidence"] = (df_rules["confidence"] * 100).round(2).astype(str) + "%"
                                df_rules = df_rules.rename(columns={"lhs": "Antecedent (IF)", "rhs": "Consequent (THEN)", "confidence": "Confidence Level"})
                                st.table(df_rules)
                            else:
                                st.warning("No patterns found with the current thresholds.")
                        with subtab2:
                            if result["frequent_items_count"] > 0:
                                frequent_list = [{"Itemset": k, "Support Instances (Transaction IDs)": v} for k, v in result["frequent_items"].items()]
                                st.dataframe(pd.DataFrame(frequent_list), use_container_width=True)
                    else:
                        st.error("Failed to run Eclat algorithm.")
