
import streamlit as st
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ─── Configuration ───────────────────────────────────────────────
CREDENTIALS_FILE = "credentials.json"
LOCATION = "us-central1"
MODEL_NAME = "safety_data.severity_scorer_v2"

# Page Config
st.set_page_config(
    page_title="Safety AI Predictor",
    page_icon="🛡️",
    layout="centered"
)

# Title & styling
st.title("🛡️ Safety Risk AI")
st.markdown("### Real-time Incident Severity Prediction")
st.markdown("Enter a safety report description below to get a **severity score (0–100)**.")

# ─── Context Inputs ──────────────────────────────────────────────
with st.expander("⚙️ Advanced Context (Optional)"):
    st.caption("Select the injury outcome to improve prediction accuracy.")
    injury_input = st.selectbox("Injury Category", [
        "No Injury", "First Aid", "Medical Treatment", "Lost Time"
    ], index=0)


# ─── Prediction Function ─────────────────────────────────────────
def get_severity_score(description, injury_category):
    """
    Uses Vertex AI embeddings + BigQuery ML to predict severity.
    Returns (score, label, probs_dict) or None on error.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"Credentials file '{CREDENTIALS_FILE}' not found.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        pid = creds.project_id
        
        vertexai.init(project=pid, location=LOCATION, credentials=creds)
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        bq_client = bigquery.Client(credentials=creds, project=pid)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

    # Generate embedding
    try:
        embeddings = embedding_model.get_embeddings([description])
        vector = embeddings[0].values
        vector_str = "[" + ", ".join(map(str, vector)) + "]"
    except Exception as e:
        st.error(f"Embedding Error: {e}")
        return None

    # BigQuery ML Prediction — binary model (High vs Not_High)
    sql = f"""
    SELECT
        predicted_is_high,
        predicted_is_high_probs
    FROM ML.PREDICT(MODEL `{pid}.{MODEL_NAME}`,
        (SELECT
            '{injury_category}' as injury_category,
            {vector_str} as embedding_vector
        )
    );
    """
    
    try:
        result = list(bq_client.query(sql).result())
        if not result:
            st.error("No results from BigQuery.")
            return None
        
        row = result[0]
        predicted = row.predicted_is_high
        probs = {p['label']: p['prob'] for p in row.predicted_is_high_probs}
        
        # Score: P(High) mapped to 0-100
        p_high = probs.get('High', 0)
        score = p_high * 100
        
        return score, predicted, probs
        
    except Exception as e:
        st.error(f"BigQuery Error: {e}")
        return None


# ─── UI Input ─────────────────────────────────────────────────────
desc_input = st.text_area(
    "Incident Description", 
    height=150, 
    placeholder="E.g., Technician noticed sparked wire in the breaker panel while removing tag..."
)

if st.button("Analyze", type="primary"):
    if not desc_input.strip():
        st.warning("Please enter a description.")
    else:
        with st.spinner("Analyzing..."):
            result = get_severity_score(desc_input, injury_input)
            
        if result:
            score, predicted, probs = result
            
            st.divider()
            
            # ─── Result Display ───────────────────────────────────
            if predicted == "High":
                st.markdown(
                    '<h1><span style="display:inline-block;width:50px;height:50px;'
                    'border-radius:50%;background:#ff4b4b;vertical-align:middle;'
                    'margin-right:10px;"></span>HIGH SEVERITY</h1>',
                    unsafe_allow_html=True
                )
                st.error(
                    "👉 **STOP WORK.** This incident has significant risk potential. "
                    "Conduct an immediate risk assessment and notify your supervisor."
                )
            else:
                st.markdown(
                    '<h1><span style="display:inline-block;width:50px;height:50px;'
                    'border-radius:50%;background:#21c354;vertical-align:middle;'
                    'margin-right:10px;"></span>LOW SEVERITY</h1>',
                    unsafe_allow_html=True
                )
                st.success(
                    "👉 Proceed with standard safety controls. "
                    "Low severity detected — monitor and log as usual."
                )
            
            # ─── Debug Info (collapsed) ───────────────────────────
            with st.expander("🔍 Debug Info"):
                st.json({
                    "model": MODEL_NAME,
                    "predicted_class": predicted,
                    "probabilities": probs,
                    "recall": 0.71,
                    "precision": 0.71,
                })
