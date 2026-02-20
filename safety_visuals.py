import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- Helper: Sankey Data Prep ---
def make_sankey_data(df, col1, col2, col3):
    # Aggregation 1: Col1 -> Col2
    df_1 = df.groupby([col1, col2]).size().reset_index(name='value')
    df_1.columns = ['source', 'target', 'value']
    
    # Aggregation 2: Col2 -> Col3
    df_2 = df.groupby([col2, col3]).size().reset_index(name='value')
    df_2.columns = ['source', 'target', 'value']

    # Unique nodes
    all_nodes = list(pd.concat([df[col1], df[col2], df[col3]]).unique())
    node_map = {name: i for i, name in enumerate(all_nodes)}

    # Links
    links = []
    
    # Process Group 1
    for _, row in df_1.iterrows():
        links.append({
            'source': node_map[row['source']],
            'target': node_map[row['target']],
            'value': row['value'],
            'color': '#E0E0E0'  # Default link color
        })
        
    # Process Group 2
    for _, row in df_2.iterrows():
        links.append({
            'source': node_map[row['source']],
            'target': node_map[row['target']],
            'value': row['value'],
            'color': '#E0E0E0'
        })
        
    return all_nodes, links

# --- Visual Styling ---
COLOR_MAP = {
    # Severity
    'Major': '#D9534F',      # Red
    'Serious': '#F0AD4E',    # Orange
    'Minor': '#5BC0DE',      # Blue
    'Near Miss': '#5CB85C',  # Green
    'Potentially Significant': '#F7E752', # Yellowish
    
    # Locations & Categories (Defaults)
    'Canada': '#777777',
    'Vancouver': '#777777',
    'Rest of Canada': '#777777',
    'USA': '#777777',
}

def get_node_color(node_name):
    return COLOR_MAP.get(node_name, '#888888') # Default grey

def render_safety_dashboard():
    """
    Call this function in your existing Streamlit app to render the safety dashboard visual.
    Make sure 'cleaned_reports.csv' is in the same directory.
    """
    
    # Check for data file
    if not os.path.exists('base_reports.xlsx'):
        st.error("❌ Error: `base_reports.xlsx` not found. Please place it in the application folder.")
        return

    # Load Data
    df = pd.read_excel('base_reports.xlsx')

    st.markdown("### 🛡️ Incident Flow Analysis")
    st.caption("Interactive Decomposition (Severity → Location → Category)")

    # Generate Sankey Data
    nodes, links = make_sankey_data(df, 'severity', 'location', 'category')

    # Create Plotly Figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=[get_node_color(n) for n in nodes]
        ),
        link=dict(
            source=[l['source'] for l in links],
            target=[l['target'] for l in links],
            value=[l['value'] for l in links],
            color="#D3D3D3" # Light grey links
        )
    )])

    fig.update_layout(
        font_size=12,
        height=600,
        margin=dict(l=0, r=0, t=20, b=20)
    )

    # Display
    st.plotly_chart(fig, use_container_width=True)

    # Optional: Data Table Expander
    with st.expander("View Underlying Data"):
        st.dataframe(
            df[['date', 'severity', 'location', 'category', 'title']],
            use_container_width=True,
            hide_index=True
        )
