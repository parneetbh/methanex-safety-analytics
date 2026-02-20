"""
Severity Prediction Tab — Drop into your multi-tab Streamlit app.
=================================================================
HOW TO USE:
    1. Copy this file into your project
    2. Copy credentials.json into your project root
    3. pip install google-cloud-bigquery google-cloud-aiplatform vertexai streamlit pandas
    4. In your main app, import and call:

        from severity_tab import render_severity_tab
        
        tab1, tab2 = st.tabs(["Other Tab", "Severity Predictor"])
        with tab2:
            render_severity_tab()

TWO THINGS THIS FILE DOES:
    A) Predicts severity (High / Low) from a text description
    B) Appends new form submissions to the model's training data
    C) Retrains the model with a single button click

IMPORTANT:
    - credentials.json must be for GCP project: pure-loop-487819-j9
    - The model lives in BigQuery: safety_data.severity_scorer_v2
    - Required columns when appending: what_happened, risk_level, injury_category
"""

import streamlit as st
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import time
import os

# ─── Configuration (do NOT change these) ─────────────────────────
CREDENTIALS_FILE = "credentials.json"
PROJECT_ID = "pure-loop-487819-j9"  # fallback when no credentials file
LOCATION = "us-central1"
DATASET = "safety_data"
MODEL_NAME = f"{DATASET}.severity_scorer_v2"
EMBEDDINGS_TABLE = f"{DATASET}.report_embeddings_v2"


def _get_clients():
    """
    Initialize GCP clients. Returns (bq_client, embedding_model, project_id).
    
    - LOCAL: Uses credentials.json file
    - CLOUD RUN: Uses Application Default Credentials (no file needed)
    """
    if os.path.exists(CREDENTIALS_FILE):
        # Local development — use the service account key file
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        pid = creds.project_id
        vertexai.init(project=pid, location=LOCATION, credentials=creds)
        emb_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        bq = bigquery.Client(credentials=creds, project=pid)
    else:
        # Cloud Run / deployed — use Application Default Credentials
        import google.auth
        creds, pid = google.auth.default()
        pid = pid or PROJECT_ID
        vertexai.init(project=pid, location=LOCATION)
        emb_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        bq = bigquery.Client(project=pid)
    return bq, emb_model, pid


# ═══════════════════════════════════════════════════════════════════
#  FUNCTION 1: Predict severity from text
# ═══════════════════════════════════════════════════════════════════
def predict_severity(description: str, injury_category: str = "No Injury"):
    """
    Predict whether a safety incident is High or Low severity.
    
    Args:
        description: Text describing the incident (e.g. "worker fell from scaffold")
        injury_category: One of "No Injury", "First Aid", "Medical Treatment", "Lost Time"
    
    Returns:
        dict with keys: predicted ("High" or "Not_High"), probs (dict), score (0-100)
        or None on error
    """
    try:
        bq, emb_model, pid = _get_clients()
        
        # Generate text embedding
        vector = emb_model.get_embeddings([description])[0].values
        vector_str = "[" + ", ".join(map(str, vector)) + "]"
        
        # Query BigQuery ML model
        sql = f"""
        SELECT predicted_is_high, predicted_is_high_probs
        FROM ML.PREDICT(MODEL `{pid}.{MODEL_NAME}`,
            (SELECT '{injury_category}' as injury_category,
                    {vector_str} as embedding_vector))
        """
        row = list(bq.query(sql).result())[0]
        predicted = row.predicted_is_high
        probs = {p['label']: p['prob'] for p in row.predicted_is_high_probs}
        
        return {
            "predicted": predicted,
            "probs": probs,
            "score": probs.get("High", 0) * 100,
        }
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
#  FUNCTION 2: Append a new report to BigQuery (call after form submit)
# ═══════════════════════════════════════════════════════════════════
def append_report(what_happened: str, risk_level: str, injury_category: str):
    """
    Append a single new report to the model's training data in BigQuery.
    Call this AFTER saving the form submission to your CSV.
    
    The model does NOT retrain automatically — click "Retrain" when ready.
    
    Args:
        what_happened: Text describing the incident
        risk_level: "High", "Medium", or "Low"
        injury_category: "No Injury", "First Aid", "Medical Treatment", or "Lost Time"
    
    Returns:
        True on success, False on error
    """
    try:
        bq, emb_model, pid = _get_clients()
        
        # Generate embedding
        vector = emb_model.get_embeddings([what_happened])[0].values
        
        # Append to BigQuery table
        new_row = pd.DataFrame({
            'risk_level': [risk_level],
            'injury_category': [injury_category],
            'embedding_vector': [vector],
        })
        
        table_id = f"{pid}.{EMBEDDINGS_TABLE}"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
        )
        bq.load_table_from_dataframe(new_row, table_id, job_config=job_config).result()
        return True
        
    except Exception as e:
        st.error(f"Append error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
#  FUNCTION 3: Retrain the model from all data in BigQuery
# ═══════════════════════════════════════════════════════════════════
def retrain_model():
    """
    Retrain the model using ALL data currently in BigQuery
    (original 196 rows + any new rows appended via append_report).
    
    Returns:
        dict with recall, precision, f1, row_count — or None on error
    """
    try:
        bq, _, pid = _get_clients()
        
        # Count rows
        count = list(bq.query(
            f"SELECT COUNT(*) as n FROM `{pid}.{EMBEDDINGS_TABLE}`"
        ).result())[0].n
        
        # Retrain
        sql = f"""
        CREATE OR REPLACE MODEL `{pid}.{MODEL_NAME}`
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
        FROM `{pid}.{EMBEDDINGS_TABLE}`;
        """
        bq.query(sql).result()
        
        # Evaluate
        r = list(bq.query(
            f"SELECT * FROM ML.EVALUATE(MODEL `{pid}.{MODEL_NAME}`)"
        ).result())[0]
        
        return {
            "recall": r.recall,
            "precision": r.precision,
            "f1": r.f1_score,
            "row_count": count,
        }
    except Exception as e:
        st.error(f"Retrain error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
#  THE TAB UI — call render_severity_tab() inside a st.tab
# ═══════════════════════════════════════════════════════════════════
def render_severity_tab():
    """Render the complete severity prediction tab. Call inside a st.tabs block."""
    
    st.markdown("### Severity Prediction")
    st.markdown("Enter a safety incident description to predict if it's **High** or **Low** severity.")
    
    # ── Injury selector ──
    injury_input = st.selectbox("Injury Category", [
        "No Injury", "First Aid", "Medical Treatment", "Lost Time"
    ], index=0, key="sev_injury")
    
    # ── Text input ──
    desc_input = st.text_area(
        "Incident Description", height=150,
        placeholder="Describe the incident...",
        key="sev_desc"
    )
    
    # ── Analyze button ──
    if st.button("Analyze", type="primary", key="sev_analyze"):
        if not desc_input.strip():
            st.warning("Please enter a description.")
        else:
            with st.spinner("Analyzing..."):
                result = predict_severity(desc_input, injury_input)
            
            if result:
                st.divider()
                if result["predicted"] == "High":
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
    
    # ── Retrain section ──
    st.divider()
    with st.expander("🔄 Retrain Model"):
        st.caption(
            "Click below to retrain the model using all data in BigQuery "
            "(original training data + any new reports submitted via forms)."
        )
        if st.button("🚀 Retrain Model", key="sev_retrain"):
            with st.spinner("Retraining model... this takes ~2–3 minutes."):
                metrics = retrain_model()
            if metrics:
                st.success(f"✅ Model retrained on **{metrics['row_count']}** reports!")
                col1, col2, col3 = st.columns(3)
                col1.metric("Recall", f"{metrics['recall']:.2f}")
                col2.metric("Precision", f"{metrics['precision']:.2f}")
                col3.metric("F1 Score", f"{metrics['f1']:.2f}")
