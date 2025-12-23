"""
Generate detailed topic descriptions using GPT-5-mini
Reads 30 random articles from each topic to create comprehensive descriptions
"""
import sqlite3
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import pickle
from bertopic import BERTopic

load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
MODEL_PATH = 'topic_model.pkl'
OUTPUT_PATH = 'topic_descriptions.json'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

print("="*70)
print("GENERATING TOPIC DESCRIPTIONS WITH GPT")
print("="*70)

# Load topic model
print("\n[STEP 1] Loading topic model...")
try:
    topic_model = BERTopic.load(MODEL_PATH)
    print(f"✓ Loaded topic model")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    exit(1)

# Get topic info
topic_info = topic_model.get_topic_info()
topics_to_process = [t for t in topic_info['Topic'].values if t != -1]

print(f"✓ Found {len(topics_to_process)} topics to describe")

# Connect to database
print("\n[STEP 2] Loading articles from database...")
conn = sqlite3.connect(DB_PATH)

# Get all summarized articles with topics
query = """
    SELECT id, title, summary, topic
    FROM articles 
    WHERE summary IS NOT NULL 
      AND summary != ''
      AND topic IS NOT NULL
      AND topic != -1
"""

cursor = conn.cursor()
cursor.execute(query)
articles = cursor.fetchall()
conn.close()

print(f"✓ Loaded {len(articles)} articles")

# Organize articles by topic
articles_by_topic = {}
for article_id, title, summary, topic in articles:
    if topic not in articles_by_topic:
        articles_by_topic[topic] = []
    articles_by_topic[topic].append({
        'id': article_id,
        'title': title,
        'summary': summary
    })

print(f"✓ Organized articles into {len(articles_by_topic)} topics")

# Generate descriptions
print("\n[STEP 3] Generating topic descriptions...")
print("-"*70)

topic_descriptions = {}

system_prompt = """You are an expert analyst specializing in content discoverability and digital media.
Your task is to create a comprehensive description of a topic based on a collection of article summaries.

Focus on:
- What this topic is about in the context of discoverability
- Key themes and patterns across the articles
- Relevant technologies, platforms, or approaches mentioned
- Why this topic matters for content discovery

Write in 2-3 paragraphs, clear and informative. Avoid generic statements."""

for i, topic_id in enumerate(topics_to_process, 1):
    if topic_id not in articles_by_topic:
        print(f"[{i}/{len(topics_to_process)}] Topic {topic_id}: No articles found, skipping")
        continue
    
    topic_articles = articles_by_topic[topic_id]
    
    # Sample up to 30 random articles
    import random
    sample_size = min(30, len(topic_articles))
    sampled_articles = random.sample(topic_articles, sample_size)
    
    # Get topic keywords
    keywords = topic_model.get_topic(topic_id)[:10]
    keyword_str = ', '.join([word for word, _ in keywords])
    
    # Get topic label if available
    topic_row = topic_info[topic_info['Topic'] == topic_id]
    topic_label = topic_row['Name'].values[0] if len(topic_row) > 0 and 'Name' in topic_row.columns else f"Topic {topic_id}"
    
    print(f"[{i}/{len(topics_to_process)}] Topic {topic_id}: {topic_label} ({len(topic_articles)} articles, sampling {sample_size})")
    
    # Create prompt with sampled articles
    articles_text = "\n\n".join([
        f"Article {j+1}: {article['title']}\nSummary: {article['summary'][:500]}"
        for j, article in enumerate(sampled_articles)
    ])
    
    user_prompt = f"""Topic Label: {topic_label}
Topic Keywords: {keyword_str}
Number of articles in topic: {len(topic_articles)}

Sample Articles (30 random samples):
{articles_text}

Based on these articles, provide a comprehensive 2-3 paragraph description of what this topic is about in the context of content discoverability. Be specific and insightful."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )
        
        description = response.choices[0].message.content.strip()
        
        topic_descriptions[int(topic_id)] = {
            'topic_id': int(topic_id),
            'label': topic_label,
            'keywords': keyword_str,
            'article_count': len(topic_articles),
            'description': description,
            'sample_size': sample_size
        }
        
        print(f"  ✓ Generated description ({len(description)} chars)")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        topic_descriptions[int(topic_id)] = {
            'topic_id': int(topic_id),
            'label': topic_label,
            'keywords': keyword_str,
            'article_count': len(topic_articles),
            'description': 'Error generating description',
            'sample_size': sample_size
        }

# Save descriptions
print(f"\n[STEP 4] Saving descriptions...")
with open(OUTPUT_PATH, 'w') as f:
    json.dump(topic_descriptions, f, indent=2)

print(f"✓ Saved to {OUTPUT_PATH}")

# Summary
print("\n" + "="*70)
print("DESCRIPTION GENERATION COMPLETE")
print("="*70)
print(f"\nTopics processed: {len(topic_descriptions)}")
print(f"Output file: {OUTPUT_PATH}")
print(f"\nSample descriptions:")
print("-"*70)
for topic_id in list(topic_descriptions.keys())[:3]:
    desc = topic_descriptions[topic_id]
    print(f"\n{desc['label']} ({desc['article_count']} articles):")
    print(f"{desc['description'][:200]}...")

print("\n" + "="*70)
print("Next step: Restart dashboard to see descriptions")
print("  streamlit run dashboard.py")
print("="*70)

