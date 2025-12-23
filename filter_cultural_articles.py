"""
Filter articles to keep only those relevant to culture using GPT Batch API
Run this BEFORE topic modeling to remove irrelevant articles
"""
import sqlite3
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
BATCH_INPUT_FILE = 'cultural_filter_batch.jsonl'
BATCH_RESULTS_FILE = 'cultural_filter_results.jsonl'
BATCH_INFO_FILE = 'cultural_filter_batch_info.txt'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

print("="*70)
print("FILTERING ARTICLES FOR CULTURAL RELEVANCE (BATCH API)")
print("="*70)
print("  Model: gpt-4o-mini (use gpt-5-mini when available)")
print("  Method: Batch API (50% discount)")
print("  Criteria: Culture & creative industries relevance")
print("="*70)

# Step 1: Prepare batch requests
print("\n[STEP 1] Loading articles from database...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add cultural_relevant column if it doesn't exist
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN cultural_relevant INTEGER')
    cursor.execute('ALTER TABLE articles ADD COLUMN filter_batch_id TEXT')
    conn.commit()
    print("✓ Added cultural_relevant column")
except sqlite3.OperationalError:
    print("✓ cultural_relevant column already exists")

# Get articles that need filtering
cursor.execute("""
    SELECT id, title, summary
    FROM articles 
    WHERE summary IS NOT NULL 
      AND summary != ''
      AND LENGTH(summary) > 50
      AND cultural_relevant IS NULL
""")

articles = cursor.fetchall()
print(f"✓ Found {len(articles)} articles to filter")

if len(articles) == 0:
    print("\nNo articles to filter. All articles already filtered.")
    conn.close()
    exit(0)

# Step 2: Create batch request file
print("\n[STEP 2] Creating batch request file...")

system_prompt = """You are an expert in culture, creative industries, and cultural content.

Your task is to determine if an article is relevant to culture and creative industries for a study about DISCOVERABILITY.

RELEVANT articles discuss:
- Cultural content (e.g. film, TV, music, books, art, theater, museums, heritage)
- Creative industries (e.g. media, publishing, entertainment, gaming, fashion)
- Cultural policies and funding
- Arts organizations and cultural institutions
- Cultural content platforms and distribution
- Cultural participation and access
- Cultural diversity and representation

NOT RELEVANT articles focus primarily on:
- General tourism (unless discussing cultural tourism/heritage sites)
- Job market/employment (unless cultural sector jobs)
- General business/economics (unless cultural economics)
- Technology in general (unless for cultural content)
- Politics in general (unless cultural policy)

Answer ONLY with "YES" or "NO"."""

with open(BATCH_INPUT_FILE, 'w') as f:
    for article_id, title, summary in articles:
        user_prompt = f"""Title: {title}

Summary: {summary}

Is this article relevant to culture and creative industries?"""
        
        request = {
            "custom_id": str(article_id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 10
            }
        }
        f.write(json.dumps(request) + '\n')

print(f"✓ Created {BATCH_INPUT_FILE} with {len(articles)} requests")

# Calculate cost estimate
estimated_tokens = len(articles) * 400  # Rough estimate
estimated_cost = (estimated_tokens / 1_000_000) * 0.075  # Batch API pricing
regular_cost = (estimated_tokens / 1_000_000) * 0.15
print(f"\n💰 Cost estimate:")
print(f"   Batch API: ${estimated_cost:.2f} (with 50% discount)")
print(f"   Regular API: ${regular_cost:.2f}")
print(f"   Savings: ${regular_cost - estimated_cost:.2f}")

# Step 3: Submit batch
print("\n[STEP 3] Uploading and submitting batch...")

with open(BATCH_INPUT_FILE, 'rb') as f:
    batch_input_file = client.files.create(
        file=f,
        purpose="batch"
    )

print(f"✓ Uploaded file: {batch_input_file.id}")

batch = client.batches.create(
    input_file_id=batch_input_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "description": "Cultural relevance filtering"
    }
)

print(f"✓ Batch created: {batch.id}")
print(f"  Status: {batch.status}")

# Save batch info
with open(BATCH_INFO_FILE, 'w') as f:
    f.write(f"Batch ID: {batch.id}\n")
    f.write(f"File ID: {batch_input_file.id}\n")
    f.write(f"Status: {batch.status}\n")
    f.write(f"Articles: {len(articles)}\n")

# Mark articles with batch ID
cursor.execute("""
    UPDATE articles 
    SET filter_batch_id = ?
    WHERE id IN ({})
""".format(','.join([str(a[0]) for a in articles])), (batch.id,))
conn.commit()
conn.close()

print(f"✓ Saved batch info to {BATCH_INFO_FILE}")

# Step 4: Wait and check status
print("\n[STEP 4] Waiting for batch to complete...")
print("  This typically takes 5-15 minutes")
print("  You can check status manually with: python check_cultural_filter_batch.py")
print("  Or wait here (checks every 30 seconds)...")

wait = input("\nWait here for completion? (y/n): ").lower().strip()

if wait == 'y':
    print("\n⏳ Checking batch status every 30 seconds...")
    while True:
        batch = client.batches.retrieve(batch.id)
        status = batch.status
        
        if status == 'completed':
            print(f"\n✅ Batch completed!")
            break
        elif status == 'failed':
            print(f"\n❌ Batch failed")
            print(f"Error: {batch.errors}")
            exit(1)
        elif status in ['cancelled', 'expired']:
            print(f"\n❌ Batch {status}")
            exit(1)
        else:
            completed = batch.request_counts.completed
            total = batch.request_counts.total
            progress = (completed / total * 100) if total > 0 else 0
            print(f"  Status: {status} | Progress: {completed}/{total} ({progress:.1f}%)")
            time.sleep(30)
    
    # Step 5: Process results
    print("\n[STEP 5] Processing results...")
    
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {'relevant': 0, 'not_relevant': 0, 'errors': 0}
    
    for line in results_content.strip().split('\n'):
        if not line:
            continue
        
        result = json.loads(line)
        article_id = int(result['custom_id'])
        
        if result.get('error'):
            stats['errors'] += 1
            # Mark as relevant on error (conservative)
            cursor.execute("""
                UPDATE articles 
                SET cultural_relevant = 1
                WHERE id = ?
            """, (article_id,))
        else:
            response = result['response']
            decision = response['body']['choices'][0]['message']['content'].strip().upper()
            is_relevant = 1 if 'YES' in decision else 0
            
            cursor.execute("""
                UPDATE articles 
                SET cultural_relevant = ?
                WHERE id = ?
            """, (is_relevant, article_id))
            
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
    
    conn.close()
    
    # Summary
    print("\n" + "="*70)
    print("FILTERING COMPLETE")
    print("="*70)
    print(f"\nThis batch:")
    print(f"  ✓ Relevant: {stats['relevant']}")
    print(f"  ✗ Not relevant: {stats['not_relevant']}")
    print(f"  ✗ Errors: {stats['errors']}")
    
    print(f"\nTotal in database:")
    print(f"  Culturally relevant: {total_relevant} ({total_relevant/total_summarized*100:.1f}%)")
    print(f"  Not relevant: {total_not_relevant} ({total_not_relevant/total_summarized*100:.1f}%)")
    print(f"  Total summarized: {total_summarized}")
    
    print(f"\nNext step:")
    print(f"  Run topic modeling (will only use cultural_relevant=1 articles)")
    print(f"  python run_topic_modeling.py")
    print("="*70)

else:
    print("\n" + "="*70)
    print("BATCH SUBMITTED")
    print("="*70)
    print(f"\nBatch ID: {batch.id}")
    print(f"Status: {batch.status}")
    print(f"\nCheck status later with:")
    print(f"  python check_cultural_filter_batch.py")
    print(f"\nOr check manually:")
    print(f"  python -c \"from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); print(OpenAI(api_key=os.getenv('OPENAI_API_KEY')).batches.retrieve('{batch.id}'))\"")
    print("="*70)
