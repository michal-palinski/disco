from serpapi import GoogleSearch
import sqlite3
import json
from datetime import datetime, timedelta
import re
from dateutil import parser

def parse_relative_date(date_string):
    """
    Parse both absolute dates and relative dates like '1 month ago', '2 days ago', etc.
    Returns a datetime object or None if parsing fails.
    """
    if not date_string:
        return None
    
    # Try to parse as absolute date first
    try:
        return parser.parse(date_string)
    except:
        pass
    
    # Parse relative dates
    now = datetime.now()
    date_string_lower = date_string.lower().strip()
    
    # Pattern: "X time_unit ago"
    patterns = [
        (r'(\d+)\s*second[s]?\s*ago', 'seconds'),
        (r'(\d+)\s*minute[s]?\s*ago', 'minutes'),
        (r'(\d+)\s*hour[s]?\s*ago', 'hours'),
        (r'(\d+)\s*day[s]?\s*ago', 'days'),
        (r'(\d+)\s*week[s]?\s*ago', 'weeks'),
        (r'(\d+)\s*month[s]?\s*ago', 'months'),
        (r'(\d+)\s*year[s]?\s*ago', 'years'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, date_string_lower)
        if match:
            amount = int(match.group(1))
            if unit == 'seconds':
                return now - timedelta(seconds=amount)
            elif unit == 'minutes':
                return now - timedelta(minutes=amount)
            elif unit == 'hours':
                return now - timedelta(hours=amount)
            elif unit == 'days':
                return now - timedelta(days=amount)
            elif unit == 'weeks':
                return now - timedelta(weeks=amount)
            elif unit == 'months':
                # Approximate: 30 days per month
                return now - timedelta(days=amount * 30)
            elif unit == 'years':
                # Approximate: 365 days per year
                return now - timedelta(days=amount * 365)
    
    # Handle special cases
    if 'yesterday' in date_string_lower:
        return now - timedelta(days=1)
    elif 'today' in date_string_lower or 'just now' in date_string_lower:
        return now
    
    # If all else fails, return None
    return None

# Database setup
conn = sqlite3.connect('innovation_radar.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT UNIQUE,
        source TEXT,
        date TEXT,
        snippet TEXT,
        query TEXT,
        search_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Add search_type column if it doesn't exist (for existing databases)
try:
    cursor.execute('ALTER TABLE search_results ADD COLUMN search_type TEXT')
    conn.commit()
    print("Added search_type column to existing table")
except sqlite3.OperationalError:
    pass  # Column already exists

# Update existing records without search_type to 'news'
cursor.execute("UPDATE search_results SET search_type = 'news' WHERE search_type IS NULL")
conn.commit()

def run_search(search_params, search_type, results_key='news_results'):
    """
    Run a search with pagination and save results to database
    
    Args:
        search_params: Dictionary of search parameters
        search_type: String identifier for the type of search ('news' or 'all')
        results_key: Key to extract results from response ('news_results' or 'organic_results')
    """
    new_count = 0
    duplicate_count = 0
    total_pages_fetched = 0
    
    print(f"\n{'='*50}")
    print(f"Starting {search_type.upper()} search with pagination...")
    print(f"{'='*50}\n")
    
    # Loop through pages using SerpAPI's pagination
    current_page = 1
    while True:
        print(f"--- Fetching page {current_page} ({search_type}) ---")
        
        try:
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            # Check if we have results
            if results_key not in results or len(results[results_key]) == 0:
                print(f"No more results found on page {current_page}. Stopping pagination.")
                break
            
            page_results = results[results_key]
            total_pages_fetched += 1
            
            # Process and save results
            for article in page_results:
                title = article.get('title', '')
                link = article.get('link', '')
                source = article.get('source', {}).get('name', '') if isinstance(article.get('source'), dict) else article.get('source', '')
                date_string = article.get('date', '')
                snippet = article.get('snippet', '')
                
                # Parse the date
                parsed_date = parse_relative_date(date_string)
                # Store as ISO format string if parsed successfully, otherwise store original
                date_to_store = parsed_date.isoformat() if parsed_date else date_string
                
                try:
                    cursor.execute('''
                        INSERT INTO search_results (title, link, source, date, snippet, query, search_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (title, link, source, date_to_store, snippet, search_params['q'], search_type))
                    conn.commit()
                    new_count += 1
                    print(f"✓ Added: {title[:60]}... (Date: {date_string} → {date_to_store})")
                except sqlite3.IntegrityError:
                    duplicate_count += 1
                    print(f"⊗ Duplicate: {title[:60]}...")
            
            print(f"Page {current_page} processed: {len(page_results)} results\n")
            
            # Check for next page using SerpAPI's pagination field
            serpapi_pagination = results.get('serpapi_pagination', {})
            
            # Check if there's a next page available
            if serpapi_pagination.get('next'):
                # Increment the start parameter for next page
                current_start = search_params.get('start', 0)
                search_params['start'] = current_start + 10
                current_page += 1
                print(f"Moving to next page (start={search_params['start']})...\n")
            else:
                print("No more pages available from SerpAPI. Reached end of results.")
                break
            
        except Exception as e:
            print(f"Error fetching page {current_page}: {e}")
            break
    
    # Summary for this search type
    print(f"\n--- {search_type.upper()} Search Summary ---")
    print(f"Pages fetched: {total_pages_fetched}")
    print(f"New articles saved: {new_count}")
    print(f"Duplicates skipped: {duplicate_count}")
    
    return new_count, duplicate_count, total_pages_fetched


# Search 1: News Results
news_params = {
    "api_key": "dca593d02852cd75549de8a759553d42e2ffac2f65e907e3e6e3a3a74c05c222",
    "engine": "google",
    "q": "(discoverability AND culture) OR (discoverability AND creative) OR (discoverability AND content)",
    "location": "Warsaw, Masovian Voivodeship, Poland",
    "google_domain": "google.pl",
    "gl": "pl",
    "hl": "en",
    "tbm": "nws",  # News search
    "start": 0
}

news_new, news_dup, news_pages = run_search(news_params, 'news', 'news_results')

# Search 2: All Results (organic search)
all_params = {
    "api_key": "dca593d02852cd75549de8a759553d42e2ffac2f65e907e3e6e3a3a74c05c222",
    "engine": "google",
    "q": "(discoverability AND culture) OR (discoverability AND creative) OR (discoverability AND content)",
    "location": "Warsaw, Masovian Voivodeship, Poland",
    "google_domain": "google.pl",
    "gl": "pl",
    "hl": "en",
    # No tbm parameter - searches all results
    "start": 0
}

all_new, all_dup, all_pages = run_search(all_params, 'all', 'organic_results')

# Final summary
print(f"\n{'='*60}")
print(f"--- FINAL SUMMARY (ALL SEARCHES) ---")
print(f"{'='*60}")
print(f"\nNEWS Search:")
print(f"  Pages fetched: {news_pages}")
print(f"  New articles: {news_new}")
print(f"  Duplicates: {news_dup}")
print(f"\nALL Search:")
print(f"  Pages fetched: {all_pages}")
print(f"  New articles: {all_new}")
print(f"  Duplicates: {all_dup}")
print(f"\nTOTAL:")
print(f"  Combined new articles: {news_new + all_new}")
print(f"  Combined duplicates: {news_dup + all_dup}")
print(f"  Total in database: {cursor.execute('SELECT COUNT(*) FROM search_results').fetchone()[0]}")
print(f"{'='*60}")

conn.close()
