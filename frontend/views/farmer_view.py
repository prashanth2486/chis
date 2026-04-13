import streamlit as st
import requests
import pandas as pd

from views.config import API_URL, auth_headers

@st.cache_data
def fetch_symptoms():
    try:
        res = requests.get(f"{API_URL}/symptoms", headers=auth_headers())
        if res.status_code == 200:
            return res.json()["symptoms"]
    except Exception:
        pass
    return []


def add_farmer_symptom(symptom: str) -> None:
    current_value = st.session_state.get("txtSymptoms", "")
    existing = [item.strip() for item in current_value.split(",") if item.strip()]
    if symptom not in existing:
        existing.append(symptom)
    st.session_state["txtSymptoms"] = ",".join(existing)


def clear_farmer_symptoms() -> None:
    st.session_state["txtSymptoms"] = ""

def render():
    st.title("🚜 Farmer Dashboard")
    st.markdown("Welcome to the Farmer Dashboard.")
    
    farmer_id = st.session_state.get("farmer_id") or st.session_state.get("user_id")

    st.success(f"Welcome, **{st.session_state.get('user_name', farmer_id)}**!")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Analyze Symptoms", "📋 Prediction History", "💬 Ask a Doctor"])
    
    with tab1:
        st.subheader("Symptom Checker & Disease Prediction")

        if "txtSymptoms" not in st.session_state:
            st.session_state["txtSymptoms"] = ""
            
        available_list = fetch_symptoms()
        if not available_list:
            st.info("No symptoms loaded from server.")
            available_list = []
            
        st.write("### Symptoms:")
        
        with st.container():
            cols = st.columns(5)
            for i, sym in enumerate(available_list):
                with cols[i % 5]:
                    st.button(
                        sym.replace('-', ' ').title(),
                        key=f"f_btn_{i}",
                        on_click=add_farmer_symptom,
                        args=(sym,),
                    )
                        
        st.markdown("<br/>", unsafe_allow_html=True)
        st.write("**Enter Symptoms**")
        
        symptoms_input = st.text_area("", height=150, key="txtSymptoms")
        
        col_submit, col_refresh, _ = st.columns([2, 2, 6])
        with col_submit:
            predict_clicked = st.button("Predict Disease", type="primary", use_container_width=True)
        with col_refresh:
            st.button("Refresh", use_container_width=True, on_click=clear_farmer_symptoms)
                
        if predict_clicked:
            if not symptoms_input:
                st.warning("Please enter symptoms.")
            else:
                with st.spinner("Analyzing symptoms..."):
                    try:
                        response = requests.post(f"{API_URL}/predict", params={"symptoms": symptoms_input}, headers=auth_headers())
                        if response.status_code == 200:
                            data = response.json()
                            disease = data.get("predicted_disease", "Unknown")
                            treatment = data.get("recommended_treatment", "None")
        
                            st.subheader("Disease Name:")
                            if disease == "Invalid Data" or disease == "Unknown":
                                st.error("No matching disease found.")
                            else:
                                st.markdown(f"**[{disease.title()}](#)**")
                                st.write("**Treatment:**")
                                st.info(treatment)
                                
                                # Auto-save to history
                                if farmer_id:
                                    try:
                                        hist_payload = {
                                            "farmer_id": farmer_id,
                                            "description": "Symptom Checker",
                                            "symptoms": symptoms_input,
                                            "disease": disease,
                                            "treatments": treatment
                                        }
                                        res_h = requests.post(f"{API_URL}/history", json=hist_payload, headers=auth_headers())
                                    except Exception:
                                        pass
                        else:
                            st.error(f"Error from API: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Failed to connect to the backend server.")

    with tab2:
        st.subheader("Your Past Predictions")
        if not farmer_id:
            st.info("Prediction history will appear after you log in as a farmer.")
        else:
            try:
                res = requests.get(f"{API_URL}/history/{farmer_id}", headers=auth_headers())
                if res.status_code == 200:
                    history_data = res.json()
                    if history_data:
                        df_hist = pd.DataFrame(history_data)
                        if 'date' in df_hist.columns:
                            df_hist['date'] = pd.to_datetime(df_hist['date']).dt.strftime('%Y-%m-%d %H:%M')
                        columns = [col for col in ['date', 'symptoms', 'disease', 'treatments', 'description'] if col in df_hist.columns]
                        st.dataframe(df_hist[columns], use_container_width=True)
                    else:
                        st.info("No prediction history found.")
                else:
                    st.error("Could not load prediction history.")
            except Exception:
                st.error("Could not fetch history tracking. Is the backend running?")
            
    with tab3:
        st.subheader("Ask a Doctor / Submit a Query")
        if not farmer_id:
            st.info("Doctor query tools are available after farmer login.")
        else:
            with st.form("query_form", clear_on_submit=True):
                query_text = st.text_area("What is your question?")
                submit_query = st.form_submit_button("Submit Question")
                if submit_query and query_text:
                    try:
                        payload = {"farmer_id": farmer_id, "query_text": query_text}
                        res_q = requests.post(f"{API_URL}/queries", json=payload, headers=auth_headers())
                        if res_q.status_code == 200:
                            st.success("Your question has been sent to the veterinary team!")
                        else:
                            st.error("Failed to submit query.")
                    except Exception:
                        st.error("Could not connect to backend.")
                    
        st.markdown("#### Your Previous Queries")
        if farmer_id:
            try:
                res_list = requests.get(f"{API_URL}/queries", params={"farmer_id": farmer_id}, headers=auth_headers())
                if res_list.status_code == 200:
                    queries_data = res_list.json()
                    if queries_data:
                        for q in queries_data:
                            with st.expander(f"Question on {pd.to_datetime(q['query_date']).strftime('%Y-%m-%d')} - {q['query_text'][:30]}..."):
                                st.write(f"**Your Question:** {q['query_text']}")
                                if q.get('reply_text'):
                                    st.info(f"**Doctor's Reply:** {q['reply_text']} (Answered: {pd.to_datetime(q['reply_date']).strftime('%Y-%m-%d')})")
                                else:
                                    st.warning("Awaiting doctor response.")
                    else:
                        st.info("You haven't submitted any questions yet.")
                else:
                    st.error("Could not fetch queries.")
            except Exception:
                st.error("Could not fetch queries.")
