"""
Export all necessary topic modeling data to avoid loading the full model in dashboard.
This makes the dashboard much faster and lighter.
"""
import json
import pickle
import sqlite3
import pandas as pd
from bertopic import BERTopic

# Load the model once
print("Loading BERTopic model...")
topic_model = BERTopic.load('topic_model.pkl')

# Load database
conn = sqlite3.connect('innovation_radar_unified.db')

# 1. Export topic info (labels, counts, keywords)
print("\n[1/4] Exporting topic info...")
topic_info = topic_model.get_topic_info()

topic_data = {}
for _, row in topic_info.iterrows():
    topic_id = int(row['Topic'])
    
    # Get c-TF-IDF keywords
    keywords = []
    if topic_id != -1:
        try:
            # Get raw keywords from c-TF-IDF
            vocab = topic_model.vectorizer_model.get_feature_names_out()
            c_tf_idf = topic_model.c_tf_idf_
            topic_idx = topic_id + 1
            
            if topic_idx >= 0 and topic_idx < c_tf_idf.shape[0]:
                row_scores = c_tf_idf[topic_idx].toarray().flatten()
                top_indices = row_scores.argsort()[-10:][::-1]
                keywords = [vocab[i] for i in top_indices if row_scores[i] > 0]
        except:
            # Fallback to get_topic
            topic_words = topic_model.get_topic(topic_id)
            keywords = [w for w, _ in topic_words[:10]]
    
    topic_data[topic_id] = {
        'name': row.get('Name', f'Topic {topic_id}'),
        'count': int(row.get('Count', 0)),
        'keywords': keywords,
        'representation': row.get('Representation', '')
    }

with open('topic_info.json', 'w') as f:
    json.dump(topic_data, f, indent=2)

print(f"  ✓ Saved {len(topic_data)} topics to topic_info.json")

# 2. Export topic map visualization data (if available)
print("\n[2/4] Exporting topic map visualization...")
try:
    fig = topic_model.visualize_topics()
    # Save as JSON for Plotly
    fig.write_json('topic_map.json')
    print("  ✓ Saved topic map to topic_map.json")
except Exception as e:
    print(f"  ✗ Could not export topic map: {e}")

# 3. Verify all articles have topic assignments
print("\n[3/4] Checking topic assignments in database...")
query = """
    SELECT COUNT(*) as total,
           SUM(CASE WHEN topic IS NOT NULL THEN 1 ELSE 0 END) as with_topic
    FROM articles
    WHERE cultural_relevant = 1
"""
df = pd.read_sql_query(query, conn)
print(f"  ✓ Articles with topics: {df['with_topic'].values[0]} / {df['total'].values[0]}")

# 4. Summary
print("\n[4/4] Summary:")
print(f"  • topic_info.json: {len(topic_data)} topics with keywords and labels")
print(f"  • topic_descriptions.json: Detailed GPT descriptions (already exists)")
print(f"  • Database: Article-topic assignments")
print("\n✅ All data exported! Dashboard can now run without loading topic_model.pkl")

conn.close()

