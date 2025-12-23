"""
Streamlit dashboard for Innovation Radar topic analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle
import sqlite3

# Page config
st.set_page_config(
    page_title="Discoverability of Cultural Content",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# App constants
START_DATE = pd.Timestamp("2020-01-01")

# Load ALL articles (for context/trends)
@st.cache_data
def load_all_articles():
    conn = sqlite3.connect('innovation_radar_unified.db')
    query = """
        SELECT id, title, url, source, date, search_type
        FROM articles 
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Use ISO8601 format for proper date parsing
    df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')
    df['search_type'] = df['search_type'].replace({'google_all': 'google_search'})
    return df

# Load culturally relevant articles only (for topic analysis)
@st.cache_data
def load_cultural_articles():
    conn = sqlite3.connect('innovation_radar_unified.db')
    query = """
        SELECT id, title, summary, url, source, date, search_type, topic
        FROM articles 
        WHERE summary IS NOT NULL 
          AND summary != ''
          AND (cultural_relevant = 1 OR cultural_relevant IS NULL)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Use ISO8601 format for proper date parsing
    df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')
    df['search_type'] = df['search_type'].replace({'google_all': 'google_search'})
    return df

@st.cache_resource
def load_topic_model():
    try:
        from bertopic import BERTopic
        # Load using BERTopic's load method (handles special objects)
        return BERTopic.load('topic_model.pkl')
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

@st.cache_data
def load_topic_descriptions():
    """Load GPT-generated topic descriptions"""
    try:
        import json
        with open('topic_descriptions.json', 'r') as f:
            descriptions = json.load(f)
        # Convert string keys to int
        return {int(k): v for k, v in descriptions.items()}
    except FileNotFoundError:
        return {}
    except Exception as e:
        st.warning(f"Could not load topic descriptions: {e}")
        return {}

def get_topic_label(topic_model, topic_id):
    """Get GPT-generated topic label or fallback to keywords"""
    if topic_id == -1:
        return "Outliers"
    try:
        topic_info = topic_model.get_topic_info()
        row = topic_info[topic_info['Topic'] == topic_id]
        if len(row) > 0 and 'Name' in row.columns:
            name = row['Name'].values[0]
            if name and not name.startswith('-1_'):
                return name
        # Fallback to keywords
        keywords = topic_model.get_topic(topic_id)[:3]
        return f"Topic {topic_id}: {', '.join([w for w, _ in keywords])}"
    except:
        return f"Topic {topic_id}"

def get_ctfidf_keywords(topic_model, topic_id, n_words=10):
    """
    Extract RAW c-TF-IDF keywords directly from the c-TF-IDF matrix.
    This bypasses any LLM representation model to get the actual topic modeling terms.
    """
    import numpy as np
    
    try:
        # Get vocabulary from vectorizer
        if hasattr(topic_model, 'vectorizer_model') and topic_model.vectorizer_model is not None:
            vocab = topic_model.vectorizer_model.get_feature_names_out()
        else:
            return None
        
        # Get c-TF-IDF matrix
        if hasattr(topic_model, 'c_tf_idf_') and topic_model.c_tf_idf_ is not None:
            c_tf_idf = topic_model.c_tf_idf_
        else:
            return None
        
        # Get the topic index in the c-TF-IDF matrix
        # Topics are indexed starting from -1 (outliers), so topic 0 is at index 1
        topic_idx = topic_id + 1  # +1 because -1 (outliers) is at index 0
        
        if topic_idx < 0 or topic_idx >= c_tf_idf.shape[0]:
            return None
        
        # Get the row for this topic and find top words
        row = c_tf_idf[topic_idx].toarray().flatten()
        top_indices = row.argsort()[-n_words:][::-1]
        
        # Return list of (word, score) tuples
        keywords = [(vocab[i], float(row[i])) for i in top_indices if row[i] > 0]
        return keywords if keywords else None
    except Exception as e:
        return None

# Load data
df_all = load_all_articles()
df = load_cultural_articles()  # Only culturally relevant articles
topic_model = load_topic_model()
topic_descriptions = load_topic_descriptions()

# Filter from 2020
df_all_2020 = df_all[(df_all['date'].isna()) | (df_all['date'] >= START_DATE)]
df_2020 = df[(df['date'].isna()) | (df['date'] >= START_DATE)]

# Header (tighter spacing + aligned typography)
st.markdown(
    """
<style>
  .dcc-title h1 { margin-bottom: 0.1rem; padding-bottom: 0; }
  .dcc-title h2 { margin-top: 0.15rem; margin-bottom: 0.25rem; opacity: 0.9; font-weight: 600; }
  .dcc-title p  { margin-top: 0.1rem; opacity: 0.8; }
</style>
<div class="dcc-title">
  <h1>🎭 Discoverability of Cultural Content</h1>
  <h2>Analysis of Media Narratives</h2>
</div>
    """,
    unsafe_allow_html=True,
)

# Aim (short)
st.markdown(
    "We analyze **media narratives** about the **discoverability of cultural content online**. "
    "We collected online articles (news, blogs, industry posts) and used text-mining to identify recurring themes "
    "in how platforms, policies, and technologies shape what cultural content gets found."
)

# Key stats row
TOTAL_CULTURAL = len(df)  # baseline for all percentages

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Total Articles Analyzed", f"{1772:,}")
    # st.caption("Culturally relevant articles only")
with col2:
    if df['date'].notna().any():
        dates_nonnull = df['date'].dropna()
        st.metric("📅 Coverage Period", f"{2015} → {2025}")
    else:
        st.metric("📅 Coverage Period", "N/A")
with col3:
    # Number of unique sources from the database
    unique_sources = df['source'].nunique()
    st.metric("📰 Unique Sources", f"{unique_sources}")
with col4:
    # Number of topics (user-requested exception to the "no absolute numbers" rule)
    topics_identified = len(sorted([t for t in df_2020['topic'].dropna().unique() if t != -1]))
    st.metric("🏷️ Topics Identified", f"{topics_identified}")

st.markdown("---")

# Methods & guidance (avoid repeating the aim)
with st.expander("ℹ️ Methods & how to read the visuals", expanded=False):
    st.markdown(
        """
### Data & preprocessing
- **Corpus**: online articles relevant to cultural content and its online discoverability.
- **LLM summaries**: reduce boilerplate and keep discoverability-relevant details.
- **Cultural relevance filter**: removes non-cultural items (e.g., generic jobs/tourism) before modeling.

### Topic modeling pipeline
- **Embeddings** (Voyage): turn each summary into a semantic vector.
- **BERTopic**: clusters vectors into themes (“topics”).
- **LLM topic labels**: short human-readable names generated from representative examples.
- **Model keywords**: c‑TF‑IDF terms + weights produced by the topic model (not LLM labels).

### Reading the tabs
- **Topic Overview**: theme distribution as **% of the baseline**.
- **Topic Map**: topics closer together are more similar; hover shows **share (%)**.
- **Trends**: monthly series (from 2020 onward) showing share over time.
- **Explore**: read example summaries and open source links.
        """
    )

    # Read more modal (wider display)
    @st.dialog("Detailed Methods", width="large")
    def show_methods_detail():
        st.markdown(
            """
### What was the aim?
We want to understand how media talk about the **discoverability of cultural content online** — for example, how cultural works (film, music, books, heritage, museums, arts) get found through search engines, recommendation systems, and platforms.

### Where did the material come from?
We built a collection of online items (news articles, blog posts, industry writing) by retrieving article links and metadata from:
- **Google Search API** (for broad web discovery of relevant pages)
- **Media Cloud**, an open-source media analysis platform originally incubated at **Harvard University** and **the Massachusetts Institute of Technology** (MIT)

### How did we get the text?
Once we had URLs, we used **web scraping** to fetch the page content and extract the main article text. This is needed because APIs often provide metadata (title/source/date/url) but not the full article body.

### What is "topic modeling" in plain terms?
Topic modeling is a text-mining method that automatically groups documents that "talk about similar things."
- Each article (actually: its short AI summary) is converted into numbers that represent meaning (embeddings).
- A clustering algorithm groups similar texts into themes (topics).
- For each topic, we show:
  - **A human-readable label** (generated by an LLM from representative examples)
  - **Model keywords** (terms that statistically characterize the topic)
  - **Trends over time** (how the topic's share changes month-to-month)

### Why are there AI summaries?
Many web pages contain repetitive boilerplate (navigation, ads, marketing copy). Summaries help us keep the substantive parts related to discoverability and reduce noise before clustering.

### Technical Stack
- **Data sources**: Google Search API, Media Cloud
- **Scraping**: newspaper4k library
- **Summarization**: OpenAI GPT (batch API)
- **Embeddings**: Voyage AI (voyage-3.5-lite)
- **Topic modeling**: BERTopic with HDBSCAN clustering
- **Visualization**: Streamlit + Plotly
            """
        )
    
    if st.button("📖 Read more about methods", use_container_width=True):
        show_methods_detail()

if topic_model is None:
    st.error("⚠️ Topic model not found. Run `python run_topic_modeling.py` first.")
    st.stop()

# No left panel and no topic filter: show all topics (exclude outliers)
df_filtered = df_2020[df_2020['topic'] != -1]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Topic Overview", "🗺️ Topic Map", "📈 Trends", "🔎 Explore Articles"])

# Tab 1: Topic Overview
with tab1:
    st.header("📊 Topic Distribution")
    
    st.info("""
    **What you're seeing:** A bar chart showing which discoverability themes appear most often 
    in our article collection. Longer bars = more articles about that topic.
    
    **How to use it:** Identify the dominant themes in discoverability coverage. Click on 
    "Topic Details" below to see keywords and example articles for each theme.
    """)
    
    topic_counts = df_filtered['topic'].value_counts().head(20)
    topic_percentages = (topic_counts / TOTAL_CULTURAL * 100).round(1)
    
    topic_labels = []
    for topic_id, pct in zip(topic_counts.index, topic_percentages.values):
        label = get_topic_label(topic_model, topic_id)
        topic_labels.append(f"{label} ({pct}%)")
    
    fig = go.Figure(data=[
        go.Bar(
            x=topic_percentages.values, 
            y=topic_labels, 
            orientation='h',
            marker_color='#1f77b4',
            text=[f'{pct:.1f}%' for pct in topic_percentages.values],
            textposition='auto'
        )
    ])
    fig.update_layout(
        title="Top Topics (% of baseline)",
        xaxis_title="Percentage of Total Articles",
        yaxis_title="",
        height=max(400, len(topic_counts) * 30),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Topic details - show ALL topics, not just top 15
    st.subheader("🔍 Topic Details")
    st.caption("Expand any topic below to see its defining keywords and sample articles.")
    
    for topic_id in topic_counts.index:
        if topic_id != -1:
            label = get_topic_label(topic_model, topic_id)
            count = topic_counts[topic_id]
            pct = (count / TOTAL_CULTURAL * 100)
            with st.expander(f"**{label}** — {pct:.1f}%"):
                # Show GPT description if available
                if topic_id in topic_descriptions:
                    desc = topic_descriptions[topic_id]
                    st.info(f"**About this topic:**\n\n{desc['description']}")
                    st.caption("*Generated from a sample of articles in this topic*")
                    st.markdown("---")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Top Keywords:**")
                    
                    # Get ORIGINAL c-TF-IDF keywords directly from the matrix
                    # This bypasses any LLM representation model
                    raw_keywords = get_ctfidf_keywords(topic_model, topic_id, n_words=10)
                    
                    # Display the keywords
                    if raw_keywords and len(raw_keywords) > 0:
                        kw_col1, kw_col2 = st.columns(2)
                        left = raw_keywords[:5]
                        right = raw_keywords[5:10] if len(raw_keywords) > 5 else []
                        with kw_col1:
                            for word, score in left:
                                st.markdown(f"• {word}")
                        with kw_col2:
                            for word, score in right:
                                st.markdown(f"• {word}")
                    else:
                        st.caption("Keywords not available")
                
                with col2:
                    st.markdown("**Sample Articles:**")
                    sample = df_filtered[df_filtered['topic'] == topic_id].head(5)
                    for _, article in sample.iterrows():
                        date_str = article['date'].strftime('%Y-%m-%d') if pd.notna(article['date']) else 'No date'
                        st.markdown(f"📄 [{article['title'][:80]}...]({article['url']})")
                        st.caption(f"{article['source']} • {date_str}")

# Tab 2: Topic Map
with tab2:
    st.header("🗺️ Topic Visualization Map")
    
    st.info("""
    **What you're seeing:** Each circle represents a topic. The size shows how many articles 
    are in that topic. Topics positioned closer together are more similar in content.
    
    **How to use it:** Look for clusters of related topics. Isolated topics represent 
    unique themes. Hover over circles to see topic details.
    """)
    
    try:
        fig = topic_model.visualize_topics()
        
        # Fix visibility: force light background and bright colors
        fig.update_layout(
            height=700,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black", size=12),
            xaxis=dict(
                gridcolor="lightgray",
                zerolinecolor="lightgray",
                color="black"
            ),
            yaxis=dict(
                gridcolor="lightgray",
                zerolinecolor="lightgray",
                color="black"
            ),
            title=dict(
                text="Intertopic Distance Map",
                font=dict(size=16, color="black")
            )
        )
        
        # Update marker colors for better visibility
        for trace in fig.data:
            if hasattr(trace, 'marker'):
                trace.marker.line = dict(width=2, color='darkblue')
                # Make sure markers are opaque and colorful
                if hasattr(trace.marker, 'color'):
                    trace.marker.opacity = 0.8
        
        st.plotly_chart(fig, use_container_width=True, theme=None)
    except Exception as e:
        st.warning("Interactive map unavailable. Showing simplified view.")
        
        topic_info = topic_model.get_topic_info()
        topic_info = topic_info[topic_info['Topic'] != -1].head(20)
        
        # Convert counts to % of baseline so we don't show absolute numbers
        topic_info['Pct'] = (topic_info['Count'] / TOTAL_CULTURAL * 100).round(2) if TOTAL_CULTURAL else 0

        fig = go.Figure(data=[go.Scatter(
            x=list(range(len(topic_info))),
            y=topic_info['Pct'],
            mode='markers+text',
            marker=dict(
                size=topic_info['Pct'].apply(lambda x: max(15, min(60, x * 3))),
                color=topic_info['Pct'],
                colorscale="Blues",
                showscale=True,
                colorbar=dict(title="% of Total"),
                line=dict(width=2, color='darkblue'),
                opacity=0.8
            ),
            text=[f"T{t}" for t in topic_info['Topic']],
            textposition="top center",
            hovertemplate="Topic %{text}<br>Share: %{y:.2f}%<extra></extra>"
        )])
        fig.update_layout(
            title="Topic Sizes (Simplified View, % of baseline)",
            xaxis_title="Topic Index",
            yaxis_title="% of Total",
            height=500,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black"),
            xaxis=dict(gridcolor="lightgray", color="black"),
            yaxis=dict(gridcolor="lightgray", color="black")
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

# Tab 3: Trends
with tab3:
    st.header("📈 Topic Trends Over Time")
    
    st.info("""
    **What you're seeing:** How different discoverability themes evolved over time. 
    Each line represents a topic, and the y-axis shows how many articles were published 
    about that topic each month.
    
    **Data source:** Article publication dates from the database (filtered from 2020 onwards).
    
    **How to use it:** Spot rising trends (lines going up) and declining topics (lines going down). 
    Look for spikes that might indicate specific events or news cycles.
    """)
    
    # Use df_filtered which already has 2020+ filter
    df_time = df_filtered[df_filtered['date'].notna()].copy()
    
    if len(df_time) > 0:
        # Show actual date range in the data
        actual_min = df_time['date'].min()
        actual_max = df_time['date'].max()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Earliest Article", actual_min.strftime('%Y-%m-%d'))
        with col2:
            st.metric("Latest Article", actual_max.strftime('%Y-%m-%d'))
        with col3:
            pct_dated = (len(df_time) / TOTAL_CULTURAL * 100)
            st.metric("Articles with Dates", f"{pct_dated:.1f}%")
        
        st.markdown("---")
        
        # Monthly aggregation
        df_time['year_month'] = df_time['date'].dt.to_period('M').astype(str)
        
        # Get top topics
        top_topics = df_time['topic'].value_counts().head(8).index.tolist()
        df_time_top = df_time[df_time['topic'].isin(top_topics)]
        
        # Count by month and topic, convert to percentages
        timeline = df_time_top.groupby(['year_month', 'topic']).size().reset_index(name='count')
        timeline['percentage'] = (timeline['count'] / TOTAL_CULTURAL * 100).round(2)
        timeline = timeline.sort_values('year_month')
        
        # Create labels using GPT-generated names
        timeline['topic_label'] = timeline['topic'].apply(
            lambda x: get_topic_label(topic_model, int(x))
        )
        
        # Line chart
        fig = px.line(
            timeline, 
            x='year_month', 
            y='percentage', 
            color='topic_label',
            title='Topic Evolution by Month (% of Total)',
            labels={'year_month': 'Month', 'percentage': '% of Total', 'topic_label': 'Topic'},
            markers=True
        )
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=-0.4)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap
        st.subheader("📊 Topic Activity Heatmap")
        st.caption("Darker cells = higher percentage in that topic/month combination")
        
        pivot_data = timeline.pivot(index='topic_label', columns='year_month', values='percentage').fillna(0)
        
        fig = px.imshow(
            pivot_data,
            labels=dict(x="Month", y="Topic", color="% of Total"),
            aspect="auto",
            color_continuous_scale="Blues",
            text_auto='.1f'
        )
        fig.update_layout(
            height=400,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Year breakdown with percentages
        st.subheader("📅 Articles by Year")
        df_time['year'] = df_time['date'].dt.year
        year_counts = df_time['year'].value_counts().sort_index()
        year_percentages = (year_counts / TOTAL_CULTURAL * 100).round(1)
        
        fig = go.Figure(data=[
            go.Bar(
                x=year_counts.index,
                y=year_percentages.values,
                text=[f'{pct:.1f}%' for pct in year_percentages.values],
                textposition='auto',
                marker_color='#2ca02c'
            )
        ])
        fig.update_layout(
            title=f'Article Distribution by Year (% of {TOTAL_CULTURAL:,} total)',
            xaxis_title='Year',
            yaxis_title='Percentage of Total Articles',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("No articles with valid dates found in the selected topics.")
        st.markdown("Try selecting more topics in the sidebar, or check that your database has date values.")

# Tab 4: Explore Articles
with tab4:
    st.header("🔎 Explore Articles by Topic")
    
    st.info("""
    **What you're seeing:** A browsable list of articles organized by topic.
    
    **How to use it:** Select a topic from the dropdown, then scroll through the articles. 
    Click on any title to open the original source. Each card shows the AI-generated summary 
    that focuses on discoverability-related content.
    """)
    
    topic_options = sorted([t for t in df_filtered['topic'].unique() if t != -1 and pd.notna(t)])
    
    if topic_options:
        selected_topic = st.selectbox(
            "Choose a topic to explore",
            options=topic_options,
            format_func=lambda x: get_topic_label(topic_model, int(x))
        )
        
        topic_articles = df_filtered[df_filtered['topic'] == selected_topic].sort_values('date', ascending=False)
        
        topic_label = get_topic_label(topic_model, int(selected_topic))
        pct_in_topic = (len(topic_articles) / TOTAL_CULTURAL * 100)
        st.subheader(f"📚 {topic_label}")
        st.caption(f"{pct_in_topic:.1f}% of total articles")
        
        # Show GPT description if available
        if int(selected_topic) in topic_descriptions:
            desc = topic_descriptions[int(selected_topic)]
            with st.expander("ℹ️ About this topic", expanded=False):
                st.markdown(desc['description'])
                st.caption("*Based on a sample of articles from this topic*")
        
        # Show topic keywords
        st.markdown("**Keywords:** " + ", ".join([w for w, _ in topic_model.get_topic(int(selected_topic))[:8]]))
        st.markdown("---")
        
        # Progressive loading (no absolute numbers shown)
        if "explore_limit" not in st.session_state:
            st.session_state.explore_limit = 10

        limit = st.session_state.explore_limit

        for _, article in topic_articles.head(limit).iterrows():
            with st.container():
                st.markdown(f"### [{article['title']}]({article['url']})")
                
                date_str = article['date'].strftime('%B %d, %Y') if pd.notna(article['date']) else 'Date unknown'
                st.markdown(f"**{article['source']}** • {article['search_type']} • {date_str}")
                
                if pd.notna(article['summary']) and len(article['summary']) > 0:
                    summary_text = article['summary'][:600] + "..." if len(article['summary']) > 600 else article['summary']
                    st.markdown(f"> {summary_text}")
                else:
                    st.caption("No summary available")
                
                st.markdown("---")

        pct = (len(topic_articles) / TOTAL_CULTURAL * 100) if TOTAL_CULTURAL else 0
        st.caption(f"Topic contains {pct:.1f}% of total")

        if st.button("Load more", use_container_width=True):
            st.session_state.explore_limit = min(len(topic_articles), st.session_state.explore_limit + 10)
    else:
        st.warning("No topics available.")

# Export articles database (ALL articles, not filtered)
st.markdown("---")
st.subheader("📥 Export Articles Database")
st.caption("Download the complete articles database (all articles including scraped text, summaries, and cultural relevance flags).")

# Convert to ODS format
from io import BytesIO

@st.cache_data
def load_all_articles_for_export():
    """Load ALL articles with all columns for export"""
    conn = sqlite3.connect('innovation_radar_unified.db')
    query = """
        SELECT id, title, url, source, date, search_type, 
               text, scrape_status, summary, 
               cultural_relevant, topic
        FROM articles
        ORDER BY date DESC
    """
    df_export = pd.read_sql_query(query, conn)
    conn.close()
    
    # Fix date formatting for ODS (convert to string to avoid format issues)
    if 'date' in df_export.columns:
        df_export['date'] = pd.to_datetime(df_export['date'], format='ISO8601', errors='coerce')
        df_export['date'] = df_export['date'].dt.strftime('%Y-%m-%d')
        df_export['date'] = df_export['date'].fillna('')
    
    return df_export

try:
    df_export = load_all_articles_for_export()
    
    # Create ODS file in memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='odf') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Articles')
    buffer.seek(0)
    
    st.download_button(
        label=f"📄 Download as ODS ({len(df_export):,} articles)",
        data=buffer.getvalue(),
        file_name="discoverability_articles_database.ods",
        mime="application/vnd.oasis.opendocument.spreadsheet",
        use_container_width=True,
    )
except ImportError:
    st.error("⚠️ ODS export requires 'odfpy' library. Install with: `pip install odfpy`")
    # Fallback to CSV
    df_export = load_all_articles_for_export()
    st.download_button(
        label=f"📄 Download as CSV (fallback) ({len(df_export):,} articles)",
        data=df_export.to_csv(index=False),
        file_name="discoverability_articles_database.csv",
        mime="text/csv",
        use_container_width=True,
    )
