import streamlit as st


def render_section_header(title: str, caption: str | None = None) -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def api_failure(message: str = "Request failed. Please try again.") -> None:
    st.error(f"{message} If this continues, check backend health at /health.")


def empty_state(message: str) -> None:
    st.info(message)
