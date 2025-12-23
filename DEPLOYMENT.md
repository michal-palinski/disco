# 🚀 Deployment Guide

## Step 1: Prepare for GitHub

### Check what will be committed:
```bash
git status
```

**Note**: Database files (`.db`), model files (`.pkl`), and API keys (`.env`) are excluded via `.gitignore` for security and size reasons.

## Step 2: Initialize Git & Push to GitHub

```bash
# Initialize git (if not already done)
cd /Users/michalpalinski/Desktop/innovation_radar
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Discoverability of Cultural Content dashboard"

# Create a new repository on GitHub (via browser):
# Go to: https://github.com/new
# Repository name: innovation_radar (or your preferred name)
# Description: Analysis of media narratives about cultural content discoverability
# Public or Private: Your choice
# DO NOT initialize with README (we already have one)

# Connect to GitHub (replace with your actual username and repo name)
git remote add origin https://github.com/YOUR_USERNAME/innovation_radar.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

### Prerequisites
- GitHub repository created (Step 2)
- Streamlit Cloud account (free): https://share.streamlit.io

### Deployment Steps

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with GitHub

2. **Create New App**
   - Click "New app"
   - Repository: Select `YOUR_USERNAME/innovation_radar`
   - Branch: `main`
   - Main file path: `dashboard.py`

3. **Add Secrets** (Important!)
   - Click "Advanced settings" before deploying
   - In "Secrets" section, add:
   
   ```toml
   # Note: Voyage AI key ONLY if you need to re-run topic modeling
   # Dashboard works without it if model files are pre-generated
   
   VOYAGE_API_KEY = "your-voyage-api-key"
   ```
   
   **Note**: The dashboard doesn't require API keys if you have pre-generated:
   - `topic_model.pkl`
   - `topic_descriptions.json`
   - `innovation_radar_unified.db`

4. **Deploy!**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - Your app will be live at: `https://YOUR_USERNAME-innovation-radar-dashboard-xxxxx.streamlit.app`

## Step 4: Share Pre-Generated Files (Optional)

Since model files are too large for GitHub, you have two options:

### Option A: Share via Cloud Storage
1. Upload to Google Drive/Dropbox:
   - `innovation_radar_unified.db`
   - `topic_model.pkl`
   - `topic_descriptions.json`
   
2. Add download instructions to README

### Option B: Git LFS (Large File Storage)
```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: apt-get install git-lfs  # Linux

# Initialize Git LFS
git lfs install

# Track large files
git lfs track "*.pkl"
git lfs track "*.db"

# Add and commit
git add .gitattributes
git add topic_model.pkl innovation_radar_unified.db
git commit -m "Add model files via Git LFS"
git push
```

### Option C: Database-only Deployment
If you only want to show the dashboard with existing data:
1. Include the SQLite database in git (remove `*.db` from `.gitignore`)
2. The dashboard will work for visualization only
3. Topic modeling and data collection remain local-only

## Step 5: Update Repository URL in README

After creating your GitHub repo, update the badge in `README.md`:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-URL.streamlit.app)
```

## 🔧 Troubleshooting

### "ModuleNotFoundError" on Streamlit Cloud
- Ensure all packages are in `requirements.txt`
- Check for typos in package names

### "FileNotFoundError: topic_model.pkl"
- Pre-generate the model locally: `python run_topic_modeling.py`
- Use Git LFS or cloud storage (see Step 4)

### Dashboard loads but no data
- Ensure `innovation_radar_unified.db` is available
- Check if database is in `.gitignore` (remove if you want it in git)

### Memory errors on Streamlit Cloud
- Free tier has 1GB RAM limit
- Consider reducing model size or using smaller datasets

## 📊 Continuous Deployment

Any push to `main` branch will automatically redeploy your Streamlit app!

```bash
# Make changes
git add .
git commit -m "Update dashboard styling"
git push

# Streamlit Cloud will auto-deploy in ~2 minutes
```

## 🎯 Production Checklist

- [ ] `.env` excluded from git (in `.gitignore`)
- [ ] API keys added to Streamlit secrets
- [ ] README updated with correct URLs
- [ ] Model files accessible (Git LFS or cloud storage)
- [ ] Database included or accessible
- [ ] Test deployment on Streamlit Cloud
- [ ] Update repository description on GitHub

---

**Need help?** Open an issue on GitHub or check [Streamlit Docs](https://docs.streamlit.io)

