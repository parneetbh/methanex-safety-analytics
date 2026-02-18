import streamlit as st
from safety_bot import ask_safety_assistant

st.set_page_config(page_title="SafeBot")

st.title("SafeBot")

# Sample prompts for users
SAMPLE_PROMPTS = [
    "What are the most common causes of slip, trip, and fall incidents?",
    "Which types of events have the highest severity or escalation potential?",
    "What patterns exist in maintenance-related safety incidents?",
    "What are the key lessons learned from near-miss events?",
    "Which hazard categories appear most frequently across all sites?",
    "What prevention strategies have been most effective?",
]

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show sample prompts only when there's no conversation yet
if not st.session_state.messages:
    st.markdown("##### 💡 Try one of these sample questions:")
    cols = st.columns(2)
    for i, prompt in enumerate(SAMPLE_PROMPTS):
        with cols[i % 2]:
            if st.button(prompt, key=f"sample_{i}", use_container_width=True):
                st.session_state["pending_query"] = prompt
                st.rerun()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Dynamic placeholder based on conversation state
placeholder = "Ask a follow-up question..." if st.session_state.messages else "Ask a safety question..."

# Chat input
if user_input := st.chat_input(placeholder):
    st.session_state["pending_query"] = user_input

# Process any pending query (from chat input or sample button)
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Build history (everything except the message we just added)
    history = st.session_state.messages[:-1]

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing incidents..."):
            answer = ask_safety_assistant(query, chat_history=history)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
