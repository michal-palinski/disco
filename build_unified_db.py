"""
Unified database builder for Innovation Radar
Creates a single SQLite database from Google Search and Media Cloud sources
"""
import sqlite3
import csv
from datetime import datetime
from dateutil import parser as date_parser
import os

# Configuration
DB_PATH = 'innovation_radar_unified.db'
MEDIA_CLOUD_CSV = 'media_cloud/mc-onlinenews-mediacloud-20251219154919-content.csv'
GOOGLE_SEARCH_DB = 'google_search/innovation_radar.db'

print("="*70)
print("BUILDING UNIFIED INNOVATION RADAR DATABASE")
print("="*70)

# Create new unified database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"✓ Removed existing database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create unified table with common schema
cursor.execute('''
    CREATE TABLE articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        source TEXT,
        date TEXT,
        search_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
print(f"✓ Created new database: {DB_PATH}")
print(f"✓ Schema: title, url, source, date, search_type\n")

# Statistics
stats = {
    'google_news': {'added': 0, 'skipped': 0, 'errors': 0},
    'google_all': {'added': 0, 'skipped': 0, 'errors': 0},
    'media_cloud': {'added': 0, 'skipped': 0, 'errors': 0}
}

# ============================================================
# STEP 1: Import from Google Search database
# ============================================================
print("[STEP 1/2] Importing from Google Search database...")
print("-"*70)

if os.path.exists(GOOGLE_SEARCH_DB):
    google_conn = sqlite3.connect(GOOGLE_SEARCH_DB)
    google_cursor = google_conn.cursor()
    
    # Get all records with URLs
    google_cursor.execute("""
        SELECT title, link, source, date, search_type 
        FROM search_results 
        WHERE link IS NOT NULL AND link != ''
        ORDER BY created_at
    """)
    
    for row in google_cursor.fetchall():
        title = row[0] or ''
        url = row[1]
        source = row[2] or ''
        date = row[3] or ''
        search_type = row[4] or 'google_unknown'
        
        # Map search_type
        if search_type == 'news':
            mapped_type = 'google_news'
        elif search_type == 'all':
            mapped_type = 'google_all'
        else:
            mapped_type = search_type
        
        try:
            cursor.execute('''
                INSERT INTO articles (title, url, source, date, search_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, url, source, date, mapped_type))
            conn.commit()
            stats[mapped_type]['added'] += 1
            
        except sqlite3.IntegrityError:
            stats[mapped_type]['skipped'] += 1
        except Exception as e:
            stats[mapped_type]['errors'] += 1
    
    google_conn.close()
    print(f"✓ Google News: {stats['google_news']['added']} added, {stats['google_news']['skipped']} duplicates")
    print(f"✓ Google All:  {stats['google_all']['added']} added, {stats['google_all']['skipped']} duplicates")
else:
    print(f"⚠ Google Search database not found: {GOOGLE_SEARCH_DB}")

# ============================================================
# STEP 2: Import from Media Cloud CSV
# ============================================================
print(f"\n[STEP 2/2] Importing from Media Cloud CSV...")
print("-"*70)

if os.path.exists(MEDIA_CLOUD_CSV):
    with open(MEDIA_CLOUD_CSV, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Map columns: CSV -> Database
            title = row.get('title', '').strip()
            url = row.get('url', '').strip()
            source = row.get('media_name', '').strip()
            date_string = row.get('publish_date', '').strip()
            
            # Skip if no URL
            if not url:
                stats['media_cloud']['skipped'] += 1
                continue
            
            # Parse date to ISO format
            try:
                parsed_date = date_parser.parse(date_string)
                date = parsed_date.isoformat()
            except:
                date = date_string
            
            try:
                cursor.execute('''
                    INSERT INTO articles (title, url, source, date, search_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, url, source, date, 'media_cloud'))
                conn.commit()
                stats['media_cloud']['added'] += 1
                
                if stats['media_cloud']['added'] % 500 == 0:
                    print(f"  Processed {stats['media_cloud']['added']} records...")
                
            except sqlite3.IntegrityError:
                # Duplicate URL
                stats['media_cloud']['skipped'] += 1
            except Exception as e:
                stats['media_cloud']['errors'] += 1
    
    print(f"✓ Media Cloud: {stats['media_cloud']['added']} added, {stats['media_cloud']['skipped']} duplicates")
else:
    print(f"⚠ Media Cloud CSV not found: {MEDIA_CLOUD_CSV}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "="*70)
print("IMPORT COMPLETE")
print("="*70)

cursor.execute("SELECT COUNT(*) FROM articles")
total_records = cursor.fetchone()[0]

print(f"\nTotal records in database: {total_records}")
print(f"\nBreakdown by source:")

cursor.execute("SELECT search_type, COUNT(*) FROM articles GROUP BY search_type ORDER BY COUNT(*) DESC")
for search_type, count in cursor.fetchall():
    percentage = (count / total_records * 100) if total_records > 0 else 0
    print(f"  {search_type:<15} {count:>5} ({percentage:>5.1f}%)")

print(f"\nImport statistics:")
print(f"  Google News:   {stats['google_news']['added']} added, {stats['google_news']['skipped']} skipped")
print(f"  Google All:    {stats['google_all']['added']} added, {stats['google_all']['skipped']} skipped")
print(f"  Media Cloud:   {stats['media_cloud']['added']} added, {stats['media_cloud']['skipped']} skipped")

total_added = sum(s['added'] for s in stats.values())
total_skipped = sum(s['skipped'] for s in stats.values())
total_errors = sum(s['errors'] for s in stats.values())

print(f"\nTotals:")
print(f"  Added:     {total_added}")
print(f"  Skipped:   {total_skipped} (duplicates or invalid)")
print(f"  Errors:    {total_errors}")

print(f"\n✓ Database saved to: {DB_PATH}")
print("="*70)

conn.close()

