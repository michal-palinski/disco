"""
Summarize articles using OpenAI API focusing on discoverability content
"""
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    print("Please create a .env file with your OpenAI API key:")
    print("  OPENAI_API_KEY=your_key_here")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

print("="*70)
print("SUMMARIZING ARTICLES WITH OPENAI (gpt-5-nano)")
print("="*70)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add summary column if it doesn't exist
print("\n[STEP 1] Adding summary column to database...")
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN summary TEXT')
    conn.commit()
    print("✓ Added 'summary' column")
except sqlite3.OperationalError:
    print("✓ 'summary' column already exists")

# Add summary metadata columns
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN summarized_at TIMESTAMP')
    cursor.execute('ALTER TABLE articles ADD COLUMN summary_status TEXT')
    conn.commit()
    print("✓ Added summary metadata columns")
except sqlite3.OperationalError:
    print("✓ Metadata columns already exist")

# Get articles with text that haven't been summarized yet
cursor.execute("""
    SELECT id, title, text, url
    FROM articles 
    WHERE text IS NOT NULL 
      AND text != ''
      AND LENGTH(text) > 200
      AND (summary IS NULL OR summary = '')
    ORDER BY id
""")

articles_to_summarize = cursor.fetchall()
total = len(articles_to_summarize)

print(f"\n[STEP 2] Found {total} articles with text to summarize\n")
print("-"*70)

# Statistics
stats = {
    'success': 0,
    'failed': 0,
    'skipped': 0,
    'tokens_used': 0
}

# System prompt for summarization
SYSTEM_PROMPT = """You are an expert analyst specializing in content discoverability and digital media. 
Your task is to summarize articles by extracting and preserving ALL information related to discoverability 
while removing irrelevant, non-substantive content.

Focus on:
- Content discovery mechanisms, algorithms, and platforms
- Discoverability challenges and solutions
- Search, recommendation, and curation systems
- Cultural content accessibility and visibility
- Platform policies affecting content discoverability
- Technology and AI in content discovery
- Creative industry discoverability issues
- Metadata, SEO, and content optimization

Remove:
- Marketing fluff and promotional language
- Biographical information not related to discoverability
- Company history unless directly relevant
- General background that doesn't relate to discoverability
- Redundant or repetitive statements

Provide a concise but comprehensive summary that preserves all discoverability-related details."""

# Summarize each article
for idx, (article_id, title, text, url) in enumerate(articles_to_summarize, 1):
    try:
        print(f"[{idx}/{total}] Summarizing: {title[:60]}...")
        
        # Prepare the prompt
        user_prompt = f"""Article Title: {title}
Article URL: {url}

Article Text:
{text}

Please provide a focused summary extracting all discoverability-related information."""
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
        )
        
        # Extract summary
        summary = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        stats['tokens_used'] += tokens_used
        
        # Update database
        cursor.execute("""
            UPDATE articles 
            SET summary = ?,
                summarized_at = ?,
                summary_status = 'success'
            WHERE id = ?
        """, (summary, datetime.now().isoformat(), article_id))
        conn.commit()
        
        stats['success'] += 1
        print(f"  ✓ Success ({len(summary)} chars, {tokens_used} tokens)")
        
        # Rate limiting - be polite to OpenAI API
        time.sleep(0.5)
        
    except Exception as e:
        # Log the error
        error_msg = str(e)[:200]
        cursor.execute("""
            UPDATE articles 
            SET summary_status = ?
            WHERE id = ?
        """, (f'error: {error_msg}', article_id))
        conn.commit()
        
        stats['failed'] += 1
        print(f"  ✗ Error: {str(e)[:80]}")
        
        # If rate limit error, wait longer
        if 'rate_limit' in str(e).lower():
            print("  ⏸ Rate limit hit, waiting 60 seconds...")
            time.sleep(60)
    
    # Progress update every 25 articles
    if idx % 25 == 0:
        print(f"\n--- Progress: {idx}/{total} articles ---")
        print(f"    Success: {stats['success']}, Failed: {stats['failed']}")
        print(f"    Tokens used: {stats['tokens_used']:,}")
        estimated_cost = (stats['tokens_used'] / 1_000_000) * 0.15  # Rough estimate for gpt-4o-mini
        print(f"    Est. cost: ${estimated_cost:.4f}\n")

# Final summary
print("\n" + "="*70)
print("SUMMARIZATION COMPLETE")
print("="*70)

cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
total_with_summary = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles WHERE text IS NOT NULL AND text != ''")
total_with_text = cursor.fetchone()[0]

print(f"\nArticles with text: {total_with_text}")
print(f"Articles with summaries: {total_with_summary} ({total_with_summary/total_with_text*100:.1f}%)")
print(f"\nThis session:")
print(f"  ✓ Successfully summarized: {stats['success']}")
print(f"  ✗ Errors: {stats['failed']}")
print(f"  📊 Total tokens used: {stats['tokens_used']:,}")

estimated_cost = (stats['tokens_used'] / 1_000_000) * 0.15
print(f"  💰 Estimated cost: ${estimated_cost:.4f}")

print(f"\nStatus breakdown:")
cursor.execute("SELECT summary_status, COUNT(*) FROM articles WHERE summary_status IS NOT NULL GROUP BY summary_status")
for status, count in cursor.fetchall():
    print(f"  {status}: {count}")

print(f"\n✓ Database updated: {DB_PATH}")
print("="*70)

conn.close()

