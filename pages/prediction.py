import streamlit as st
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from pathlib import Path

# ─── Configuration ───
LOCATION = "us-central1"
MODEL_NAME = "safety_data.severity_scorer_v2"
EMBEDDINGS_TABLE = "safety_data.report_embeddings_v2"
PROJECT_ID = "pure-loop-487819-j9" # Updated Project ID

# ─── Authentication ───
# Adapted from safety_bot.py to support both local secrets and Cloud Run default credentials
def get_credentials():
    local_creds = Path(__file__).parent.parent / "credentials.json"
    try:
        # Try loading from local secrets (development)
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return creds, st.secrets["gcp_service_account"].get("project_id", PROJECT_ID)
    except (KeyError, FileNotFoundError, Exception):
        if local_creds.exists():
            creds = service_account.Credentials.from_service_account_file(
                str(local_creds),
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            return creds, PROJECT_ID
        
        # Fallback to Application Default Credentials (production/Cloud Run)
        import google.auth
        creds, project_id = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return creds, project_id

# ─── Prediction Function ───
def get_severity_score(description, injury_category):
    """
    Uses Vertex AI embeddings + BigQuery ML to predict severity.
    Returns (score, label, probs_dict) or None on error.
    """
    try:
        creds, pid = get_credentials()
        
        # Initialize clients with the resolved credentials
        vertexai.init(project=pid, location=LOCATION, credentials=creds)
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        # Explicitly set location for BigQuery client
        bq_client = bigquery.Client(credentials=creds, project=pid, location=LOCATION)
        
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
    FROM ML.PREDICT(MODEL `{PROJECT_ID}.{MODEL_NAME}`,
        (SELECT
            '{injury_category}' as injury_category,
            {vector_str} as embedding_vector
        )
    );
    """
    
    try:
        # Run query in specific location
        result = list(bq_client.query(sql, location=LOCATION).result())
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

# ─── Retrain Function ───
def retrain_model():
    """
    Retrain the model using ALL data currently in BigQuery.
    Returns: dict with metrics or None on error
    """
    try:
        creds, _ = get_credentials()
        # Initialize BigQuery client with hardcoded PROJECT_ID for data
        bq_client = bigquery.Client(credentials=creds, project=PROJECT_ID, location=LOCATION)
        
        # Count rows
        count_sql = f"SELECT COUNT(*) as n FROM `{PROJECT_ID}.{EMBEDDINGS_TABLE}`"
        count = list(bq_client.query(count_sql).result())[0].n
        
        # Retrain Loop
        sql = f"""
        CREATE OR REPLACE MODEL `{PROJECT_ID}.{MODEL_NAME}`
        OPTIONS (
            model_type = 'LOGISTIC_REG',
            input_label_cols = ['is_high'],
            auto_class_weights = TRUE,
            data_split_method = 'RANDOM',
            data_split_eval_fraction = 0.2,
            max_iterations = 50,
            l2_reg = 0.1
        ) AS
        SELECT
            CASE WHEN risk_level = 'High' THEN 'High' ELSE 'Not_High' END as is_high,
            injury_category,
            embedding_vector
        FROM `{PROJECT_ID}.{EMBEDDINGS_TABLE}`;
        """
        bq_client.query(sql).result()
        
        # Evaluate
        eval_sql = f"SELECT * FROM ML.EVALUATE(MODEL `{PROJECT_ID}.{MODEL_NAME}`)"
        r = list(bq_client.query(eval_sql).result())[0]
        
        return {
            "recall": r.recall,
            "precision": r.precision,
            "f1": r.f1_score,
            "row_count": count,
        }
    except Exception as e:
        st.error(f"Retrain error: {e}")
        return None


# ─── UI Layout ───
# ─── UI Layout ───
st.markdown("""
<style>
    .page-header {
        padding: 0 0 20px 0;
        border-bottom: 1px solid #eaedf2; margin-bottom: 24px;
    }
    .page-header .title { font-size: 1.4rem; font-weight: 700; color: #1a202c; margin: 0; }
    .page-header .subtitle { font-size: 0.85rem; color: #718096; margin: 0; }

    /* Blue Button Style */
    div.stButton > button:first-child {
        background-color: #3182ce;
        color: white;
        border-color: #3182ce;
    }
    div.stButton > button:first-child:hover {
        background-color: #2b6cb0;
        border-color: #2b6cb0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div>
        <p class="title">Real-time Incident Severity Prediction</p>
        <p class="subtitle">AI-powered incident severity assessment</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Input
st.markdown("Enter a brief incident description to classify it as **High** or **Low** severity potential.")
desc_input = st.text_area(
    "Incident Description", 
    height=150, 
    placeholder="E.g., Technician noticed sparked wire in the breaker panel while removing tag..."
)

# Analyze Button with consistent styling (Streamlit primary button is used by default)
if st.button("Analyze Severity", type="primary", use_container_width=True):
    if not desc_input.strip():
        st.warning("Please enter a description.")
    else:
        with st.spinner("Analyzing incident severity..."):
            # Hardcoded 'No Injury' since context input was removed, ensuring model still runs
            result = get_severity_score(desc_input, "No Injury")
            
        if result:
            score, predicted, probs = result
            
            st.divider()
            
            # Result Display
            if predicted == "High":
                st.error("### 🔴 High Severity Potential")
                st.markdown("**Action Required:** Stop work and conduct immediate risk assessment.")
            else:
                st.success("### 🟢 Low Severity Potential")
                st.markdown("**Status:** Proceed with standard safety controls.")

# ─── Retrain Section ───
st.divider()
with st.expander("🔄 Retrain Model"):
    st.caption(
        "Click below to retrain the model using all data in BigQuery "
        "(original training data + any new reports submitted via forms)."
    )
    if st.button("🚀 Retrain Model", type="primary", key="sev_retrain"):
        with st.spinner("Retraining model... this takes ~2–3 minutes."):
            metrics = retrain_model()
        if metrics:
            st.success(f"✅ Model retrained on **{metrics['row_count']}** reports!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Recall", f"{metrics['recall']:.2f}")
            col2.metric("Precision", f"{metrics['precision']:.2f}")
            col3.metric("F1 Score", f"{metrics['f1']:.2f}")
