# 🎭 Discoverability of Cultural Content

**Analysis of Media Narratives**

An AI-powered text mining project that analyzes how media discuss the discoverability of cultural content online — exploring themes around search engines, recommendation systems, platforms, and cultural policy.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## 📊 Features

- **Topic Modeling**: Automated identification of recurring themes using BERTopic
- **Interactive Dashboard**: Explore topics, trends, and article summaries
- **Multiple Data Sources**: Google Search API + Media Cloud
- **AI-Powered Analysis**: GPT summaries + Voyage embeddings
- **Cultural Filtering**: LLM-based relevance filtering
- **Comprehensive Export**: Download complete database as ODS

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- API Keys:
  - OpenAI API key
  - SerpAPI key
  - Voyage AI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/innovation_radar.git
cd innovation_radar

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Run the Dashboard

```bash
streamlit run dashboard.py
```

## 📁 Project Structure

```
innovation_radar/
├── dashboard.py                 # Main Streamlit dashboard
├── google_search/              
│   └── google_search.py        # Google Search data collection
├── build_unified_db.py         # Unify data sources
├── scrape_articles.py          # Web scraping with newspaper4k
├── summarize_batch_*.py        # OpenAI batch summarization
├── filter_cultural_articles.py # LLM-based cultural filtering
├── run_topic_modeling.py       # BERTopic analysis
├── generate_topic_descriptions.py # GPT topic descriptions
└── requirements.txt            # Python dependencies
```

## 🔧 Complete Workflow

1. **Data Collection**
   ```bash
   cd google_search && python google_search.py
   ```

2. **Database Integration**
   ```bash
   python build_unified_db.py
   ```

3. **Article Scraping**
   ```bash
   python scrape_articles.py
   ```

4. **AI Summarization** (Batch API)
   ```bash
   python summarize_batch_prepare.py
   python summarize_batch_submit.py
   python summarize_batch_check.py    # Check status
   python summarize_batch_process.py  # When complete
   ```

5. **Cultural Filtering**
   ```bash
   python filter_cultural_articles.py
   python check_cultural_filter_batch.py  # Check status
   ```

6. **Topic Modeling**
   ```bash
   python run_topic_modeling.py
   ```

7. **Topic Descriptions**
   ```bash
   python generate_topic_descriptions.py
   ```

8. **Launch Dashboard**
   ```bash
   streamlit run dashboard.py
   ```

## 🌐 Data Sources

- **Google Search API** (via SerpAPI) - Web-wide article discovery
- **[Media Cloud](https://www.mediacloud.org/)** - Open-source media analysis platform (Harvard/MIT)

## 🧠 Technology Stack

- **Data Collection**: SerpAPI, Media Cloud
- **Web Scraping**: newspaper4k
- **AI/ML**: 
  - OpenAI GPT (summarization, filtering, descriptions)
  - Voyage AI (embeddings: voyage-3.5-lite)
  - BERTopic (topic modeling with HDBSCAN)
- **Visualization**: Streamlit, Plotly
- **Database**: SQLite3

## 📊 Dashboard Tabs

1. **Topic Overview** - Distribution and details of identified themes
2. **Topic Map** - Visual intertopic distance map
3. **Trends** - Monthly time series analysis (2020+)
4. **Explore Articles** - Browse summaries by topic

## 🔑 Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
VOYAGE_API_KEY=...
```

## 📦 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Add secrets in dashboard settings:
   ```toml
   OPENAI_API_KEY = "sk-..."
   VOYAGE_API_KEY = "..."
   ```
5. Deploy!

**Note**: The dashboard works with pre-computed model files. For full pipeline replication, run data collection scripts locally.

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Contact

For questions or collaboration: [your-email@example.com]

---

**Built with ❤️ for understanding cultural discoverability**
