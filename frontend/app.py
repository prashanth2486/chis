import streamlit as st
import views.home_view as home_view
import views.prediction_view as prediction_view
import views.doctor_view as doctor_view
import views.farmer_view as farmer_view
import views.admin_view as admin_view
import views.login_view as login_view

st.set_page_config(
    page_title="Cattle Health Intelligence System",
    page_icon="Cattle",
    layout="wide",
)

st.markdown("""
    <style>
        [data-testid="collapsedControl"] {
            display: none
        }
        .block-container {
            padding-top: 2.25rem;
        }
        div[role="radiogroup"] {
            margin-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize Auth State
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

# If not logged in, enforce login view
if not st.session_state['user_role']:
    login_view.render()
else:
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Sidebar logout & user badge
    with st.sidebar:
        st.write(f"Logged in as **{st.session_state.get('user_name', '')}**")
        st.caption(f"Role: {st.session_state['user_role'].capitalize()}")
        if st.button("Logout", type="primary"):
            st.session_state.clear()
            st.rerun()

    # Determine available pages based on role
    PAGES = {"HOME": "🏠 Home"}

    role = st.session_state['user_role']
    if role == "admin":
        PAGES["PREDICTION"] = "💊 Prediction System"
        PAGES["FARMER"] = "🚜 Farmer Dashboard"
        PAGES["DOCTOR"] = "🩺 Doctor Dashboard"
        PAGES["ADMIN"] = "🛡️ Admin Dashboard"
    elif role == "farmer":
        PAGES["FARMER"] = "🚜 Farmer Dashboard"
    elif role == "doctor":
        PAGES["PREDICTION"] = "💊 Prediction System"
        PAGES["DOCTOR"] = "🩺 Doctor Dashboard"

    selected_page = st.radio(
        "Navigation",
        options=list(PAGES.values()),
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    if selected_page == PAGES.get("HOME"):
        home_view.render()
    elif selected_page == PAGES.get("PREDICTION"):
        prediction_view.render()
    elif selected_page == PAGES.get("DOCTOR"):
        doctor_view.render()
    elif selected_page == PAGES.get("FARMER"):
        farmer_view.render()
    elif selected_page == PAGES.get("ADMIN"):
        admin_view.render()
