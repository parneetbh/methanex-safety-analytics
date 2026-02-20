import streamlit as st
import base64
import pandas as pd
from pathlib import Path

# ─── Page Config ───
st.set_page_config(
    page_title="Methanex Safety Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Logo helper ───
def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return None

logo_b64 = get_logo_base64() or ""

# ─── Data for sidebar metrics ───
DATA_DIR = Path(__file__).parent
REPORTS_PATH = DATA_DIR / "base_reports.xlsx"
ACTIONS_PATH = DATA_DIR / "actions.xlsx"

total_incidents = 0
total_actions = 0
total_locations = 0
if REPORTS_PATH.exists():
    base = pd.read_excel(REPORTS_PATH)
    total_incidents = len(base)
    total_locations = base["location"].nunique() if "location" in base.columns else 0
if ACTIONS_PATH.exists():
    actions = pd.read_excel(ACTIONS_PATH)
    total_actions = len(actions)

# ─── Global CSS ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* Hide defaults */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    .block-container {{ padding-top: 1.5rem !important; }}

    /* ── Clean Light Sidebar ── */
    [data-testid="stSidebar"] {{
        background: #f8f9fb;
        border-right: 1px solid #eaedf2;
        width: 240px !important;
        min-width: 240px !important;
    }}
    [data-testid="stSidebar"][aria-expanded="true"] {{
        min-width: 240px !important;
        max-width: 240px !important;
    }}

    /* Force logo above nav via ::before */
    [data-testid="stSidebar"] [data-testid="stSidebarContent"]::before {{
        content: "";
        display: block;
        background-image: url("data:image/png;base64,{logo_b64}");
        background-repeat: no-repeat;
        background-size: contain;
        background-position: center;
        height: 48px;
        margin: 20px auto 16px auto;
        width: calc(100% - 40px);
    }}

    /* Sidebar nav items */
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
        padding-top: 0.5rem;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span {{
        color: #4a5568 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover span {{
        color: #1a202c !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] span {{
        color: #1a202c !important;
        font-weight: 600 !important;
    }}

    /* Sidebar custom sections */
    [data-testid="stSidebar"] .sidebar-section-label {{
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #a0aec0;
        padding: 14px 20px 6px 20px;
    }}
    [data-testid="stSidebar"] .sidebar-metrics {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 8px 20px 12px 20px;
    }}
    [data-testid="stSidebar"] .sidebar-metric {{
        background: #ffffff;
        border-radius: 8px;
        padding: 10px 14px;
        border: 1px solid #e8ecf1;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    [data-testid="stSidebar"] .sidebar-metric .metric-value {{
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0;
        line-height: 1;
        order: 2;
    }}
    [data-testid="stSidebar"] .sidebar-metric .metric-label {{
        font-size: 0.7rem;
        color: #718096;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        order: 1;
    }}
    [data-testid="stSidebar"] .sidebar-divider {{
        border-top: 1px solid #eaedf2;
        margin: 8px 20px;
    }}
    [data-testid="stSidebar"] .sidebar-footer {{
        padding: 16px 16px;
        font-size: 0.65rem;
        color: #a0aec0;
        text-align: center;
        margin-top: 20px;
    }}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar Content (below nav) ───
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-section-label">Dataset</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div class="sidebar-metrics">
    <div class="sidebar-metric">
        <p class="metric-value">{total_incidents}</p>
        <p class="metric-label">Incidents</p>
    </div>
    <div class="sidebar-metric">
        <p class="metric-value">{total_actions}</p>
        <p class="metric-label">Actions</p>
    </div>
    <div class="sidebar-metric">
        <p class="metric-value">{total_locations}</p>
        <p class="metric-label">Locations</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div class="sidebar-footer">
    Powered by Gemini AI & ChromaDB
</div>
""", unsafe_allow_html=True)

# ─── Page Definitions ───
home = st.Page("pages/home.py", title="Home", default=True)
safebot = st.Page("pages/safebot.py", title="SafeBot AI Assistant")
clustering = st.Page("pages/clustering.py", title="Incident Clustering")
prediction = st.Page("pages/prediction.py", title="Severity Predictor")
report = st.Page("pages/report_incident.py", title="Report Incident")

pg = st.navigation([home, safebot, clustering, prediction, report])
pg.run()
