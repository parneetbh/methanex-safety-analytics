import streamlit as st

# ─── Page Config ───
st.set_page_config(
    page_title="Methanex Safety Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS — Clean Minimal Theme ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Hide defaults */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    .block-container { padding-top: 1.5rem !important; }

    /* ── Clean Sidebar ── */
    [data-testid="stSidebar"] {
        background: #fafbfd;
        border-right: 1px solid #eaedf2;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] span {
        color: #4a5568 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover span {
        color: #003a70 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] span {
        color: #003a70 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Page Definitions ───
home = st.Page("pages/home.py", title="Home", default=True)
safebot = st.Page("pages/safebot.py", title="SafeBot AI Assistant")
report = st.Page("pages/report_incident.py", title="Report Incident")

pg = st.navigation([home, safebot, report])
pg.run()
