# Imports
import vertexai
import chromadb
import streamlit as st
from google import genai
from google.oauth2 import service_account
from vertexai.preview.language_models import TextEmbeddingModel

# Load GCP credentials from Streamlit secrets (for cloud deployment)
# Falls back to default credentials when running locally
try:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
except (KeyError, FileNotFoundError):
    credentials = None  # Use default credentials locally

# Initialization
vertexai.init(
    project="methanex-safety",
    location="us-central1",
    credentials=credentials
)

embedding_model = TextEmbeddingModel.from_pretrained(
    "text-embedding-004"
)

client = genai.Client(
    vertexai=True,
    project="methanex-safety",
    location="us-central1"
)

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="safety_incidents"
)

# System prompt for the safety assistant
SYSTEM_PROMPT = """You are a safety knowledge assistant for Methanex industrial operations.
You analyze historical safety incidents, near misses, and lessons learned to help identify
patterns, understand severity drivers, and recommend prevention strategies.

RULES:
- Answer ONLY using the incident records provided below. Do not add external safety advice or assumptions.
- If the incidents do not contain enough information to answer, say so clearly.
- Do NOT reference specific incident numbers in your answer (e.g. "Incident 5"). Instead, describe incidents by their type, location, or key details.
- When identifying patterns, group by activity type, equipment, root cause, or hazard category.
- Keep answers concise and to the point — avoid lengthy quotes from incidents.

RESPONSE FORMAT — Structure your answer with these sections as relevant to the question:
1. **Direct Answer** — A concise answer to the user's question.
2. **Patterns & Recurring Themes** — Common causes, contributing factors, or trends you observe across incidents.
3. **Severity & Escalation Potential** — What could have happened; which factors are linked to higher severity.
4. **Prevention Recommendations** — Data-driven suggestions based on the lessons and corrective actions in the incidents.

At the very end of your response, always add this exact line on its own:

**Would you like to take a closer look at the related incidents?**

Keep your response clear, actionable, and grounded in the data provided."""


def ask_safety_assistant(query, chat_history=None):
    """
    Send a query to the safety assistant with optional conversation history.

    Args:
        query: The user's current question.
        chat_history: List of dicts with 'role' ('user'/'assistant') and 'content'.
    """
    if chat_history is None:
        chat_history = []

    # Retrieve ALL incidents from the collection so the model sees the full dataset
    total_docs = collection.count()
    query_embedding = embedding_model.get_embeddings(
        [query]
    )[0].values

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=total_docs
    )

    # Format context as numbered incidents for clear referencing
    context_parts = []
    for i, doc in enumerate(results["documents"][0]):
        context_parts.append(f"--- Incident {i+1} ---\n{doc}")
    context = "\n\n".join(context_parts)

    # Build multi-turn contents for Gemini
    contents = []

    # First message includes system prompt + incident context
    system_and_context = f"""{SYSTEM_PROMPT}

=== INCIDENT RECORDS ===
{context}
"""
    # Add conversation history so the model has context for follow-ups
    if chat_history:
        # Start with a system-level user message containing the prompt + incidents
        contents.append({
            "role": "user",
            "parts": [{"text": system_and_context + "\n=== USER QUESTION ===\n" + chat_history[0]["content"]}]
        })
        # Add the rest of the history
        for msg in chat_history[1:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        # Add current query
        contents.append({
            "role": "user",
            "parts": [{"text": query}]
        })
    else:
        # Single-turn: just combine everything
        contents.append({
            "role": "user",
            "parts": [{"text": system_and_context + "\n=== USER QUESTION ===\n" + query + "\n\nPlease analyze the incidents above and answer the user's question following the response format."}]
        })

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents
    )

    return response.text
