import sqlite3
import csv
from datetime import datetime
from dateutil import parser as date_parser

# Database setup - use the main database
DB_PATH = 'google_search/innovation_radar.db'
CSV_PATH = 'media_cloud/mc-onlinenews-mediacloud-20251219154919-content.csv'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure search_type column exists
try:
    cursor.execute('ALTER TABLE search_results ADD COLUMN search_type TEXT')
    conn.commit()
    print("Added search_type column to table")
except sqlite3.OperationalError:
    pass  # Column already exists

print(f"Reading CSV file: {CSV_PATH}")
print(f"Integrating into database: {DB_PATH}\n")

# Counters
new_count = 0
duplicate_count = 0
error_count = 0

# Read and import CSV
with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        try:
            # Extract fields from CSV
            title = row.get('title', '').strip()
            link = row.get('url', '').strip()
            source = row.get('media_name', '').strip()
            date_string = row.get('publish_date', '').strip()
            
            # Parse the date to ISO format
            try:
                parsed_date = date_parser.parse(date_string)
                date_to_store = parsed_date.isoformat()
            except:
                date_to_store = date_string
            
            # Insert into database
            cursor.execute('''
                INSERT INTO search_results (title, link, source, date, snippet, query, search_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, link, source, date_to_store, '', 'media_cloud_import', 'media_cloud'))
            
            conn.commit()
            new_count += 1
            
            if new_count % 100 == 0:
                print(f"✓ Processed {new_count} records...")
                
        except sqlite3.IntegrityError:
            # Duplicate URL
            duplicate_count += 1
            if duplicate_count % 100 == 0:
                print(f"⊗ Skipped {duplicate_count} duplicates...")
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Only show first 5 errors
                print(f"✗ Error processing row: {e}")

# Final summary
print(f"\n{'='*50}")
print(f"--- Integration Summary ---")
print(f"New records added: {new_count}")
print(f"Duplicates skipped: {duplicate_count}")
print(f"Errors: {error_count}")
print(f"Total records in database: {cursor.execute('SELECT COUNT(*) FROM search_results').fetchone()[0]}")
print(f"\nBreakdown by search_type:")
cursor.execute('SELECT search_type, COUNT(*) FROM search_results GROUP BY search_type')
for search_type, count in cursor.fetchall():
    print(f"  {search_type}: {count}")
print(f"{'='*50}")

conn.close()

