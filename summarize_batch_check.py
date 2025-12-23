"""
Check status of OpenAI batch
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("="*70)
print("CHECKING BATCH STATUS")
print("="*70)

# Get batch ID from database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT batch_id 
    FROM articles 
    WHERE batch_id IS NOT NULL
    ORDER BY batch_id DESC
    LIMIT 1
""")

result = cursor.fetchone()
if not result:
    print("\n✗ No batch found in database")
    print("Run summarize_batch_submit.py first")
    exit(1)

batch_id = result[0]
print(f"\nBatch ID: {batch_id}\n")
print("-"*70)

# Get batch status
batch = client.batches.retrieve(batch_id)

print(f"Status: {batch.status}")
print(f"Created at: {datetime.fromtimestamp(batch.created_at)}")

if batch.completed_at:
    print(f"Completed at: {datetime.fromtimestamp(batch.completed_at)}")
    duration = batch.completed_at - batch.created_at
    print(f"Duration: {duration // 60} minutes")

if batch.failed_at:
    print(f"Failed at: {datetime.fromtimestamp(batch.failed_at)}")

print(f"\nRequest counts:")
print(f"  Total: {batch.request_counts.total}")
print(f"  Completed: {batch.request_counts.completed}")
print(f"  Failed: {batch.request_counts.failed}")

if batch.request_counts.total > 0:
    progress = (batch.request_counts.completed / batch.request_counts.total) * 100
    print(f"  Progress: {progress:.1f}%")

if batch.output_file_id:
    print(f"\n✓ Output file ready: {batch.output_file_id}")
    print(f"\nRun: python summarize_batch_process.py")
elif batch.status == 'failed':
    print(f"\n✗ Batch failed")
    if batch.errors:
        print(f"Errors: {batch.errors}")
elif batch.status in ['validating', 'in_progress', 'finalizing']:
    print(f"\n⏳ Batch is still processing...")
    print(f"Check again later with: python summarize_batch_check.py")
elif batch.status == 'completed':
    print(f"\n✓ Batch completed!")
    print(f"Run: python summarize_batch_process.py")

print("="*70)
conn.close()

