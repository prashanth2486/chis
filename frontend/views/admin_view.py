import streamlit as st
import requests
import pandas as pd

from views.config import API_URL, auth_headers
from views.ui_helpers import api_failure, empty_state, render_section_header


def render():
    st.title("🛡️ Admin Dashboard")
    st.markdown("Welcome to the Administrative Dashboard.")

    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Manage Users", "Eclat Algorithm"])

    with tab1:
        render_section_header("System Metrics & Health", "Platform activity and disease telemetry overview.")

        with st.expander("Interview Demo Tools", expanded=False):
            st.caption("Populate realistic sample records in one click for a smooth demo flow.")
            if st.button("Generate Demo Data", type="primary", use_container_width=True):
                try:
                    seed_response = requests.post(f"{API_URL}/admin/demo-seed", headers=auth_headers())
                    if seed_response.status_code == 200:
                        payload = seed_response.json()
                        st.success(payload.get("message", "Demo data generated."))
                        c1, c2 = st.columns(2)
                        c1.write("Created")
                        c1.json(payload.get("created", {}))
                        c2.write("Already Existing")
                        c2.json(payload.get("existing", {}))
                    else:
                        try:
                            st.error(seed_response.json().get("detail", "Failed to generate demo data."))
                        except ValueError:
                            st.error("Failed to generate demo data.")
                except requests.exceptions.ConnectionError:
                    api_failure("Could not connect to backend for demo data seeding.")

        try:
            res_a = requests.get(f"{API_URL}/analytics", headers=auth_headers())
            if res_a.status_code == 200:
                data = res_a.json()
                metrics = data["metrics"]
                diseases = data["disease_counts"]

                # Top-level metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Registered Farmers", metrics["total_farmers"])
                col2.metric("Veterinary Doctors", metrics["total_doctors"])
                col3.metric("Farmer Queries", metrics["total_queries"])
                col4.metric("Total Predictions", metrics["total_predictions"])

                st.markdown("---")
                st.subheader("📈 Disease Frequency Distribution")
                if diseases:
                    # Convert to dataframe for charting
                    df_disease = pd.DataFrame(list(diseases.items()), columns=["Disease", "Count"]).set_index("Disease")
                    st.bar_chart(df_disease, color="#FF4B4B")
                else:
                    st.info("No prediction telemetry available to render charts yet.")
            else:
                api_failure("Failed to load analytics data.")
        except Exception:
            api_failure("Could not reach backend for analytics.")

    with tab2:
        render_section_header("Manage System Users", "User administration and onboarding controls.")
        try:
            res_users = requests.get(f"{API_URL}/users", headers=auth_headers())
            if res_users.status_code == 200:
                users_data = res_users.json()

                user_tab1, user_tab2, user_tab3 = st.tabs(["Farmers List", "Doctors List", "Register New Doctor"])

                with user_tab1:
                    if users_data.get("farmers"):
                        st.dataframe(pd.DataFrame(users_data["farmers"]), use_container_width=True)
                    else:
                        st.info("No farmers registered yet.")

                with user_tab2:
                    if users_data.get("doctors"):
                        st.dataframe(pd.DataFrame(users_data["doctors"]), use_container_width=True)
                    else:
                        st.info("No doctors registered yet.")

                with user_tab3:
                    st.write("Register a new Veterinary Doctor")
                    with st.form("register_doctor_form"):
                        ic_id = st.text_input("IC ID (e.g., IC202)")
                        name = st.text_input("Full Name")
                        email = st.text_input("Email")
                        contact = st.text_input("Contact Number")
                        address = st.text_area("Address")
                        city = st.text_input("City")
                        doc_pass = st.text_input("Password", type="password")

                        submit_doc = st.form_submit_button("Create Doctor Account")

                        if submit_doc and ic_id and name and doc_pass:
                            payload = {
                                "ic_id": ic_id,
                                "password": doc_pass,
                                "name": name,
                                "address": address,
                                "contact_no": contact,
                                "email_id": email,
                                "city_name": city,
                            }
                            res_doc = requests.post(f"{API_URL}/register/vdoctor", json=payload, headers=auth_headers())
                            if res_doc.status_code == 200:
                                st.success("Doctor registered successfully!")
                            else:
                                st.error(res_doc.json().get("detail", "Failed to register doctor."))
            else:
                api_failure("Could not fetch user directory.")
        except Exception:
            api_failure("Failed to connect to backend server.")

    with tab3:
        render_section_header("Pattern Prediction & Mining (Eclat)", "Upload structured transaction data and mine frequent patterns.")
        st.markdown(
            """
        Upload a transaction dataset to run the frequent pattern mining algorithm.
        The dataset must contain a **Data** column with comma-separated items.
        """
        )

        col1, col2 = st.columns(2)
        with col1:
            min_support = st.slider(
                "Minimum Support",
                min_value=0.01,
                max_value=1.0,
                value=0.04,
                step=0.01,
                help="Minimum threshold for itemset support (percentage of transactions containing the itemset).",
            )
        with col2:
            min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.1,
                max_value=1.0,
                value=0.50,
                step=0.05,
                help="Minimum threshold for rule confidence.",
            )

        uploaded_file = st.file_uploader("Upload Dataset (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

        if st.button("Run Eclat Algorithm", type="primary"):
            if uploaded_file is None:
                st.warning("Please upload a dataset file first.")
            else:
                with st.spinner("Running Pattern Mining Algorithm mapping itemsets..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                        params = {"min_support": min_support, "min_confidence": min_confidence}

                        response = requests.post(f"{API_URL}/eclat/run", files=files, params=params, headers=auth_headers())

                        if response.status_code == 200:
                            data = response.json()
                            st.success("Algorithm executed successfully!")

                            m_col1, m_col2, m_col3 = st.columns(3)
                            m_col1.metric("Total Transactions", data.get("transaction_count", 0))
                            m_col2.metric("Frequent Itemsets", data.get("frequent_items_count", 0))
                            m_col3.metric("Strong Rules", data.get("rules_count", 0))

                            st.divider()

                            st.subheader("Strong Association Rules")
                            rules = data.get("strong_rules", [])
                            if rules:
                                df_rules = pd.DataFrame(rules)
                                df_rules = df_rules.rename(
                                    columns={"lhs": "Antecedents (LHS)", "rhs": "Consequents (RHS)", "confidence": "Confidence"}
                                )
                                st.dataframe(df_rules, use_container_width=True)
                            else:
                                st.info("No strong rules found with the current confidence and support thresholds.")

                            st.divider()

                            st.subheader("Frequent Itemsets")
                            frequent_items = data.get("frequent_items", {})
                            if frequent_items:
                                df_items = pd.DataFrame(list(frequent_items.items()), columns=["Itemset", "Matched Transaction Indices"])
                                st.dataframe(df_items, use_container_width=True)
                            else:
                                st.info("No frequent itemsets found with the current support threshold.")

                        else:
                            try:
                                error_detail = response.json().get("detail", response.text)
                                st.error(f"Error from API: {error_detail}")
                            except ValueError:
                                st.error(f"Error from API: {response.text}")
                    except requests.exceptions.ConnectionError:
                        api_failure("Failed to connect to backend server.")
