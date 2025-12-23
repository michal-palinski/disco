# Innovation Radar Dashboard Guide

## Overview

Interactive Streamlit dashboard for exploring discoverability topics identified by BERTopic.

## Features

### 📊 Tab 1: Topic Overview
- **Topic Distribution** - Bar chart showing top 20 topics by article count
- **Topic Details** - Expandable sections with:
  - Top 10 keywords per topic with relevance scores
  - Sample articles from each topic
  - Direct links to full articles

### 🗺️ Tab 2: Topic Map
- **Interactive Visualization** - Visual representation of topic relationships
- **Topic Network** - Shows topic sizes and connections
- **Cluster Analysis** - Identify related topics

### 📈 Tab 3: Trends Over Time
- **Timeline Chart** - Line chart showing topic evolution
- **Activity Heatmap** - Topic activity by month
- **Trend Analysis** - Identify emerging and declining topics

### 🔎 Tab 4: Explore Articles
- **Topic Selector** - Browse articles by specific topic
- **Article Details** - Full summaries and metadata
- **Direct Links** - Click through to original articles

## Sidebar Filters

### Date Range
- Filter articles by publication date
- Dynamic range based on available data

### Source Type
- Filter by: `google_news`, `google_all`, `media_cloud`
- Or view all sources combined

### Topic Filter
- Multi-select specific topics
- Exclude outliers (-1)
- Focus on relevant topics only

## Installation

```bash
# Install required packages
pip install bertopic streamlit plotly scikit-learn pandas

# Or install all at once
pip install -r requirements.txt
```

## Usage

### Step 1: Run Topic Modeling
```bash
python run_topic_modeling.py
```

**What it does:**
- Loads summaries from database
- Trains BERTopic model (5-10 minutes)
- Identifies topics automatically
- Saves model and assignments
- Updates database with topic IDs

**Output:**
```
Found 1,753 articles with summaries
Training BERTopic model...
✓ Model trained! Found 25 topics

Topic Distribution:
  Topic 0: discovery, platform, content, algorithm, search (245 docs)
  Topic 1: discoverability, cultural, european, content, policy (198 docs)
  Topic 2: ai, artificial, intelligence, recommendation, system (167 docs)
  ...

✓ Saved model to topic_model.pkl
✓ Saved topics data to topics_data.csv
✓ Updated database with topic assignments
```

### Step 2: Launch Dashboard
```bash
streamlit run dashboard.py
```

**Opens:** http://localhost:8501

Dashboard loads automatically with all visualizations.

## Dashboard Sections Explained

### Topic Distribution Chart
- **X-axis:** Number of articles
- **Y-axis:** Topic labels with top 3 keywords
- **Top 20 topics** shown by default
- **Interactive:** Click bars for details

### Topic Timeline
- **X-axis:** Time (by month)
- **Y-axis:** Article count
- **Colors:** Different topics
- **Shows:** Topic trends over time
- **Useful for:** Identifying seasonal patterns, emerging topics

### Heatmap
- **Rows:** Topics
- **Columns:** Months
- **Color intensity:** Article count
- **Useful for:** Spotting activity clusters

### Article Explorer
- **Select topic** from dropdown
- **Browse all articles** in that topic
- **Click titles** to read original articles
- **View summaries** inline

## Interpreting Topics

### Understanding Topic Labels
Format: `Topic ID: keyword1, keyword2, keyword3`

**Example:**
- `Topic 0: discovery, platform, content` - Platform-based content discovery
- `Topic 5: ai, recommendation, algorithm` - AI-driven recommendations

### Topic Sizes
- **Large topics (100+ docs):** Major themes
- **Medium topics (20-99 docs):** Specific sub-themes
- **Small topics (10-19 docs):** Niche areas
- **Outliers (-1):** Didn't fit any topic

### Topic Quality
- **Good topics:** Clear, distinct keywords
- **Overlapping topics:** May need model refinement
- **Generic topics:** May need more specific data

## Customization

### Adjusting Topic Model

Edit `run_topic_modeling.py`:

```python
# Change minimum topic size
topic_model = BERTopic(
    min_topic_size=15,  # Increase for larger, fewer topics
    nr_topics=20,       # Set specific number of topics
)
```

### Dashboard Styling

Edit `dashboard.py`:

```python
# Change color scheme
fig = px.line(..., color_discrete_sequence=px.colors.qualitative.Set1)

# Adjust chart height
fig.update_layout(height=800)

# Change default filters
selected_topics = st.sidebar.multiselect(..., default=topics_list[:15])
```

## Exporting Data

### From Dashboard
1. Apply desired filters
2. Click "Download Filtered Data" in sidebar
3. Downloads CSV with current view

### From Command Line
```bash
python export_to_csv.py
```
Exports all data with topic assignments.

## Troubleshooting

### "Topic model not found"
**Solution:** Run `python run_topic_modeling.py` first

### "Not enough summaries"
**Solution:** Run summarization first:
```bash
python summarize_batch_process.py
```

### Dashboard won't load
**Check:**
1. Streamlit installed: `pip install streamlit`
2. Database exists: `innovation_radar_unified.db`
3. Model exists: `topic_model.pkl`

### Slow performance
**Solutions:**
- Filter by date range
- Select fewer topics
- Reduce data size in `run_topic_modeling.py`

### Empty visualizations
**Check:**
- Summaries exist in database
- Topics were assigned (check `topics_data.csv`)
- Filters aren't too restrictive

## Best Practices

1. ✅ **Filter effectively** - Use date ranges for faster loading
2. ✅ **Explore topics incrementally** - Start with top 10 topics
3. ✅ **Use timeline for trends** - Identify emerging themes
4. ✅ **Export filtered data** - Save interesting subsets
5. ✅ **Rerun modeling periodically** - As new data arrives

## Advanced Usage

### Topic Refinement
1. Run initial model
2. Review topic quality
3. Adjust parameters
4. Rerun modeling
5. Compare results

### Time Period Analysis
1. Filter to specific date range
2. Download filtered data
3. Run separate topic model on subset
4. Compare with overall topics

### Source Comparison
1. Filter by source type
2. Note topic distribution
3. Compare across sources
4. Identify source-specific themes

## Keyboard Shortcuts

When dashboard is active:
- `R` - Rerun dashboard
- `C` - Clear cache
- `S` - Open settings

## Performance Tips

- **Large datasets (5000+ articles):** Increase `min_topic_size` to 20-30
- **Fast exploration:** Use topic filter to limit display
- **Detailed analysis:** Export subset and analyze offline
- **Memory issues:** Close other applications

## Next Steps

After exploring dashboard:
1. ✅ Identify key topics of interest
2. ✅ Track topic evolution over time
3. ✅ Export relevant article subsets
4. ✅ Update database with new articles
5. ✅ Rerun analysis monthly

## Support

For issues:
1. Check error messages in terminal
2. Verify all files exist
3. Check requirements installed
4. Review this guide

---

**Dashboard URL:** http://localhost:8501  
**Stop dashboard:** Ctrl+C in terminal

