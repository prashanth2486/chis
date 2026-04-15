import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=DM+Serif+Display:ital@0;1&display=swap');

            :root {
                --bg-soft: #f5f8f6;
                --surface: #ffffff;
                --surface-2: #f9fcfa;
                --text-main: #182b24;
                --text-muted: #4d645c;
                --brand: #1f6f5b;
                --brand-2: #2d8a72;
                --accent: #e07a45;
                --line: #d8e6df;
                --ring: rgba(31, 111, 91, 0.24);
                --shadow: 0 14px 35px rgba(21, 43, 35, 0.08);
            }

            [data-testid="collapsedControl"] {
                display: none;
            }

            .stApp, [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 5% 3%, rgba(224, 122, 69, 0.08), transparent 25%),
                    radial-gradient(circle at 95% 0%, rgba(45, 138, 114, 0.10), transparent 28%),
                    linear-gradient(170deg, #f8fbf9 0%, var(--bg-soft) 55%, #eef6f2 100%);
                color: var(--text-main);
                font-family: 'Manrope', 'Segoe UI', sans-serif;
            }

            .block-container {
                padding-top: 1.9rem;
                padding-bottom: 2.3rem;
            }

            h1, h2, h3 {
                color: var(--text-main);
                letter-spacing: -0.02em;
            }

            h1 {
                font-family: 'DM Serif Display', Georgia, serif;
                font-weight: 400;
            }

            p, label, .stCaption, .stMarkdown, .stAlert {
                color: var(--text-muted);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #f0f7f3 0%, #e8f2ee 100%);
                border-right: 1px solid var(--line);
            }

            [data-testid="stSidebar"] * {
                color: #1f3c33;
            }

            [data-testid="stSidebar"] .stButton button {
                border-radius: 12px;
                border: 1px solid rgba(224, 122, 69, 0.35);
                background: linear-gradient(135deg, #e88d5f 0%, #dd6f3b 100%);
                color: #fff;
                font-weight: 700;
                box-shadow: 0 10px 20px rgba(221, 111, 59, 0.22);
            }

            .stRadio > div {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 0.35rem;
                box-shadow: var(--shadow);
                gap: 0.32rem;
            }

            .stRadio [role="radio"] {
                border-radius: 12px;
                padding: 0.42rem 0.9rem;
                background: transparent;
                transition: all 0.18s ease;
            }

            .stRadio [aria-checked="true"] {
                background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
                color: #fff;
                font-weight: 700;
            }

            [data-baseweb="tab-list"] {
                gap: 0.45rem;
                padding-bottom: 0.4rem;
            }

            button[data-baseweb="tab"] {
                border-radius: 12px;
                border: 1px solid var(--line);
                background: #f7fbf8;
                color: #2b4b40;
                font-weight: 600;
                padding: 0.45rem 0.9rem;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
                border-color: transparent;
                color: #fff;
                box-shadow: 0 10px 20px rgba(31, 111, 91, 0.22);
            }

            .stButton button {
                border-radius: 12px;
                border: 1px solid #cfe2d9;
                background: #fff;
                color: #174335;
                font-weight: 700;
                transition: all 0.18s ease;
            }

            .stButton button[kind="primary"] {
                border: 1px solid #cfe2d9;
                background: #ffffff;
                color: #111111;
                box-shadow: 0 10px 20px rgba(24, 46, 38, 0.08);
            }

            .stButton button:hover {
                transform: translateY(-1px);
                box-shadow: 0 10px 22px rgba(24, 46, 38, 0.12);
            }

            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            div[data-baseweb="select"] > div,
            .stDateInput input {
                border-radius: 12px !important;
                border: 1px solid var(--line) !important;
                background: #fcfefd !important;
                color: var(--text-main) !important;
                -webkit-text-fill-color: var(--text-main) !important;
                caret-color: var(--brand) !important;
            }

            .stTextInput input::placeholder,
            .stTextArea textarea::placeholder {
                color: #799186 !important;
                opacity: 1 !important;
            }

            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stNumberInput input:focus,
            .stDateInput input:focus {
                border-color: var(--brand) !important;
                box-shadow: 0 0 0 3px var(--ring) !important;
            }

            [data-testid="stDataFrame"],
            [data-testid="stMetric"],
            [data-testid="stExpander"],
            .stAlert,
            .stForm {
                border: 1px solid var(--line);
                border-radius: 14px;
                background: var(--surface);
                box-shadow: var(--shadow);
            }

            [data-testid="stMetric"] {
                padding: 0.85rem 0.9rem;
            }

            .stAlert {
                box-shadow: none;
            }

            [data-testid="stHorizontalBlock"] > div:has(> .stMetric) {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 12px;
                padding: 0.35rem;
            }

            hr {
                border: 0;
                border-top: 1px solid var(--line);
                margin: 1rem 0 1.2rem 0;
            }

            input,
            textarea,
            [data-baseweb="input"] input,
            [data-baseweb="textarea"] textarea,
            [data-baseweb="base-input"] input {
                color: #111111 !important;
                -webkit-text-fill-color: #111111 !important;
                caret-color: #111111 !important;
            }
            @media (max-width: 900px) {
                .block-container {
                    padding-top: 1.2rem;
                }
                h1 {
                    font-size: 2rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
