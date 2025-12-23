# Innovation Radar - Complete Workflow

## Overview
Complete pipeline for analyzing discoverability topics in media coverage with AI-powered filtering, topic modeling, and visualization.

---

## 📋 Complete Workflow

### Step 1: Build Database
```bash
python build_unified_db.py
```
**Output:** `innovation_radar_unified.db` with ~2,600 articles from Google Search + Media Cloud

---

### Step 2: Scrape Article Text (Optional)
```bash
python scrape_articles.py
```
**Time:** 20-30 minutes  
**Output:** Adds full text to articles (uses newspaper4k)

---

### Step 3: Summarize Articles (Batch API)
```bash
# 3a. Prepare batch
python summarize_batch_prepare.py

# 3b. Submit to OpenAI
python summarize_batch_submit.py

# 3c. Check status (wait 2-6 hours)
python summarize_batch_check.py

# 3d. Process results when complete
python summarize_batch_process.py
```
**Cost:** ~$2.50-5 (50% discount)  
**Output:** AI summaries focusing on discoverability content

---

### Step 4: Filter Cultural Relevance ⭐ NEW
```bash
python filter_cultural_articles.py
```
**What it does:**
- Uses GPT to check if each article relates to culture/creative industries
- Drops articles about general tourism, job market, etc.
- Marks articles as `cultural_relevant=1` or `0`

**Cost:** ~$0.50-1 for 2,000 articles  
**Output:** Filtered dataset for topic modeling

---

### Step 5: Topic Modeling with Voyage + GPT
```bash
python run_topic_modeling.py
```
**What it does:**
- Uses **Voyage AI** embeddings (voyage-3.5-lite)
- Uses **GPT** for topic labels  
- Only processes culturally relevant articles
- **⭐ NEW:** Suggests topic merges using GPT

**Cost:** ~$0.15-0.25  
**Time:** 5-10 minutes  
**Output:**
- `topic_model.pkl` - BERTopic model
- `embeddings.npy` - Cached embeddings
- `topics_data.csv` - Topic assignments
- `topic_merge_suggestions.txt` - GPT analysis of which topics to merge

---

### Step 6: Generate Topic Descriptions
```bash
python generate_topic_descriptions.py
```
**What it does:**
- Reads 30 random articles from each topic
- Uses GPT to generate 2-3 paragraph descriptions

**Cost:** ~$0.50-1  
**Output:** `topic_descriptions.json`

---

### Step 7: Launch Dashboard
```bash
streamlit run dashboard.py
```
**Opens:** http://localhost:8501

**Features:**
- Topic distribution charts
- GPT-generated topic labels & descriptions
- Timeline trends (2020+)
- Interactive article explorer

---

## 💰 Total Cost Estimate

| Step | Cost | Required |
|------|------|----------|
| Scraping | Free | Optional |
| Summarization (Batch) | $2.50-5 | Yes |
| Cultural Filtering | $0.50-1 | Recommended |
| Topic Modeling | $0.15-0.25 | Yes |
| Topic Descriptions | $0.50-1 | Optional |
| **Total** | **$3.65-7.25** | |

---

## 🔑 API Keys Required

Create `.env` file:
```
OPENAI_API_KEY=your_key_here
VOYAGE_API_KEY=your_key_here
```

Get keys at:
- OpenAI: https://platform.openai.com/api-keys
- Voyage: https://www.voyageai.com/

---

## 📊 Model Names

**Note:** User specified "gpt-5-mini" and "gpt-5.2" which don't exist yet.

**Current OpenAI models:**
- `gpt-4o-mini` (recommended, fast & cheap)
- `gpt-4o` (more powerful, 2x cost)
- `gpt-4-turbo`

**To update model names:**
1. Edit scripts: replace "gpt-5-mini" with "gpt-4o-mini"
2. Or wait for GPT-5 release

---

## 🎯 Key Files

### Scripts
- `filter_cultural_articles.py` ⭐ NEW - Pre-filter for culture
- `run_topic_modeling.py` - Main topic modeling (updated with merge suggestions)
- `generate_topic_descriptions.py` - Create descriptions
- `dashboard.py` - Streamlit visualization

### Data
- `innovation_radar_unified.db` - Main SQLite database
- `topic_model.pkl` - BERTopic model
- `embeddings.npy` - Cached Voyage embeddings
- `topic_descriptions.json` - GPT descriptions
- `topic_merge_suggestions.txt` ⭐ NEW - Merge recommendations

---

## 🔄 Rerunning After Updates

**After adding more articles:**
```bash
python build_unified_db.py
python summarize_batch_prepare.py  # Then submit/process
python filter_cultural_articles.py  # Filter new articles
python run_topic_modeling.py        # Retrain model
python generate_topic_descriptions.py  # Regenerate descriptions
streamlit run dashboard.py --clear-cache
```

**To use cached embeddings:**
- Keep `embeddings.npy` file
- Model will load embeddings instead of regenerating

---

## 🐛 Troubleshooting

### "gpt-5-mini not found"
→ Change to "gpt-4o-mini" in scripts

### "Voyage API error"
→ Check VOYAGE_API_KEY in `.env`

### "No embeddings.npy"
→ First run generates it, subsequent runs use cache

### "Pickle error"
→ Model now uses BERTopic.save/load (fixed)

### Dashboard shows few articles
→ Run with `--clear-cache` flag

---

## 📈 Dashboard Features

1. **Topic Overview** - Bar charts + GPT descriptions
2. **Topic Map** - Visual clustering
3. **Trends** - Timeline from 2020+ (fixed date parsing)
4. **Explore** - Browse articles by topic

All topics now show:
- GPT-generated labels
- Detailed descriptions (from 30 articles)
- Keywords
- Sample articles

---

## ⚡ Quick Reference

```bash
# Complete pipeline
python build_unified_db.py
python summarize_batch_prepare.py && python summarize_batch_submit.py
# Wait for batch...
python summarize_batch_process.py
python filter_cultural_articles.py
python run_topic_modeling.py
python generate_topic_descriptions.py
streamlit run dashboard.py
```

**Total time:** ~4-8 hours (mostly waiting for OpenAI batch)

