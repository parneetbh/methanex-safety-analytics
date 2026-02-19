import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path

# ─── Minimal Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header */
    .page-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 0 0 20px 0;
        border-bottom: 1px solid #eaedf2;
        margin-bottom: 24px;
    }
    .page-header img { height: 40px; }
    .page-header .title {
        font-size: 1.4rem; font-weight: 700; color: #1a202c; margin: 0;
    }
    .page-header .subtitle {
        font-size: 0.85rem; color: #718096; margin: 0; font-weight: 400;
    }
    .divider { color: #cbd5e0; font-size: 1.4rem; font-weight: 300; }

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

# ─── Header ───
st.markdown(f"""
<div class="page-header">
    {logo_img}
    <span class="divider">|</span>
    <div>
        <p class="title">Safety Incident & Near-Miss Dashboard</p>
        <p class="subtitle">AI-driven pattern mining & incident analytics</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tableau EDA ───
tableau_html = """
<div class='tableauPlaceholder' id='viz1771482874683' style='position: relative'>
    <noscript>
        <a href='#'>
            <img alt='Dashboard 1' src='https://public.tableau.com/static/images/ED/EDA1_17714828410200/Dashboard1/1_rss.png' style='border: none' />
        </a>
    </noscript>
    <object class='tableauViz' style='display:none;'>
        <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
        <param name='embed_code_version' value='3' />
        <param name='site_root' value='' />
        <param name='name' value='EDA1_17714828410200/Dashboard1' />
        <param name='tabs' value='no' />
        <param name='toolbar' value='yes' />
        <param name='static_image' value='https://public.tableau.com/static/images/ED/EDA1_17714828410200/Dashboard1/1.png' />
        <param name='animate_transition' value='yes' />
        <param name='display_static_image' value='yes' />
        <param name='display_spinner' value='yes' />
        <param name='display_overlay' value='yes' />
        <param name='display_count' value='yes' />
        <param name='language' value='en-US' />
        <param name='filter' value='publish=yes' />
    </object>
</div>
<script type='text/javascript'>
    var divElement = document.getElementById('viz1771482874683');
    var vizElement = divElement.getElementsByTagName('object')[0];
    vizElement.style.width='100%';
    vizElement.style.height='800px';
    var scriptElement = document.createElement('script');
    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
    vizElement.parentNode.insertBefore(scriptElement, vizElement);
</script>
"""

components.html(tableau_html, height=820, scrolling=False)

# ─── Footer ───
st.markdown('<div class="footer-bar">Methanex Safety Analytics • Powered by Gemini AI & ChromaDB</div>', unsafe_allow_html=True)
