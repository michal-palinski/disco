"""
Run BERTopic on article summaries with:
- Voyage AI embeddings (voyage-3.5-lite)
- OpenAI GPT for topic representation
"""
import sqlite3
import pickle
import os
from dotenv import load_dotenv
from bertopic import BERTopic
from bertopic.representation import OpenAI as OpenAIRepresentation
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import numpy as np
import voyageai
from openai import OpenAI

# Load environment variables
load_dotenv()

DB_PATH = 'innovation_radar_unified.db'
MODEL_PATH = 'topic_model.pkl'
TOPICS_CSV = 'topics_data.csv'
EMBEDDINGS_PATH = 'embeddings.npy'

# Check API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env file")
    exit(1)

if not VOYAGE_API_KEY:
    print("ERROR: VOYAGE_API_KEY not found in .env file")
    print("Get your API key at: https://www.voyageai.com/")
    exit(1)

print("="*70)
print("RUNNING BERTOPIC WITH VOYAGE EMBEDDINGS + GPT")
print("="*70)
print(f"  Embeddings: Voyage AI (voyage-3.5-lite)")
print(f"  Topic Labels: OpenAI GPT (gpt-5-mini)")
print("="*70)

# Initialize clients
voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Load data from database
print("\n[STEP 1] Loading summaries from database...")
conn = sqlite3.connect(DB_PATH)

query = """
    SELECT id, title, summary, url, source, date, search_type
    FROM articles 
    WHERE summary IS NOT NULL 
      AND summary != ''
      AND LENGTH(summary) > 50
      AND (cultural_relevant = 1 OR cultural_relevant IS NULL)
    ORDER BY date DESC
"""
# Note: cultural_relevant IS NULL means not yet filtered (keep for backward compatibility)

df = pd.read_sql_query(query, conn)
conn.close()

print(f"✓ Loaded {len(df)} articles with summaries")

if len(df) < 10:
    print("\n✗ Not enough summaries to run topic modeling")
    print("Run summarization first: python summarize_batch_process.py")
    exit(1)

# Prepare documents
documents = df['summary'].tolist()
print(f"\n[STEP 2] Preparing {len(documents)} documents...")

# Generate embeddings with Voyage AI
print("\n[STEP 3] Generating embeddings with Voyage AI...")
print("  Model: voyage-3.5-lite")
print("  This may take a few minutes...")

# Check if embeddings already exist
if os.path.exists(EMBEDDINGS_PATH):
    print(f"  Loading cached embeddings from {EMBEDDINGS_PATH}...")
    embeddings = np.load(EMBEDDINGS_PATH)
    if len(embeddings) != len(documents):
        print(f"  ⚠ Cached embeddings size mismatch, regenerating...")
        embeddings = None
    else:
        print(f"  ✓ Loaded {len(embeddings)} cached embeddings")
else:
    embeddings = None

if embeddings is None:
    # Generate embeddings in batches (Voyage has rate limits)
    batch_size = 128
    all_embeddings = []
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        print(f"  Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
        
        result = voyage_client.embed(
            texts=batch,
            model="voyage-3.5-lite",
            input_type="document"
        )
        all_embeddings.extend(result.embeddings)
    
    embeddings = np.array(all_embeddings)
    
    # Cache embeddings
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"  ✓ Saved embeddings to {EMBEDDINGS_PATH}")

print(f"✓ Generated {len(embeddings)} embeddings (dim: {embeddings.shape[1]})")

# Configure OpenAI representation model
print("\n[STEP 4] Configuring GPT topic representation...")

# Custom prompt for discoverability-focused topics
representation_prompt = """
I have a topic that contains the following documents:
[DOCUMENTS]

The topic is described by the following keywords: [KEYWORDS]

Based on the documents and keywords, create a short, descriptive label for this topic.
Focus on discoverability, content discovery, and media/creative industries themes.
The label should be 2-5 words, clear and specific.

Topic label:"""

representation_model = OpenAIRepresentation(
    client=openai_client,
    model="gpt-5-mini",
    prompt=representation_prompt,
    nr_docs=30,
    chat=True
)

# Configure BERTopic
print("\n[STEP 5] Training BERTopic model...")
print("  This may take 5-10 minutes...")

vectorizer_model = CountVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))

# Initialize BERTopic with pre-computed embeddings
topic_model = BERTopic(
    vectorizer_model=vectorizer_model,
    representation_model=representation_model,
    min_topic_size=10,
    nr_topics="auto",
    calculate_probabilities=False,
    verbose=True
)

# Fit the model with pre-computed embeddings
topics, probs = topic_model.fit_transform(documents, embeddings)

print(f"\n✓ Model trained!")
print(f"  Found {len(set(topics)) - 1} topics (excluding outliers)")

# Add topics to dataframe
df['topic'] = topics

# Get topic info with GPT-generated labels
topic_info = topic_model.get_topic_info()
print(f"\n[STEP 6] Topic Distribution (with GPT labels):")
print("-"*70)
for idx, row in topic_info.head(15).iterrows():
    if row['Topic'] != -1:
        # Get the GPT-generated name
        topic_name = row.get('Name', row.get('CustomName', ''))
        if not topic_name:
            topic_words = ', '.join([word for word, _ in topic_model.get_topic(row['Topic'])[:3]])
            topic_name = topic_words
        print(f"  Topic {row['Topic']}: {topic_name} ({row['Count']} docs)")

# Save model
print(f"\n[STEP 7] Saving model and results...")

# Remove unpicklable objects before saving
if hasattr(topic_model, 'representation_model'):
    if hasattr(topic_model.representation_model, 'client'):
        topic_model.representation_model.client = None

# Save using BERTopic's built-in method (safer than pickle)
topic_model.save(MODEL_PATH, serialization="pickle", save_ctfidf=True, save_embedding_model=False)
print(f"✓ Saved model to {MODEL_PATH}")

# Save topics data
df['topic_name'] = df['topic'].apply(
    lambda x: topic_model.get_topic_info()[topic_model.get_topic_info()['Topic'] == x]['Name'].values[0] 
    if x in topic_model.get_topic_info()['Topic'].values else 'Outlier'
)
df.to_csv(TOPICS_CSV, index=False)
print(f"✓ Saved topics data to {TOPICS_CSV}")

# Update database with topic assignments
print(f"\n[STEP 8] Updating database with topic assignments...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add topic column if it doesn't exist
try:
    cursor.execute('ALTER TABLE articles ADD COLUMN topic INTEGER')
    conn.commit()
except sqlite3.OperationalError:
    pass

# Update topics
for idx, row in df.iterrows():
    cursor.execute("""
        UPDATE articles 
        SET topic = ?
        WHERE id = ?
    """, (int(row['topic']), int(row['id'])))

conn.commit()
conn.close()
print(f"✓ Updated database with topic assignments")

# Step 9: Analyze topics for potential merging
print(f"\n[STEP 9] Analyzing topics for potential merging...")
print("-"*70)

merge_suggestions_path = 'topic_merge_suggestions.txt'

try:
    # Get topic info for merging analysis
    topic_info = topic_model.get_topic_info()
    topics_for_analysis = topic_info[topic_info['Topic'] != -1]
    
    if len(topics_for_analysis) > 1:
        # Create topic summary for GPT
        topic_summary = []
        for _, row in topics_for_analysis.iterrows():
            topic_id = row['Topic']
            topic_name = row.get('Name', f"Topic {topic_id}")
            topic_count = row['Count']
            keywords = ', '.join([word for word, _ in topic_model.get_topic(topic_id)[:8]])
            topic_summary.append(f"Topic {topic_id} ({topic_count} articles): {topic_name}\n  Keywords: {keywords}")
        
        topics_text = "\n\n".join(topic_summary)
        
        merge_prompt = f"""You are analyzing topics from a BERTopic model about content discoverability.

Topics identified:
{topics_text}

Task: Identify topics that should potentially be MERGED because they are too similar or represent the same theme.

Guidelines:
- Only suggest merging if topics are clearly overlapping
- Consider keywords, topic names, and article counts
- Smaller topics (<20 articles) are good candidates for merging with larger similar topics
- Don't merge if topics have distinct meanings even if keywords overlap slightly

Provide your analysis in this format:
MERGE: Topic X + Topic Y → Reason
MERGE: Topic A + Topic B + Topic C → Reason

If no merges are needed, write: NO MERGES RECOMMENDED"""
        
        response = openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": "You are an expert in topic modeling and content analysis."},
                {"role": "user", "content": merge_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        merge_suggestions = response.choices[0].message.content.strip()
        
        # Save suggestions
        with open(merge_suggestions_path, 'w') as f:
            f.write("TOPIC MERGE SUGGESTIONS\n")
            f.write("="*70 + "\n\n")
            f.write("Generated by GPT-5.2 based on topic analysis\n\n")
            f.write(merge_suggestions)
            f.write("\n\n" + "="*70 + "\n")
            f.write("To merge topics manually, use BERTopic's merge_topics() method\n")
        
        print(f"✓ Saved merge suggestions to {merge_suggestions_path}")
        print("\nMerge Suggestions Preview:")
        print("-"*70)
        print(merge_suggestions[:500] + ("..." if len(merge_suggestions) > 500 else ""))
    else:
        print("  Only 1 topic found, no merging needed")

except Exception as e:
    print(f"✗ Error analyzing topics for merging: {e}")

# Summary
print("\n" + "="*70)
print("TOPIC MODELING COMPLETE")
print("="*70)
print(f"\nConfiguration:")
print(f"  - Embeddings: Voyage AI voyage-3.5-lite")
print(f"  - Topic Labels: OpenAI gpt-5-mini (or gpt-4o-mini)")
print(f"  - Cultural filtering: Only culturally relevant articles")
print(f"\nResults:")
print(f"  - Total articles analyzed: {len(df)}")
print(f"  - Topics discovered: {len(set(topics)) - 1}")
print(f"  - Outliers: {sum(1 for t in topics if t == -1)}")
print(f"\nFiles created:")
print(f"  - {MODEL_PATH} (BERTopic model)")
print(f"  - {TOPICS_CSV} (Topics data with labels)")
print(f"  - {EMBEDDINGS_PATH} (Cached Voyage embeddings)")
print(f"  - {merge_suggestions_path} (Topic merge suggestions)")
print(f"\nNext steps:")
print(f"  1. Review topic merge suggestions: cat {merge_suggestions_path}")
print(f"  2. Generate topic descriptions: python generate_topic_descriptions.py")
print(f"  3. Run dashboard: streamlit run dashboard.py")
print("="*70)
