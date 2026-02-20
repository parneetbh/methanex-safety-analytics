import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ─── Page Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .home-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #a0aec0;
        margin-bottom: 4px;
    }
    .home-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0 0 8px 0;
        line-height: 1.2;
    }
    .home-subtitle {
        font-size: 0.9rem;
        color: #718096;
        margin: 0 0 24px 0;
        line-height: 1.5;
        max-width: 640px;
    }

    /* Tool cards */
    .tool-card {
        background: #ffffff;
        border: 1px solid #e8ecf1;
        border-radius: 12px;
        padding: 24px 22px;
        height: 100%;
        transition: all 0.2s ease;
    }
    .tool-card:hover {
        border-color: #c3d0e0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        transform: translateY(-2px);
    }
    .tool-card .card-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        margin-bottom: 14px;
    }
    .tool-card .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a202c;
        margin: 0 0 6px 0;
    }
    .tool-card .card-desc {
        font-size: 0.82rem;
        color: #718096;
        line-height: 1.5;
        margin: 0;
    }

    .footer-bar {
        text-align: center; color: #a0aec0; font-size: 0.75rem;
        padding: 20px 0 5px 0; margin-top: 30px;
    }

    /* Make st.page_link buttons look clean */
    [data-testid="stPageLink"] {
        margin-top: 8px;
    }
    [data-testid="stPageLink"] a {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #4a90d9 !important;
        text-decoration: none !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───
st.markdown("""
<h1 style="font-size: 2.8rem !important; font-weight: 800 !important; color: #1a202c; margin: 0 0 8px 0; line-height: 1.2; font-family: 'Inter', sans-serif;">
    Methanex Safety Intelligence Platform
</h1>
<p class="home-subtitle">
    AI-powered safety tools built on real Methanex incident data — explore patterns,
    chat with an AI assistant, cluster incidents, predict severity, and report new events.
</p>
""", unsafe_allow_html=True)

# ─── Tool Cards (Clickable) ───
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="card-icon" style="background: #fff3e0;">📊</div>
        <p class="card-title">Safety Data Explorer</p>
        <p class="card-desc">
            Explore interactive safety data visualizations — including incident 
            trends over time and severity heatmaps by location.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="tool-card">
        <div class="card-icon" style="background: #e3f2fd;">🤖</div>
        <p class="card-title">SafeBot AI Assistant</p>
        <p class="card-desc">
            Ask questions about safety incidents in natural language. The AI 
            analyzes past reports to find related events and safety recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/safebot.py", label="Open SafeBot →")

st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

col3, col4 = st.columns(2, gap="medium")

with col3:
    st.markdown("""
    <div class="tool-card">
        <div class="card-icon" style="background: #e8f5e9;">🔬</div>
        <p class="card-title">Incident Clustering</p>
        <p class="card-desc">
            AI-powered pattern discovery for safety incidents. Automatically
            identifies key risk themes and recurring issues across all reports.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/clustering.py", label="Open Clustering →")

with col4:
    st.markdown("""
    <div class="tool-card">
        <div class="card-icon" style="background: #fff5f5;">⚡</div>
        <p class="card-title">Severity Predictor</p>
        <p class="card-desc">
            Real-time AI assessment of safety incidents to identify high-risk events. 
            Classifies incidents into High or Low severity potential.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/prediction.py", label="Open Predictor →")

st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

col5, col6 = st.columns(2, gap="medium")

with col5:
    st.markdown("""
    <div class="tool-card">
        <div class="card-icon" style="background: #fce4ec;">📝</div>
        <p class="card-title">Report Incident</p>
        <p class="card-desc">
            Log new safety incidents with detailed narratives, causal factors, and
            corrective actions for future analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/report_incident.py", label="Open Report Form →")

st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

# ─── Load data once ───
DATA_DIR = Path(__file__).parent.parent
REPORTS_XLSX = DATA_DIR / "base_reports.xlsx"

df = None
if REPORTS_XLSX.exists():
    df = pd.read_excel(REPORTS_XLSX)

# ─── Style multiselect pills ───
st.markdown("""
<style>
    span[data-baseweb="tag"] {
        background-color: #3182ce !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Incident Trends Over Time (Line Chart) ───
st.markdown('<p class="home-label" style="margin-bottom: 12px;">Safety Incident Trends Over Time with Severity Distribution</p>', unsafe_allow_html=True)

if df is not None and "date" in df.columns and "severity" in df.columns and "location" in df.columns:
    all_locations = sorted(df["location"].unique().tolist())
    selected_locations = st.multiselect(
        "Filter by Location",
        options=all_locations,
        default=all_locations,
        key="trend_location_filter",
    )

    df_filtered = df[df["location"].isin(selected_locations)] if selected_locations else df

    severity_order = ["Minor", "Near Miss", "Potentially Significant", "Serious", "Major"]
    severity_colors = {
        "Minor": "#4e79a7",
        "Near Miss": "#59a14f",
        "Potentially Significant": "#e15759",
        "Serious": "#b07aa1",
        "Major": "#f28e2b",
    }

    trend = df_filtered.groupby(["date", "severity"]).size().reset_index(name="count")
    trend = trend.rename(columns={"date": "Year"})

    fig2 = go.Figure()
    annotations = []
    for sev in severity_order:
        sev_data = trend[trend["severity"] == sev].sort_values("Year")
        if not sev_data.empty:
            fig2.add_trace(go.Scatter(
                x=sev_data["Year"],
                y=sev_data["count"],
                name=sev,
                mode="lines",
                line=dict(width=2.5, color=severity_colors.get(sev, "#4299e1")),
                hovertemplate="<b>%{x}</b><br>" + sev + ": %{y}<extra></extra>",
                showlegend=False,
            ))
            last_x = sev_data["Year"].iloc[-1]
            last_y = sev_data["count"].iloc[-1]
            annotations.append(dict(
                x=last_x,
                y=last_y,
                text=f"  {sev}",
                font=dict(size=11, color=severity_colors.get(sev, "#4299e1")),
                xanchor="left",
                yanchor="middle",
                showarrow=False,
            ))

    fig2.update_layout(
        height=420,
        margin=dict(l=0, r=140, t=10, b=0),
        xaxis_title="Year",
        yaxis_title="Number of Incidents",
        xaxis=dict(dtick=1),
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        annotations=annotations,
    )
    fig2.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

# ─── Severity Heatmap by Location ───
st.markdown('<p class="home-label" style="margin-bottom: 12px;">Severity Heatmap by Location</p>', unsafe_allow_html=True)

if df is not None and "severity" in df.columns and "location" in df.columns:
    severity_order_hm = ["Minor", "Near Miss", "Potentially Significant", "Serious", "Major"]
    existing_severities = [s for s in severity_order_hm if s in df["severity"].unique()]

    pivot = df.groupby(["location", "severity"]).size().reset_index(name="count")
    pivot_table = pivot.pivot(index="location", columns="severity", values="count").fillna(0).astype(int)
    pivot_table = pivot_table.reindex(columns=existing_severities, fill_value=0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns.tolist(),
        y=pivot_table.index.tolist(),
        colorscale="Blues",
        hovertemplate="<b>%{y}</b><br>Severity: %{x}<br>Incidents: %{z}<extra></extra>",
        colorbar=dict(title="Count"),
    ))
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_title="Severity",
        yaxis_title="",
        font=dict(family="Inter, sans-serif"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── Footer ───
st.markdown('<div class="footer-bar">Methanex Safety Analytics • Powered by Gemini AI & ChromaDB</div>', unsafe_allow_html=True)

