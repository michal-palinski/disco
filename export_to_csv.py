"""
Export unified database to CSV
"""
import sqlite3
import csv

DB_PATH = 'innovation_radar_unified.db'
OUTPUT_CSV = 'innovation_radar_export.csv'

print(f"Exporting database to CSV...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all data
cursor.execute("""
    SELECT id, title, url, source, date, search_type, text, summary, 
           scrape_status, scraped_at, summary_status, summarized_at, created_at
    FROM articles
    ORDER BY date DESC
""")

rows = cursor.fetchall()
columns = ['id', 'title', 'url', 'source', 'date', 'search_type', 'text', 'summary',
           'scrape_status', 'scraped_at', 'summary_status', 'summarized_at', 'created_at']

# Write to CSV
with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"✓ Exported {len(rows)} records to {OUTPUT_CSV}")

# Show statistics
print(f"\nBreakdown by search_type:")
cursor.execute("SELECT search_type, COUNT(*) FROM articles GROUP BY search_type ORDER BY COUNT(*) DESC")
for search_type, count in cursor.fetchall():
    print(f"  {search_type}: {count}")

conn.close()

