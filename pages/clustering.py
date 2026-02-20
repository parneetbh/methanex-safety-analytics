import re
import numpy as np
import pandas as pd
import streamlit as st
import sys
from pathlib import Path


from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .page-header {
        padding: 0 0 20px 0;
        border-bottom: 1px solid #eaedf2; margin-bottom: 24px;
    }
    .page-header .title { font-size: 1.4rem; font-weight: 700; color: #1a202c; margin: 0; }
    .page-header .subtitle { font-size: 0.85rem; color: #718096; margin: 0; }

    /* Blue primary button */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #3182ce !important;
        border-color: #3182ce !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background-color: #2b6cb0 !important;
        border-color: #2b6cb0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div>
        <p class="title">Incident Clustering Analysis</p>
        <p class="subtitle">AI-powered incident pattern discovery</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Config ───
PROJECT_ID = "methanex-safety"
REGION = "us-central1"

DATA_DIR = Path(__file__).parent.parent
REPORTS_PATH = DATA_DIR / "base_reports.xlsx"
ACTIONS_PATH = DATA_DIR / "actions.xlsx"

TEXT_COLS = [
    "title",
    "what_happened",
    "what_could_have_happened",
    "why_did_it_happen",
    "causal_factors",
    "what_went_well",
    "lessons_to_prevent",
]

BASE_REQUIRED_COLS = set(["case_id", "risk_level", "severity"]).union(TEXT_COLS)
ACTIONS_REQUIRED_COLS = set(["case_id", "action", "owner", "timing", "verification"])

K_CANDIDATES = [3, 4, 5, 6]
DEFAULT_TIE_EPS = 0.01
RANDOM_STATE = 42


# ─── Helpers ───
def clean_text(x) -> str:
    if pd.isna(x):
        return ""
    x = str(x).replace("\n", " ").replace("\r", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x

@st.cache_data
def load_data():
    if not REPORTS_PATH.exists():
        return None
    df = pd.read_excel(REPORTS_PATH)
    # Ensure text cols exist
    for col in TEXT_COLS:
        if col not in df.columns:
            df[col] = ""
    # Combine text for embedding
    df["combined_text"] = df[TEXT_COLS].fillna("").agg(" ".join, axis=1)
    return df.copy()

def build_incident_text(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in TEXT_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"base_reports is missing required text columns: {missing}")
    df = df.copy()
    df["incident_text"] = df[TEXT_COLS].apply(
        lambda r: " | ".join([clean_text(v) for v in r.values if clean_text(v)]),
        axis=1
    )
    return df


def normalize_timing(x: object) -> str:
    if pd.isna(x):
        return "Unspecified"
    s = str(x).strip().lower()
    if "immediate" in s or "right away" in s or "asap" in s:
        return "Immediate"
    if ">90" in s or "over 90" in s or "90+" in s:
        return "Long-Term"
    if "<30" in s or "0-30" in s or "30 days" in s or "< 30" in s:
        return "Short-Term"
    if "30-60" in s or "60 days" in s:
        return "Short-Term"
    if "60-90" in s or "90 days" in s:
        return "Short-Term"
    return "Other"


def pick_best_k_by_silhouette(embeddings: np.ndarray, eps: float):
    scores = {}
    for k in K_CANDIDATES:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init="auto")
        labels = km.fit_predict(embeddings)
        scores[k] = float(silhouette_score(embeddings, labels))
    best_k = max(scores, key=scores.get)
    if 4 in scores and (scores[best_k] - scores[4] <= eps):
        chosen = 4
    else:
        chosen = best_k
    return chosen, scores


def compute_cluster_matrix(base_df, actions_df, cluster_col="cluster_id"):
    risk_dist = base_df.groupby([cluster_col, "risk_level"]).size().unstack(fill_value=0)
    risk_pct = (risk_dist.div(risk_dist.sum(axis=1), axis=0) * 100).round(1)
    high_risk = risk_pct.get("High", pd.Series(0, index=risk_pct.index))

    sev_dist = base_df.groupby([cluster_col, "severity"]).size().unstack(fill_value=0)
    sev_pct = (sev_dist.div(sev_dist.sum(axis=1), axis=0) * 100).round(1)
    major = sev_pct.get("Major", pd.Series(0, index=sev_pct.index))
    serious = sev_pct.get("Serious", pd.Series(0, index=sev_pct.index))
    high_sev = (major + serious).fillna(0)

    a = actions_df.copy()
    a["timing_clean"] = a["timing"].apply(normalize_timing)
    timing_dist = a.groupby([cluster_col, "timing_clean"]).size().unstack(fill_value=0)
    timing_pct = (timing_dist.div(timing_dist.sum(axis=1), axis=0) * 100).fillna(0)
    reactivity = timing_pct.get("Immediate", pd.Series(0, index=timing_pct.index))

    n_cases = base_df.groupby(cluster_col).size()

    out = pd.DataFrame({
        "cluster_id": n_cases.index.astype(int),
        "n_cases": n_cases.values.astype(int),
        "High_Risk_%": high_risk.reindex(n_cases.index).fillna(0).values,
        "High_Severity_%": high_sev.reindex(n_cases.index).fillna(0).values,
        "Reactivity_Score": reactivity.reindex(n_cases.index).fillna(0).values,
    }).sort_values("n_cases", ascending=False)
    return out


def top_action_owners(actions_df, cluster_col="cluster_id", top_n=5):
    a = actions_df.copy()
    a["owner"] = (
        a["owner"].fillna("Unspecified").astype(str)
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )
    counts = (
        a.groupby([cluster_col, "owner"]).size()
        .reset_index(name="n_actions")
        .sort_values([cluster_col, "n_actions"], ascending=[True, False])
    )
    return counts.groupby(cluster_col).head(top_n)


# ─── Vertex AI Embeddings ───
@st.cache_data(show_spinner=False)
def embed_with_vertex_ai(texts, project_id, region, model="text-embedding-004", batch_size=16):
    from google import genai
    client = genai.Client(vertexai=True, project=project_id, location=region)
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = client.models.embed_content(model=model, contents=batch)
        vectors.extend([e.values for e in resp.embeddings])
    return np.array(vectors, dtype=np.float32)


@st.cache_data(show_spinner=False)
def generate_cluster_themes(df: pd.DataFrame, cluster_col: str, text_col: str, project_id: str, region: str):
    from google import genai
    import json
    client = genai.Client(vertexai=True, project=project_id, location=region)
    
    themes = {}
    clusters = sorted(df[cluster_col].unique())
    
    for cid in clusters:
        # Sample up to 15 incidents for better context
        sample_texts = df[df[cluster_col] == cid][text_col].sample(n=min(15, len(df)), random_state=42).tolist()
        text_blob = "\n- ".join(sample_texts)
        
        prompt = f"""
        You are a senior safety analyst. Below are incident descriptions from a specific cluster.
        Analyze them to identify the root cause pattern and key risks.

        Incidents:
        {text_blob}
        
        Task: Return a JSON object with:
        1. "title": A short, specific title (3-6 words).
        2. "summary": A list of exactly 3 short bullet points summarizing the key risk, common cause, and a recommended focus area.

        Example Output:
        {{
            "title": "Contractor LOTO Violations",
            "summary": [
                "High frequency of Lockout/Tagout violations during contractor shift changes.",
                "Root causes often involve unclear verbal communication of isolation points.",
                "Focus on digital verification and localized supervision for contractors."
            ]
        }}
        Return ONLY valid JSON.
        """
        
        try:
            # Try 2.0-flash which is used in safety_bot.py
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            data = json.loads(response.text)
            themes[cid] = data
        except Exception as e:
            # Show the actual error in the UI for debugging
            themes[cid] = {
                "title": f"Error: {str(e)[:50]}...",
                "summary": ["Could not generate summary due to an error."]
            }
            print(f"Error generating theme for cluster {cid}: {e}")
            
    return themes


# ─── Load Data ───
if not REPORTS_PATH.exists():
    st.error(f"❌ `{REPORTS_PATH.name}` not found in the project directory.")
    st.stop()
if not ACTIONS_PATH.exists():
    st.error(f"❌ `{ACTIONS_PATH.name}` not found in the project directory.")
    st.stop()

base = pd.read_excel(REPORTS_PATH)
actions = pd.read_excel(ACTIONS_PATH)

missing_base = [c for c in BASE_REQUIRED_COLS if c not in base.columns]
missing_actions = [c for c in ACTIONS_REQUIRED_COLS if c not in actions.columns]

if missing_base:
    st.error(f"base_reports is missing required columns: {missing_base}")
    st.stop()
if missing_actions:
    st.error(f"actions is missing required columns: {missing_actions}")
    st.stop()

# ─── Run Clustering ───
FIXED_K = 4

st.markdown("Click **Start Clustering** to begin. The AI will analyze incident narratives and automatically identify key risk patterns.")
run = st.button("🚀 Start Clustering", type="primary", use_container_width=True)

if not run and "clustering_done" not in st.session_state:
    st.stop()

if run:
    base_processed = build_incident_text(base)

    with st.spinner("Creating embeddings with Vertex AI..."):
        embeddings = embed_with_vertex_ai(
            texts=base_processed["incident_text"].fillna("").astype(str).tolist(),
            project_id=PROJECT_ID,
            region=REGION,
        )

    with st.spinner("Clustering incidents (k=4)..."):
        km = KMeans(n_clusters=FIXED_K, random_state=RANDOM_STATE, n_init="auto")
        base_processed["cluster_id"] = km.fit_predict(embeddings).astype(int)

    with st.spinner("Analyzing cluster themes with Gemini..."):
        themes = generate_cluster_themes(
            base_processed, "cluster_id", "incident_text", PROJECT_ID, REGION
        )

    actions_merged = actions.merge(
        base_processed[["case_id", "cluster_id"]], on="case_id", how="left"
    )

    st.session_state["clustering_done"] = True
    st.session_state["base_clustered"] = base_processed
    st.session_state["actions_clustered"] = actions_merged
    st.session_state["cluster_themes"] = themes
    st.rerun()

# ─── Display Results ───
if "clustering_done" in st.session_state:
    base_processed = st.session_state["base_clustered"]
    actions_merged = st.session_state["actions_clustered"]
    themes = st.session_state.get("cluster_themes", {})

    st.success(f"✅ Clustering complete — **{FIXED_K} clusters** identified")

    missing_clusters = int(actions_merged["cluster_id"].isna().sum())
    if missing_clusters > 0:
        st.warning(f"{missing_clusters} action rows did not match a case_id in base_reports.")

    # ─── Tabs ───
    tab_analysis, tab_matrix = st.tabs([
        "🔍 Detailed Analysis",
        "📊 Strategic Risk Matrix"
    ])

    # ── Cluster Analysis (Drill Down) ──
    with tab_analysis:
        st.subheader("Detailed Cluster Analysis")
        st.caption("Select a cluster to view its summary and top action owners.")

        # 1. Cluster Selector
        # Create a list of cluster labels
        cluster_options = sorted(base_processed["cluster_id"].unique())
        
        def format_cluster_option(cid):
            theme_data = themes.get(cid, {})
            title = theme_data.get("title", f"Cluster {cid+1}")
            return f"Cluster {cid+1}: {title}"

        selected_cluster = st.radio(
            "Select Cluster:",
            options=cluster_options,
            format_func=format_cluster_option,
            horizontal=True
        )

        st.divider()

        # 2. Layout: Summary (Left) + Action Owners (Right)
        col1, col2 = st.columns(2)

        # -- Executive Summary --
        with col1:
            theme_data = themes.get(selected_cluster, {})
            title = theme_data.get("title", "Unknown Pattern")
            summary_points = theme_data.get("summary", ["No summary available."])
            
            st.markdown(f"### Cluster {selected_cluster+1}: {title}")
            
            if summary_points:
                # First point without bullet
                st.markdown(summary_points[0])
                # Remaining points with bullets
                for point in summary_points[1:]:
                    st.markdown(f"- {point}")
                
            st.caption("Generated by Gemini 2.0 Flash based on incident patterns.")

        # -- Top Action Owners --
        with col2:
            st.markdown("<p style='text-align: center; font-weight: bold;'>Top Action Owners</p>", unsafe_allow_html=True)
            
            top_owners_df = top_action_owners(
                actions_merged.dropna(subset=["cluster_id"]),
                cluster_col="cluster_id", top_n=5
            )
            
            sub = top_owners_df[top_owners_df["cluster_id"] == selected_cluster].sort_values("n_actions", ascending=True)
            
            if not sub.empty:
                fig_bar, ax = plt.subplots(figsize=(6, 4))
                ax.barh(sub["owner"], sub["n_actions"], color="#3182ce")
                ax.set_xlabel("# Actions")
                ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
                st.pyplot(fig_bar, clear_figure=True)
            else:
                st.info("No action data available for this cluster.")

        # -- Sample Cases Expander --
        with st.expander(f"View sample cases in Cluster {selected_cluster+1}"):
            mask = base_processed["cluster_id"] == selected_cluster
            display_cols = ["case_id", "title", "risk_level", "severity"]
            available = [c for c in display_cols if c in base_processed.columns]
            st.dataframe(
                base_processed.loc[mask, available].head(20),
                use_container_width=True, hide_index=True
            )

    # ── Risk Matrix ──
    with tab_matrix:
        st.subheader("Strategic Risk Matrix")
        st.caption("Bubble chart: X = High Risk %, Y = Reactivity Score, Size = # cases, Color = High Severity %")

        matrix = compute_cluster_matrix(
            base_processed,
            actions_merged.dropna(subset=["cluster_id"]),
            cluster_col="cluster_id"
        )
        # st.dataframe(matrix, use_container_width=True, hide_index=True)

        # Reduced figsize
        fig, ax = plt.subplots(figsize=(4, 3))
        sc = ax.scatter(
            matrix["High_Risk_%"],
            matrix["Reactivity_Score"],
            s=np.maximum(matrix["n_cases"] * 8, 40), # Smaller bubbles
            c=matrix["High_Severity_%"],
            cmap="Blues",
            alpha=0.85,
            edgecolors="black",
            linewidth=0.8
        )
        for _, row in matrix.iterrows():
            ax.text(
                row["High_Risk_%"] + 0.6,
                row["Reactivity_Score"] + 0.2,
                f"C{int(row['cluster_id'])+1}",
                fontsize=7, fontweight="bold"
            )
        ax.axvline(x=float(matrix["High_Risk_%"].median()), linestyle="--", alpha=0.35)
        ax.axhline(y=float(matrix["Reactivity_Score"].median()), linestyle="--", alpha=0.35)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.set_xlabel("High Risk %", fontsize=8)
        ax.set_ylabel("Reactivity Score", fontsize=8)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.set_title("Risk Matrix", fontsize=9)
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("High Severity %", fontsize=8)
        cbar.ax.tick_params(labelsize=7) 
        st.pyplot(fig, clear_figure=True, use_container_width=False)
