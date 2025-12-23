# Quick Start Guide - Innovation Radar

## Complete Workflow

### Step 1: Install Dependencies
```bash
cd /Users/michalpalinski/Desktop/innovation_radar
pip install -r requirements.txt
```

### Step 2: Build Unified Database
```bash
python build_unified_db.py
```
**Output:** `innovation_radar_unified.db` with 2,592 articles

### Step 3: Scrape Article Text (Optional but Recommended)
```bash
python scrape_articles.py
```
**Time:** ~20-30 minutes for all articles  
**Output:** Adds full text to database

### Step 4: Summarize with AI (Optional) - BATCH API RECOMMENDED

**Create .env file:**
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

**Batch API Method (Recommended - 50% cheaper):**
```bash
# 1. Prepare batch (instant)
python summarize_batch_prepare.py

# 2. Submit to OpenAI (instant)
python summarize_batch_submit.py

# 3. Check status (run every hour)
python summarize_batch_check.py

# 4. Process results when complete
python summarize_batch_process.py
```
**Time:** 2-6 hours (asynchronous)  
**Cost:** ~$2.50-5 (50% discount)  

**Real-time API Method (Alternative):**
```bash
python summarize_articles.py
```
**Time:** ~30-60 minutes  
**Cost:** ~$5-10  

**Output:** Adds discoverability-focused summaries to database

### Step 5: Run Topic Modeling (After summaries complete)
```bash
python run_topic_modeling.py
```
**Time:** 5-10 minutes  
**Output:** Topic assignments for all articles

### Step 6: Launch Interactive Dashboard
```bash
streamlit run dashboard.py
```
**Opens:** http://localhost:8501  
**Features:**
- Topic distribution charts
- Topic trends over time
- Interactive article explorer
- Filtered data downloads

### Step 7: Export to CSV (Optional)
```bash
python export_to_csv.py
```
**Output:** `innovation_radar_export.csv` with all data

---

## AI Summarization Focus

The summarization script is specifically designed to:

✅ **Extract & Preserve:**
- Content discovery mechanisms and algorithms
- Discoverability challenges and solutions
- Search, recommendation, curation systems
- Cultural content accessibility
- Platform policies affecting discoverability
- Technology and AI in content discovery
- Creative industry discoverability issues
- Metadata, SEO, content optimization

❌ **Remove:**
- Marketing fluff and promotional language
- Irrelevant biographical information
- Company history (unless relevant)
- General background
- Redundant statements

---

## Database Schema

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT,
    date TEXT,
    search_type TEXT NOT NULL,
    text TEXT,                -- Full article (scraped)
    summary TEXT,             -- AI summary (OpenAI)
    scrape_status TEXT,       -- 'success', 'error', etc.
    scraped_at TIMESTAMP,
    summary_status TEXT,      -- 'success', 'error', etc.
    summarized_at TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## Cost Estimates

| Operation | Time | Cost |
|-----------|------|------|
| Build Database | 1 min | Free |
| Scrape Articles | 20-30 min | Free |
| Summarize (Batch API) | 2-6 hours | $2.50-5 (50% off) |
| Summarize (Real-time) | 30-60 min | $5-10 |
| Export CSV | 1 min | Free |

**💡 Use Batch API for 50% cost savings!**

---

## Resumable Operations

All scripts are resumable:
- **Scraping:** Only processes articles without text
- **Summarization:** Only processes articles without summaries
- Can safely interrupt and restart anytime

