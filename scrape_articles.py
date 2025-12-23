"""
Scrape full article text using newspaper4k and add to database
"""
import sqlite3
from newspaper import Article
import time
from datetime import datetime

DB_PATH = 'innovation_radar_unified.db'

print("="*70)
print("SCRAPING ARTICLE TEXT WITH NEWSPAPER4K")
print("="*70)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add text column if it doesn't exist
print("\n[STEP 1] Adding text column to database...")
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN text TEXT')
    conn.commit()
    print("✓ Added 'text' column")
except sqlite3.OperationalError:
    print("✓ 'text' column already exists")

# Add scrape status columns
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN scraped_at TIMESTAMP')
    cursor.execute('ALTER TABLE articles ADD COLUMN scrape_status TEXT')
    conn.commit()
    print("✓ Added scraping status columns")
except sqlite3.OperationalError:
    print("✓ Status columns already exist")

# Get articles that haven't been scraped yet
cursor.execute("""
    SELECT id, url, title 
    FROM articles 
    WHERE text IS NULL OR text = ''
    ORDER BY id
""")

articles_to_scrape = cursor.fetchall()
total = len(articles_to_scrape)

print(f"\n[STEP 2] Found {total} articles to scrape\n")
print("-"*70)

# Statistics
stats = {
    'success': 0,
    'failed': 0,
    'skipped': 0
}

# Scrape each article
for idx, (article_id, url, title) in enumerate(articles_to_scrape, 1):
    try:
        print(f"[{idx}/{total}] Scraping: {title[:50]}...")
        
        # Create Article object
        article = Article(url)
        
        # Download and parse
        article.download()
        article.parse()
        
        # Get the text
        text = article.text
        
        if text and len(text) > 100:  # Only save if we got substantial text
            # Update database
            cursor.execute("""
                UPDATE articles 
                SET text = ?,
                    scraped_at = ?,
                    scrape_status = 'success'
                WHERE id = ?
            """, (text, datetime.now().isoformat(), article_id))
            conn.commit()
            
            stats['success'] += 1
            print(f"  ✓ Success ({len(text)} chars)")
        else:
            cursor.execute("""
                UPDATE articles 
                SET scrape_status = 'no_content'
                WHERE id = ?
            """, (article_id,))
            conn.commit()
            stats['skipped'] += 1
            print(f"  ⊗ No substantial content")
        
        # Be polite - small delay between requests
        time.sleep(0.5)
        
    except Exception as e:
        # Log the error
        error_msg = str(e)[:200]  # Truncate long errors
        cursor.execute("""
            UPDATE articles 
            SET scrape_status = ?
            WHERE id = ?
        """, (f'error: {error_msg}', article_id))
        conn.commit()
        
        stats['failed'] += 1
        print(f"  ✗ Error: {str(e)[:60]}")
    
    # Progress update every 50 articles
    if idx % 50 == 0:
        print(f"\n--- Progress: {idx}/{total} articles processed ---")
        print(f"    Success: {stats['success']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}\n")

# Final summary
print("\n" + "="*70)
print("SCRAPING COMPLETE")
print("="*70)

cursor.execute("SELECT COUNT(*) FROM articles WHERE text IS NOT NULL AND text != ''")
total_with_text = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles")
total_articles = cursor.fetchone()[0]

print(f"\nTotal articles in database: {total_articles}")
print(f"Articles with text: {total_with_text} ({total_with_text/total_articles*100:.1f}%)")
print(f"\nThis session:")
print(f"  ✓ Successfully scraped: {stats['success']}")
print(f"  ⊗ No content found: {stats['skipped']}")
print(f"  ✗ Errors: {stats['failed']}")

print(f"\nStatus breakdown:")
cursor.execute("SELECT scrape_status, COUNT(*) FROM articles GROUP BY scrape_status")
for status, count in cursor.fetchall():
    status_label = status if status else 'not_scraped'
    print(f"  {status_label}: {count}")

print(f"\n✓ Database updated: {DB_PATH}")
print("="*70)

conn.close()

