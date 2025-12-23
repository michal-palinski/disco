"""
Process completed batch results and update database
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import json
from datetime import datetime

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

print("="*70)
print("PROCESSING BATCH RESULTS")
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
    exit(1)

batch_id = result[0]
print(f"\nBatch ID: {batch_id}\n")
print("-"*70)

# Get batch status
batch = client.batches.retrieve(batch_id)

if batch.status != 'completed':
    print(f"✗ Batch not completed yet. Status: {batch.status}")
    print(f"Run: python summarize_batch_check.py")
    exit(1)

if not batch.output_file_id:
    print("✗ No output file available")
    exit(1)

print(f"[STEP 1] Downloading results...")
print(f"  Output file: {batch.output_file_id}")

# Download the results
file_response = client.files.content(batch.output_file_id)
results_content = file_response.read().decode('utf-8')

# Save results to file for backup
with open('batch_results.jsonl', 'w') as f:
    f.write(results_content)
print(f"✓ Saved results to batch_results.jsonl")

# Process results
print(f"\n[STEP 2] Processing results and updating database...")
print("-"*70)

stats = {
    'success': 0,
    'failed': 0,
    'total_tokens': 0
}

for line in results_content.strip().split('\n'):
    if not line:
        continue
    
    result = json.loads(line)
    custom_id = result['custom_id']  # This is our article ID
    article_id = int(custom_id)
    
    if result.get('error'):
        # Handle error
        error_msg = str(result['error'])[:200]
        cursor.execute("""
            UPDATE articles 
            SET summary_status = ?
            WHERE id = ?
        """, (f'error: {error_msg}', article_id))
        stats['failed'] += 1
        print(f"  ✗ Article {article_id}: Error - {error_msg[:60]}")
    else:
        # Extract summary
        response = result['response']
        summary = response['body']['choices'][0]['message']['content']
        tokens = response['body']['usage']['total_tokens']
        stats['total_tokens'] += tokens
        
        # Update database
        cursor.execute("""
            UPDATE articles 
            SET summary = ?,
                summarized_at = ?,
                summary_status = 'success'
            WHERE id = ?
        """, (summary, datetime.now().isoformat(), article_id))
        
        stats['success'] += 1
        
        if stats['success'] % 100 == 0:
            print(f"  ✓ Processed {stats['success']} articles...")

conn.commit()

# Final summary
print("\n" + "="*70)
print("PROCESSING COMPLETE")
print("="*70)

cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
total_with_summary = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles WHERE text IS NOT NULL AND text != ''")
total_with_text = cursor.fetchone()[0]

print(f"\nArticles with text: {total_with_text}")
print(f"Articles with summaries: {total_with_summary} ({total_with_summary/total_with_text*100:.1f}%)")
print(f"\nThis batch:")
print(f"  ✓ Successfully summarized: {stats['success']}")
print(f"  ✗ Errors: {stats['failed']}")
print(f"  📊 Total tokens used: {stats['total_tokens']:,}")

# Calculate actual cost (with 50% batch discount)
input_cost = (stats['total_tokens'] * 0.5 / 1_000_000) * 0.075  # Rough estimate
output_cost = (stats['total_tokens'] * 0.5 / 1_000_000) * 0.300
total_cost = input_cost + output_cost
print(f"  💰 Estimated cost: ${total_cost:.2f} (with 50% batch discount)")

print(f"\nStatus breakdown:")
cursor.execute("""
    SELECT summary_status, COUNT(*) 
    FROM articles 
    WHERE summary_status IS NOT NULL 
    GROUP BY summary_status
""")
for status, count in cursor.fetchall():
    print(f"  {status}: {count}")

print(f"\n✓ Database updated: {DB_PATH}")
print(f"✓ Export with: python export_to_csv.py")
print("="*70)

conn.close()

