import streamlit as st

def render():
    st.markdown("""
    Welcome to the modernized **Cattle Health Intelligence System**.

    This system allows:
    * **Farmers** to capture symptoms, review prediction history, and communicate with the veterinary team.
    * **Veterinary Doctors (VDoctors)** to manage cattle case sheets, prescriptions, lab reports, and data-driven analysis.
    * **Admins** to manage users, dashboards, and overall platform visibility.
    """)

    st.markdown("---")
    st.markdown("### Platform Overview")
    st.markdown("""
    The platform runs on a modern Python stack:
    - **FastAPI** drives the API endpoints.
    - **SQLite** handles the persistence layer.
    - **mlxtend** Python library executes the pattern mining.
    - **Streamlit** powers the interactive user experience.
    """)
