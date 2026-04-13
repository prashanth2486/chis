import streamlit as st
import requests

from views.config import API_URL, auth_headers


def add_prediction_symptom(symptom: str) -> None:
    current_value = st.session_state.get("txtSymptomsAdmin", "")
    existing = [item.strip() for item in current_value.split(",") if item.strip()]
    if symptom not in existing:
        existing.append(symptom)
    st.session_state["txtSymptomsAdmin"] = ",".join(existing)


def clear_prediction_symptoms() -> None:
    st.session_state["txtSymptomsAdmin"] = ""

def render():

    st.title("💊 Symptom Checker & Disease Prediction")
    
    st.markdown("""
    Enter the symptoms your cattle are experiencing to receive a rapid prediction and corresponding treatment plan.
    """)
    
    AVAILABLE_SYMPTOMS = sorted([
        "frothy-salivation", "reduced-appetite", "resistance-oralExamination", "mouth-ulcer", "vesicles",
        "gas-bloat", "ptyyalism", "nasal-discharge", "asphyxia", "bruxism", "bloat", "increased-salivation",
        "difficulty-swallowing", "shallow-breathing", "coughing", "anorexia", "recurrent-bloat", "decreased-milk",
        "weight-loss", "diarrhea", "Increased-heart-rate", "Increased-breathing", "decreased-rumen-motility", "fever",
        "poorly-digested", "pain", "dysentery", "abdominal-pain", "mucosal-damage", "mucosal-petechiation",
        "GI-hemorrhage", "sunken-eyes", "twisting-stomach", "rectal-pain", "bleeding", "discharge", "sever-anemia",
        "diarrhoea", "Anemia", "colic-diarrhoea", "respiratory-noise", "dysphagia", "Increased-respiratory-rate",
        "dyspnea", "constipation", "grey/white-skin", "ash-skin", "red-patches", "red-patch", "papules", "nodules",
        "hair-loss", "thickened-skin", "lesions", "itching", "skin-thicken", "folds", "Pruritus", "alopatia",
        "vulvar-swelling", "labia-swelling", "vulvar-discharge", "vaginal-mucosa", "straining-urination",
        "grayish-discharge", "pale-yellow-discharge", "weakness", "fowl-smell", "arch-back", "deacreased-urination",
        "uterus-pus", "discharge-vulva", "swelling-abdomen", "enlarged-uterus", "red-brown-fluid", "uterine-discharge",
        "foetid-odour", "laminitis", "infection-uterus", "focal-hemorrhages", "subcutaneous-tissues", "bleeding-spots",
        "blood-from-skin", "tearing", "spasms-lids", "squinting", "spilling-tears", "epiphora", "avoidance-sunlight",
        "photophobia", "redness", "discharge-eye", "corneal-ulcers", "weeping", "closure-pain", "cornea-cloudy",
        "cornea-white", "eye-pain", "bleeding-nostril", "bleeding-eyeball", "bloody", "ulcerated", "friable",
        "foul-smelling", "mass-eye", "snoring", "febrile", "ear-pain", "head-shaking", "facial-nerve-paralysis",
        "red-gum", "salivation", "difficult-open-mouth", "staggering", "trembling", "convulsions", "swollen-thigh",
        "sound-thigh", "swelling-throat", "drooling", "slobbering", "smacking-lips", "shivering", "sore-feet",
        "blisters", "swollen-udder", "flabes", "blood-millshardness", "reddening", "abortion", "high-fever",
        "ocular-discharge", "eye-discharge", "seizures", "coffee-colour-urine", "jaundice", "brown-urine", "aggression",
        "rapid-pulse", "tachypnoea", "anaemia", "hypoglucemia", "seizure", "impaired-coordination", "lameness",
        "hyper-salivation", "choking", "aggressive-behavior", "attacking-animals"
    ])
    
    if "txtSymptomsAdmin" not in st.session_state:
        st.session_state["txtSymptomsAdmin"] = ""

    st.write("### Symptoms:")
    
    with st.container():
        cols = st.columns(5)
        for i, sym in enumerate(AVAILABLE_SYMPTOMS):
            with cols[i % 5]:
                st.button(
                    sym.replace('-', ' ').title(),
                    key=f"a_btn_{i}",
                    on_click=add_prediction_symptom,
                    args=(sym,),
                )
                    
    st.markdown("<br/>", unsafe_allow_html=True)
    st.write("**Enter Symptoms**")
    
    symptoms_input = st.text_area("", height=150, key="txtSymptomsAdmin")
    
    col_submit, col_refresh, _ = st.columns([2, 2, 6])
    with col_submit:
        predict_clicked = st.button("Predict Disease", type="primary", use_container_width=True)
    with col_refresh:
        st.button("Refresh", use_container_width=True, on_click=clear_prediction_symptoms)
            
    if predict_clicked:
        if not symptoms_input:
            st.warning("Please enter at least one symptom.")
        else:
            with st.spinner("Analyzing..."):
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
                            
                    else:
                        st.error(f"Error from API: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Failed to connect to the backend server. Is FastAPI running?")
