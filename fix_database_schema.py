"""
Add missing columns to database for batch API tracking
"""
import sqlite3

DB_PATH = 'innovation_radar_unified.db'

print("Fixing database schema...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add all missing columns
columns_to_add = [
    ('summary', 'TEXT'),
    ('summary_status', 'TEXT'),
    ('summarized_at', 'TIMESTAMP'),
    ('batch_id', 'TEXT'),
    ('text', 'TEXT'),
    ('scrape_status', 'TEXT'),
    ('scraped_at', 'TIMESTAMP')
]

for column_name, column_type in columns_to_add:
    try:
        cursor.execute(f'ALTER TABLE articles ADD COLUMN {column_name} {column_type}')
        conn.commit()
        print(f"✓ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  Column already exists: {column_name}")
        else:
            print(f"  Error adding {column_name}: {e}")

# Now update the batch_id for the submitted batch
# The batch ID from your terminal is: batch_69494aa753708190818b6d63dd6bb69c
BATCH_ID = "batch_69494aa753708190818b6d63dd6bb69c"

cursor.execute("""
    UPDATE articles 
    SET batch_id = ?,
        summary_status = 'batch_submitted'
    WHERE (summary IS NULL OR summary = '')
      AND text IS NOT NULL
      AND text != ''
      AND LENGTH(text) > 200
""", (BATCH_ID,))
conn.commit()

updated = cursor.rowcount
print(f"\n✓ Updated {updated} articles with batch_id: {BATCH_ID}")

# Save batch info
with open('batch_info.txt', 'w') as f:
    f.write(f"Batch ID: {BATCH_ID}\n")
    f.write(f"Status: submitted\n")
    f.write(f"Articles: {updated}\n")

print(f"\n✓ Database schema fixed!")
print(f"✓ Batch info saved to batch_info.txt")
print(f"\nYou can now run:")
print(f"  python summarize_batch_check.py")

conn.close()

