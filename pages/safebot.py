import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for safety_bot import
sys.path.insert(0, str(Path(__file__).parent.parent))
from safety_bot import ask_safety_assistant

# ─── Minimal Styling ───
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

    /* Welcome message */
    .welcome-msg {
        background: #f7fafc;
        border: 1px solid #eaedf2;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 16px;
        color: #2d3748;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .welcome-msg strong { color: #003a70; }

    /* Sample buttons — outlined style */
    .stButton > button {
        background: white !important;
        color: #003a70 !important;
        border: 1.5px solid #003a70 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #003a70 !important;
        color: white !important;
    }

    .footer-bar {
        text-align: center; color: #a0aec0; font-size: 0.75rem;
        padding: 8px 0 0 0; margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <div>
        <p class="title">SafeBot AI Assistant</p>
        <p class="subtitle">AI-powered safety incident analysis</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Chat State ───
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── Chat Container ───
chat_container = st.container(height=480)

with chat_container:
    if not st.session_state.messages:
        # Welcome message instead of duplicate header
        st.markdown("""
        <div class="welcome-msg">
            Hi there! I'm your <strong>AI-powered safety assistant</strong>. I've analyzed hundreds of
            Methanex safety incident reports and can help you uncover patterns, identify recurring
            causes, and find prevention strategies. Ask me anything about past incidents, hazard trends,
            or safety recommendations.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Try a sample question:**")
        sample_prompts = [
            "What are the most common causes of slip, trip, and fall incidents?",
            "Which hazard categories appear most frequently?",
            "What prevention strategies have been most effective?",
            "Key lessons learned from near-miss events?",
        ]
        cols = st.columns(2)
        for i, prompt in enumerate(sample_prompts):
            with cols[i % 2]:
                if st.button(prompt, key=f"sample_{i}", use_container_width=True):
                    st.session_state["pending_query"] = prompt
                    st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─── Chat Input ───
placeholder = "Ask a follow-up question..." if st.session_state.messages else "Ask a safety question..."
if user_input := st.chat_input(placeholder):
    st.session_state["pending_query"] = user_input

# ─── Process Query ───
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")
    st.session_state.messages.append({"role": "user", "content": query})

    with chat_container:
        with st.chat_message("user"):
            st.markdown(query)
        history = st.session_state.messages[:-1]
        with st.chat_message("assistant"):
            with st.spinner("Analyzing incidents..."):
                answer = ask_safety_assistant(query, chat_history=history)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()


