"""
Prepare batch requests for OpenAI Batch API
Creates JSONL file with all summarization requests
"""
import sqlite3
import json
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
BATCH_INPUT_FILE = 'batch_requests.jsonl'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

print("="*70)
print("PREPARING BATCH SUMMARIZATION REQUESTS")
print("="*70)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add batch tracking columns if they don't exist
print("\n[STEP 1] Setting up database...")
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN summary TEXT')
    cursor.execute('ALTER TABLE articles ADD COLUMN summary_status TEXT')
    cursor.execute('ALTER TABLE articles ADD COLUMN summarized_at TIMESTAMP')
    cursor.execute('ALTER TABLE articles ADD COLUMN batch_id TEXT')
    conn.commit()
    print("✓ Added columns")
except sqlite3.OperationalError:
    print("✓ Columns already exist")

# Get articles with text that need summarization
cursor.execute("""
    SELECT id, title, text, url
    FROM articles 
    WHERE text IS NOT NULL 
      AND text != ''
      AND LENGTH(text) > 200
      AND (summary IS NULL OR summary = '')
    ORDER BY id
""")

articles = cursor.fetchall()
total = len(articles)

print(f"\n[STEP 2] Found {total} articles to summarize\n")
print("-"*70)

# System prompt
SYSTEM_PROMPT = """You are an expert analyst specializing in content discoverability and digital media. 
Your task is to summarize articles by extracting and preserving ALL information related to discoverability 
while removing irrelevant, non-substantive content.

Focus on:
- Content discovery mechanisms, algorithms, and platforms
- Discoverability challenges and solutions
- Search, recommendation, and curation systems
- Cultural content accessibility and visibility
- Platform policies affecting content discoverability
- Technology and AI in content discovery
- Creative industry discoverability issues
- Metadata, SEO, and content optimization

Remove:
- Marketing fluff and promotional language
- Biographical information not related to discoverability
- Company history unless directly relevant
- General background that doesn't relate to discoverability
- Redundant or repetitive statements

Provide a concise but comprehensive summary that preserves all discoverability-related details."""

# Create batch requests in JSONL format
print("[STEP 3] Creating batch request file...")
with open(BATCH_INPUT_FILE, 'w') as f:
    for article_id, title, text, url in articles:
        user_prompt = f"""Article Title: {title}
Article URL: {url}

Article Text:
{text}

Please provide a focused summary extracting all discoverability-related information."""
        
        # Create request in OpenAI Batch API format
        request = {
            "custom_id": str(article_id),  # Use article ID as custom_id
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
        }
        
        # Write as JSON line
        f.write(json.dumps(request) + '\n')

print(f"✓ Created {BATCH_INPUT_FILE} with {total} requests")

# Calculate estimated cost
# Batch API is 50% off regular pricing
# gpt-4o-mini: $0.150 per 1M input tokens, $0.600 per 1M output tokens
# With batch discount: $0.075 per 1M input, $0.300 per 1M output

# Rough estimate: avg 1500 tokens input + 500 tokens output per article
estimated_input_tokens = total * 1500
estimated_output_tokens = total * 500
estimated_cost = (estimated_input_tokens / 1_000_000 * 0.075) + (estimated_output_tokens / 1_000_000 * 0.300)

print(f"\n[STEP 4] Cost Estimate:")
print(f"  Articles: {total}")
print(f"  Est. input tokens: {estimated_input_tokens:,}")
print(f"  Est. output tokens: {estimated_output_tokens:,}")
print(f"  Est. cost: ${estimated_cost:.2f} (with 50% batch discount)")
print(f"  Regular API cost: ${estimated_cost * 2:.2f}")
print(f"  Savings: ${estimated_cost:.2f}")

print(f"\n✓ Ready to submit batch!")
print(f"\nNext steps:")
print(f"  1. Run: python summarize_batch_submit.py")
print(f"  2. Wait for batch to complete (check with: python summarize_batch_check.py)")
print(f"  3. Process results: python summarize_batch_process.py")
print("="*70)

conn.close()

