# 🛡️ Methanex Safety Intelligence Platform
**AI-Powered Safety Incident Analysis for Industrial Operations**

This project was built during the Google Cloud Hackathon hosted by UBC Sauder School of Business. It transforms 196 unanalyzed safety incident reports from Methanex Corporation into actionable, data-driven prevention strategies using a combination of NLP, machine learning, and interactive visualization — all deployed on Google Cloud.

🔗 **Live Platform:** [safety-ai-bot-418677477535.us-central1.run.app](https://safety-ai-bot-418677477535.us-central1.run.app/)

## 📌 Objectives
- Analyze and structure real-world safety incident data for pattern discovery
- Build an AI chatbot grounded in historical incident reports using RAG
- Cluster incident narratives to surface recurring risk themes
- Predict incident severity in real time using BigQuery ML
- Provide an interactive dashboard with trend analysis and severity heatmaps
- Enable new incident reporting that feeds back into the ML pipeline

## 📊 Datasets Used
- `base_reports.xlsx` — 196 safety incident records with narratives, severity, risk level, causal factors, and lessons learned
- `actions.xlsx` — corrective actions linked to each incident, including owners, timing, and verification status

## 📈 1. Safety Data Explorer
The home dashboard provides a financial-style overview of the incident data:
- Incident trend lines over time, broken down by severity level
- Severity heatmap by location to identify high-risk sites
- Location-based filtering for focused analysis
- Summary metrics for total incidents, actions, and locations

## 🤖 2. SafeBot AI Assistant
A conversational AI assistant that lets safety teams query historical incidents using natural language.

How it works:
- Incident narratives are embedded using Vertex AI (`text-embedding-004`) and stored in ChromaDB
- User queries are embedded and matched against all incident records via semantic search
- Retrieved context is passed to Gemini 2.0 Flash with a structured system prompt
- Multi-turn conversation history is maintained for follow-up questions

The assistant identifies patterns, severity drivers, and prevention strategies — all grounded in real data.

## 🔬 3. Incident Clustering
AI-powered pattern discovery across all incident reports:
- Text from multiple narrative fields (what happened, causal factors, lessons learned, etc.) is combined and embedded via Vertex AI
- KMeans clustering groups incidents into risk themes
- Gemini generates executive summaries for each cluster, identifying root cause patterns
- A strategic risk matrix visualizes clusters by high-risk percentage, reactivity score, and severity distribution
- Top action owners are surfaced per cluster for accountability tracking

## ⚡ 4. Severity Predictor
Real-time severity classification for new incidents:
- Incident descriptions are embedded using Vertex AI text embeddings
- A logistic regression model trained in BigQuery ML classifies incidents as **High** or **Low** severity
- The model uses text embeddings combined with injury category as input features
- One-click model retraining incorporates newly submitted reports
- Evaluation metrics (recall, precision, F1) are displayed after each retrain cycle

## 📝 5. Report Incident
A structured form for logging new safety events:
- Captures detailed narratives, causal factors, and corrective actions
- New submissions are appended to BigQuery, feeding back into the severity prediction model
- Keeps the platform's data and models up to date in real time

## 🛠 Tools and Libraries
- Python
- Streamlit
- Google Cloud (Vertex AI, BigQuery ML, Cloud Run)
- Gemini 2.0 Flash
- ChromaDB
- Plotly
- scikit-learn
- matplotlib
- pandas
- numpy
