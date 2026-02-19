import streamlit as st
import pandas as pd
import base64
from pathlib import Path

# ─── Minimal Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .page-header {
        display: flex; align-items: center; gap: 16px;
        padding: 0 0 20px 0; border-bottom: 1px solid #eaedf2; margin-bottom: 24px;
    }
    .page-header img { height: 40px; }
    .page-header .title { font-size: 1.4rem; font-weight: 700; color: #1a202c; margin: 0; }
    .page-header .subtitle { font-size: 0.85rem; color: #718096; margin: 0; }
    .divider { color: #cbd5e0; font-size: 1.4rem; font-weight: 300; }

    .section-label {
        font-size: 0.75rem; font-weight: 600; color: #a0aec0;
        text-transform: uppercase; letter-spacing: 1px;
        margin: 24px 0 8px 0;
    }

    .stFormSubmitButton > button {
        background: #003a70 !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        padding: 12px 30px !important; font-size: 0.95rem !important;
        transition: all 0.15s ease !important;
    }
    .stFormSubmitButton > button:hover {
        background: #00507a !important;
        box-shadow: 0 4px 12px rgba(0,58,112,0.2) !important;
    }

    .success-box {
        background: #f0fdf4; border: 1px solid #86efac;
        border-radius: 10px; padding: 16px; text-align: center;
        color: #166534; font-weight: 500;
    }

    .footer-bar {
        text-align: center; color: #a0aec0; font-size: 0.8rem;
        padding: 20px 0 5px 0; border-top: 1px solid #eaedf2; margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Logo ───
def get_logo_base64():
    logo_path = Path(__file__).parent.parent / "logo.png"
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return None

logo_b64 = get_logo_base64()
logo_img = f'<img src="data:image/png;base64,{logo_b64}" alt="Methanex">' if logo_b64 else ""

st.markdown(f"""
<div class="page-header">
    {logo_img}
    <span class="divider">|</span>
    <div>
        <p class="title">Report an Incident</p>
        <p class="subtitle">File a new safety incident or near-miss report</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════
# INCIDENT REPORT FORM
# ════════════════════════════════════════════════

REPORTS_PATH = Path(__file__).parent.parent / "base_reports.xlsx"
ACTIONS_PATH = Path(__file__).parent.parent / "actions.xlsx"

# ── Dynamic action count ──
if "action_count" not in st.session_state:
    st.session_state.action_count = 3

with st.form("incident_form", clear_on_submit=True):

    # ── Incident Details ──
    st.markdown('<p class="section-label">Incident Details</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if REPORTS_PATH.exists():
            existing_df = pd.read_excel(REPORTS_PATH)
            next_num = len(existing_df) + 1
        else:
            next_num = 1
        case_id = st.text_input("Case ID", value=f"CASE-{next_num:03d}", disabled=True)
    with col2:
        title = st.text_input("Incident Title", placeholder="e.g. Unexpected Pressure Release During Sampling Line Replacement")

    col3, col4, col5 = st.columns(3)
    with col3:
        category = st.selectbox("Category", ["Safety", "Environmental", "Process", "Security", "Other"])
    with col4:
        risk_level = st.selectbox("Risk Level", ["Low", "Medium", "High", "Critical"])
    with col5:
        primary_classification = st.selectbox("Primary Classification", [
            "Health and Safety", "Process Safety", "Environmental",
            "Security", "Transportation", "Other"
        ])

    # ── Location & Timing ──
    st.markdown('<p class="section-label">Location & Timing</p>', unsafe_allow_html=True)

    col6, col7, col8 = st.columns(3)
    with col6:
        incident_date = st.text_input("Year", placeholder="e.g. 2025")
    with col7:
        location = st.selectbox("Location", [
            "Canada", "USA", "New Zealand", "Chile",
            "Trinidad", "Egypt", "Brussels", "Vancouver",
            "Working from Home", "Other"
        ])
    with col8:
        setting = st.text_input("Setting", placeholder="e.g. Chemical processing unit – general area")

    # ── Outcome ──
    st.markdown('<p class="section-label">Outcome</p>', unsafe_allow_html=True)

    col9, col10 = st.columns(2)
    with col9:
        injury_category = st.selectbox("Injury Category", [
            "No Injury", "First Aid", "Medical Treatment",
            "Restricted Work", "Lost Time", "Fatality"
        ])
    with col10:
        severity = st.selectbox("Severity", [
            "Near Miss", "Minor", "Potentially Significant",
            "Serious", "Major"
        ])

    # ── Narrative ──
    st.markdown('<p class="section-label">Narrative</p>', unsafe_allow_html=True)

    what_happened = st.text_area("What Happened", placeholder="Describe the sequence of events in detail...", height=120)
    what_could_have_happened = st.text_area("What Could Have Happened", placeholder="Potential escalation and worst-case outcomes...", height=80)

    col11, col12 = st.columns(2)
    with col11:
        why_did_it_happen = st.text_area("Why Did It Happen", placeholder="Root causes...", height=100)
    with col12:
        causal_factors = st.text_area("Causal Factors", placeholder="Contributing factors...", height=100)

    col13, col14 = st.columns(2)
    with col13:
        what_went_well = st.text_area("What Went Well", placeholder="Positive actions taken...", height=100)
    with col14:
        lessons_to_prevent = st.text_area("Lessons to Prevent Recurrence", placeholder="Recommendations...", height=100)

    # ── Corrective Actions (dynamic) ──
    st.markdown('<p class="section-label">Corrective Actions</p>', unsafe_allow_html=True)

    num_actions = st.number_input(
        "Number of actions",
        min_value=1,
        max_value=15,
        value=st.session_state.action_count,
        step=1,
        help="Add up to 15 corrective actions"
    )

    actions = []
    for i in range(num_actions):
        st.markdown(f"**Action {i+1}**")
        acol1, acol2, acol3, acol4 = st.columns([3, 1.5, 1, 1.5])
        with acol1:
            action_text = st.text_input("Description", placeholder="Describe the action", key=f"action_{i}", label_visibility="collapsed")
        with acol2:
            action_owner = st.text_input("Owner", placeholder="Role / Name", key=f"owner_{i}", label_visibility="collapsed")
        with acol3:
            action_timing = st.selectbox("Timing", ["<30 days", "30–90 days", ">90 days"], key=f"timing_{i}", label_visibility="collapsed")
        with acol4:
            action_verify = st.text_input("Verification", placeholder="How to verify", key=f"verify_{i}", label_visibility="collapsed")
        if action_text.strip():
            actions.append({
                "action_number": i + 1,
                "action": action_text,
                "owner": action_owner,
                "timing": action_timing,
                "verification": action_verify
            })

    # Column headers hint
    st.caption("Columns: Description  •  Owner  •  Timing  •  Verification method")

    # ── Submit ──
    submitted = st.form_submit_button("Submit Incident Report", use_container_width=True)

    if submitted:
        if not title.strip() or not what_happened.strip():
            st.error("Please provide at least an Incident Title and What Happened description.")
        else:
            new_report = {
                "case_id": f"CASE-{next_num:03d}",
                "title": title,
                "category": category,
                "risk_level": risk_level,
                "setting": setting,
                "date": incident_date,
                "location": location,
                "injury_category": injury_category,
                "severity": severity,
                "primary_classification": primary_classification,
                "what_happened": what_happened,
                "what_could_have_happened": what_could_have_happened,
                "why_did_it_happen": why_did_it_happen,
                "causal_factors": causal_factors,
                "what_went_well": what_went_well,
                "lessons_to_prevent": lessons_to_prevent
            }

            report_df = pd.DataFrame([new_report])
            if REPORTS_PATH.exists():
                existing = pd.read_excel(REPORTS_PATH)
                updated = pd.concat([existing, report_df], ignore_index=True)
            else:
                updated = report_df
            updated.to_excel(REPORTS_PATH, index=False)

            if actions:
                action_rows = []
                for a in actions:
                    a["case_id"] = f"CASE-{next_num:03d}"
                    action_rows.append(a)
                action_df = pd.DataFrame(action_rows)
                if ACTIONS_PATH.exists():
                    existing_actions = pd.read_excel(ACTIONS_PATH)
                    updated_actions = pd.concat([existing_actions, action_df], ignore_index=True)
                else:
                    updated_actions = action_df
                updated_actions.to_excel(ACTIONS_PATH, index=False)

            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>Incident CASE-{next_num:03d} submitted successfully!</strong><br>
                Report and {len(actions)} action(s) saved.
            </div>
            """, unsafe_allow_html=True)
            st.balloons()

# ─── Recent Reports ───
if REPORTS_PATH.exists():
    st.markdown("---")
    st.markdown("#### Recent Incident Reports")
    df = pd.read_excel(REPORTS_PATH)
    display_cols = ["case_id", "title", "category", "risk_level", "location", "severity", "date"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols].tail(10).iloc[::-1], use_container_width=True, hide_index=True)

st.markdown('<div class="footer-bar">Methanex Safety Analytics • Powered by Gemini AI & ChromaDB</div>', unsafe_allow_html=True)
