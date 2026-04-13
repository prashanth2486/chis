import os

import streamlit as st


API_URL = os.getenv("PATTERN_PREDICTION_API_URL") or os.getenv("API_URL", "http://localhost:8000")
API_URL = API_URL.rstrip("/")


def auth_headers() -> dict:
    token = st.session_state.get("auth_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}
