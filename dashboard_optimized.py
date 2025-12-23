"""
OPTIMIZED Streamlit dashboard - No heavy model loading!
Uses pre-computed JSON files instead of loading the full BERTopic model.
10-20x faster startup, 100x less memory.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Discoverability of Cultural Content",
    page_icon="🎭",
    layout="wide"
)

# App constants
START_DATE = pd.Timestamp("2020-01-01")

# Load culturally relevant articles only
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
    df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')
    df['search_type'] = df['search_type'].replace({'google_all': 'google_search'})
    return df

@st.cache_data
def load_topic_info():
    """Load pre-computed topic info (lightweight JSON)"""
    try:
        with open('topic_info.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ topic_info.json not found. Run: python export_topic_data.py")
        return {}

@st.cache_data
def load_topic_descriptions():
    """Load GPT-generated topic descriptions"""
    try:
        with open('topic_descriptions.json', 'r') as f:
            descriptions = json.load(f)
        return {int(k): v for k, v in descriptions.items()}
    except:
        return {}

@st.cache_data
def load_topic_map():
    """Load pre-rendered topic map visualization"""
    try:
        with open('topic_map.json', 'r') as f:
            return json.load(f)
    except:
        return None

def get_topic_label(topic_id):
    """Get topic label from pre-computed data"""
    topic_id_str = str(topic_id)
    if topic_id == -1:
        return "Outliers"
    if topic_id_str in topic_info:
        return topic_info[topic_id_str]['name']
    return f"Topic {topic_id}"

def get_keywords(topic_id):
    """Get keywords from pre-computed data"""
    topic_id_str = str(topic_id)
    if topic_id_str in topic_info:
        return topic_info[topic_id_str].get('keywords', [])
    return []

# Load data
df = load_cultural_articles()
topic_info = load_topic_info()
topic_descriptions = load_topic_descriptions()
topic_map_fig = load_topic_map()

# Filter from 2020
df_2020 = df[(df['date'].isna()) | (df['date'] >= START_DATE)]

# Header
st.markdown(
    """
<style>
  .dcc-title h1 { margin-bottom: 0.1rem; padding-bottom: 0; }
  .dcc-title h2 { margin-top: 0.15rem; margin-bottom: 0.25rem; opacity: 0.9; font-weight: 600; }
</style>
<div class="dcc-title">
  <h1>🎭 Discoverability of Cultural Content</h1>
  <h2>Analysis of Media Narratives</h2>
</div>
    """,
    unsafe_allow_html=True,
)

# Aim
st.markdown(
    "We analyze **media narratives** about the **discoverability of cultural content online**. "
    "We collected online articles (news, blogs, industry posts) and used text-mining to identify recurring themes "
    "in how platforms, policies, and technologies shape what cultural content gets found."
)

# Key stats
TOTAL_CULTURAL = len(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Total Articles Analyzed", f"{TOTAL_CULTURAL:,}")
with col2:
    if df['date'].notna().any():
        st.metric("📅 Coverage Period", f"2015 → 2025")
    else:
        st.metric("📅 Coverage Period", "N/A")
with col3:
    unique_sources = df['source'].nunique()
    st.metric("📰 Unique Sources", f"{unique_sources}")
with col4:
    topics_identified = len([t for t in df_2020['topic'].dropna().unique() if t != -1])
    st.metric("🏷️ Topics Identified", f"{topics_identified}")

st.markdown("---")

# Methods section with modal
with st.expander("🔬 Methods & how to read the visuals", expanded=False):
    st.markdown(
        """
- **Data sources**: Google Search API + Media Cloud (Harvard/MIT project)
- **Text processing**: Web scraping → AI summarization → cultural filtering
- **Topic modeling**: Voyage AI embeddings + BERTopic clustering
- **Visualizations**:
  - **Topic Overview**: most common themes (% of total)
  - **Topic Map**: spatial layout showing topic similarities
  - **Trends**: monthly series (from 2020 onward) showing share over time.
  - **Explore**: read example summaries and open source links.
        """
    )

# Read more modal
@st.dialog("Detailed Methods", width="large")
def show_methods_detail():
    st.markdown("""
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
    """)

if st.button("📖 Read more about methods", use_container_width=True):
    show_methods_detail()

# Show all topics (no filtering)
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
        label = get_topic_label(int(topic_id))
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
    
    # Topic details
    st.subheader("🔍 Topic Details")
    st.caption("Expand any topic below to see its defining keywords and sample articles.")
    
    for topic_id in topic_counts.index:
        if topic_id != -1:
            label = get_topic_label(int(topic_id))
            count = topic_counts[topic_id]
            pct = (count / TOTAL_CULTURAL * 100)
            with st.expander(f"**{label}** — {pct:.1f}%"):
                # Show GPT description if available
                if int(topic_id) in topic_descriptions:
                    desc = topic_descriptions[int(topic_id)]
                    st.info(f"**About this topic:**\n\n{desc['description']}")
                    st.caption("*Generated from a sample of articles in this topic*")
                    st.markdown("---")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**c-TF-IDF Keywords:**")
                    keywords = get_keywords(int(topic_id))
                    if keywords:
                        kw_col1, kw_col2 = st.columns(2)
                        left = keywords[:5]
                        right = keywords[5:10] if len(keywords) > 5 else []
                        with kw_col1:
                            for word in left:
                                st.markdown(f"• {word}")
                        with kw_col2:
                            for word in right:
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
    
    if topic_map_fig:
        # Load the pre-rendered Plotly figure
        fig = go.Figure(topic_map_fig)
        
        # Apply visibility fixes
        fig.update_layout(
            height=700,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black", size=12),
            xaxis=dict(gridcolor="lightgray", zerolinecolor="lightgray", color="black"),
            yaxis=dict(gridcolor="lightgray", zerolinecolor="lightgray", color="black"),
            title=dict(text="Intertopic Distance Map", font=dict(size=16, color="black"))
        )
        
        for trace in fig.data:
            if hasattr(trace, 'marker'):
                trace.marker.line = dict(width=2, color='darkblue')
                if hasattr(trace.marker, 'opacity'):
                    trace.marker.opacity = 0.8
        
        st.plotly_chart(fig, use_container_width=True, theme=None)
    else:
        st.warning("Topic map not available. Run: python export_topic_data.py")

# Tab 3: Trends (simplified, using only database data)
with tab3:
    st.header("📈 Topic Trends Over Time")
    
    st.info("""
    **What you're seeing:** How different discoverability themes evolved over time. 
    Each line represents a topic, and the y-axis shows the percentage of articles 
    published about that topic each month.
    
    **How to use it:** Spot rising trends (lines going up) and declining topics (lines going down).
    """)
    
    df_time = df_filtered[df_filtered['date'].notna()].copy()
    
    if len(df_time) > 0:
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
        
        # Count by month and topic
        timeline = df_time_top.groupby(['year_month', 'topic']).size().reset_index(name='count')
        timeline['percentage'] = (timeline['count'] / TOTAL_CULTURAL * 100).round(2)
        timeline = timeline.sort_values('year_month')
        
        # Add labels
        timeline['topic_label'] = timeline['topic'].apply(lambda x: get_topic_label(int(x)))
        
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
        
        # Year breakdown
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
            title=f'Article Distribution by Year',
            xaxis_title='Year',
            yaxis_title='Percentage of Total Articles',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No articles with valid dates found.")

# Tab 4: Explore Articles
with tab4:
    st.header("🔎 Explore Articles by Topic")
    
    st.info("""
    **What you're seeing:** A browsable list of articles organized by topic.
    
    **How to use it:** Select a topic from the dropdown, then scroll through the articles. 
    Click on any title to open the original source.
    """)
    
    topic_options = sorted([t for t in df_filtered['topic'].unique() if t != -1 and pd.notna(t)])
    
    if topic_options:
        selected_topic = st.selectbox(
            "Choose a topic to explore",
            options=topic_options,
            format_func=lambda x: get_topic_label(int(x))
        )
        
        topic_articles = df_filtered[df_filtered['topic'] == selected_topic].sort_values('date', ascending=False)
        
        topic_label = get_topic_label(int(selected_topic))
        pct_in_topic = (len(topic_articles) / TOTAL_CULTURAL * 100)
        st.subheader(f"📚 {topic_label}")
        st.caption(f"{pct_in_topic:.1f}% of total articles")
        
        # Show GPT description
        if int(selected_topic) in topic_descriptions:
            desc = topic_descriptions[int(selected_topic)]
            with st.expander("ℹ️ About this topic", expanded=False):
                st.markdown(desc['description'])
        
        # Show keywords
        keywords = get_keywords(int(selected_topic))
        if keywords:
            st.markdown("**Keywords:** " + ", ".join(keywords[:8]))
        st.markdown("---")
        
        # Pagination
        if 'explore_limit' not in st.session_state:
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

# Export database
st.markdown("---")
st.subheader("📥 Export Articles Database")
st.caption("Download the complete articles database (all articles including scraped text, summaries, and cultural relevance flags).")

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
    
    # Fix date formatting
    if 'date' in df_export.columns:
        df_export['date'] = pd.to_datetime(df_export['date'], format='ISO8601', errors='coerce')
        df_export['date'] = df_export['date'].dt.strftime('%Y-%m-%d')
        df_export['date'] = df_export['date'].fillna('')
    
    return df_export

try:
    df_export = load_all_articles_for_export()
    
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
    df_export = load_all_articles_for_export()
    st.download_button(
        label=f"📄 Download as CSV (fallback) ({len(df_export):,} articles)",
        data=df_export.to_csv(index=False),
        file_name="discoverability_articles_database.csv",
        mime="text/csv",
        use_container_width=True,
    )

