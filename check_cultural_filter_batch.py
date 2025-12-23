"""
Check status of cultural filtering batch
"""
import os
import json
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
BATCH_RESULTS_FILE = 'cultural_filter_results.jsonl'

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Get batch ID from database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT filter_batch_id 
    FROM articles 
    WHERE filter_batch_id IS NOT NULL
    ORDER BY filter_batch_id DESC
    LIMIT 1
""")

result = cursor.fetchone()
if not result:
    print("❌ No batch found. Run filter_cultural_articles.py first.")
    exit(1)

batch_id = result[0]
print(f"Batch ID: {batch_id}\n")

# Get batch status
batch = client.batches.retrieve(batch_id)

print(f"Status: {batch.status}")
print(f"Total requests: {batch.request_counts.total}")
print(f"Completed: {batch.request_counts.completed}")
print(f"Failed: {batch.request_counts.failed}")

if batch.request_counts.total > 0:
    progress = (batch.request_counts.completed / batch.request_counts.total) * 100
    print(f"Progress: {progress:.1f}%")

if batch.status == 'completed':
    print("\n✅ Batch completed! Processing results...")
    
    if not batch.output_file_id:
        print("❌ No output file available")
        exit(1)
    
    # Download results
    file_response = client.files.content(batch.output_file_id)
    results_content = file_response.read().decode('utf-8')
    
    with open(BATCH_RESULTS_FILE, 'w') as f:
        f.write(results_content)
    print(f"✓ Saved results to {BATCH_RESULTS_FILE}")
    
    # Process results
    stats = {'relevant': 0, 'not_relevant': 0, 'errors': 0}
    
    for line in results_content.strip().split('\n'):
        if not line:
            continue
        
        result = json.loads(line)
        article_id = int(result['custom_id'])
        
        if result.get('error'):
            stats['errors'] += 1
            cursor.execute("UPDATE articles SET cultural_relevant = 1 WHERE id = ?", (article_id,))
        else:
            response = result['response']
            decision = response['body']['choices'][0]['message']['content'].strip().upper()
            is_relevant = 1 if 'YES' in decision else 0
            
            cursor.execute("UPDATE articles SET cultural_relevant = ? WHERE id = ?", (is_relevant, article_id))
            
            if is_relevant:
                stats['relevant'] += 1
            else:
                stats['not_relevant'] += 1
    
    conn.commit()
    
    # Get final counts
    cursor.execute("SELECT COUNT(*) FROM articles WHERE cultural_relevant = 1 AND summary IS NOT NULL")
    total_relevant = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE cultural_relevant = 0 AND summary IS NOT NULL")
    total_not_relevant = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
    total_summarized = cursor.fetchone()[0]
    
    print(f"\n✅ FILTERING COMPLETE")
    print(f"  ✓ Relevant: {stats['relevant']}")
    print(f"  ✗ Not relevant: {stats['not_relevant']}")
    print(f"  ✗ Errors: {stats['errors']}")
    print(f"\nTotal in database:")
    print(f"  Culturally relevant: {total_relevant} ({total_relevant/total_summarized*100:.1f}%)")
    print(f"  Not relevant: {total_not_relevant} ({total_not_relevant/total_summarized*100:.1f}%)")
    print(f"\nNext: python run_topic_modeling.py")

elif batch.status in ['failed', 'cancelled', 'expired']:
    print(f"\n❌ Batch {batch.status}")
    if batch.errors:
        print(f"Errors: {batch.errors}")
else:
    print(f"\n⏳ Still processing... Check again in a few minutes")

conn.close()

