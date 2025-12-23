"""
Submit batch to OpenAI Batch API
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
BATCH_INPUT_FILE = 'batch_requests.jsonl'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("="*70)
print("SUBMITTING BATCH TO OPENAI")
print("="*70)

# Upload the batch input file
print("\n[STEP 1] Uploading batch input file...")
with open(BATCH_INPUT_FILE, 'rb') as f:
    batch_input_file = client.files.create(
        file=f,
        purpose="batch"
    )

print(f"✓ Uploaded file: {batch_input_file.id}")

# Create the batch
print("\n[STEP 2] Creating batch...")
batch = client.batches.create(
    input_file_id=batch_input_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "description": "Innovation Radar article summarization"
    }
)

print(f"✓ Batch created: {batch.id}")
print(f"  Status: {batch.status}")
print(f"  Total requests: {batch.request_counts.total}")

# Save batch ID to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Mark all articles in this batch
cursor.execute("""
    UPDATE articles 
    SET batch_id = ?,
        summary_status = 'batch_submitted'
    WHERE (summary IS NULL OR summary = '')
      AND text IS NOT NULL
      AND text != ''
      AND LENGTH(text) > 200
""", (batch.id,))
conn.commit()

updated = cursor.rowcount
print(f"✓ Updated {updated} articles with batch_id: {batch.id}")

# Save batch info to file for reference
with open('batch_info.txt', 'w') as f:
    f.write(f"Batch ID: {batch.id}\n")
    f.write(f"File ID: {batch_input_file.id}\n")
    f.write(f"Status: {batch.status}\n")
    f.write(f"Created: {batch.created_at}\n")
    f.write(f"Total requests: {batch.request_counts.total}\n")

print("\n" + "="*70)
print("BATCH SUBMITTED SUCCESSFULLY")
print("="*70)
print(f"\nBatch ID: {batch.id}")
print(f"Status: {batch.status}")
print(f"\nThe batch will be processed within 24 hours.")
print(f"\nCheck status with: python summarize_batch_check.py")
print(f"Process results when complete: python summarize_batch_process.py")
print("="*70)

conn.close()

