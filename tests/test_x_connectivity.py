import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from zimbra.adapters.x_api import XAdapter

def main():
    print("Loading environment variables...")
    load_dotenv()
    
    token = os.getenv("X_BEARER_TOKEN", "")
    if not token:
        print("Error: X_BEARER_TOKEN is not set in the environment or .env file.")
        sys.exit(1)
        
    print(f"X Bearer Token found: {token[:15]}... (Length: {len(token)})")
    
    print("\nInitializing XAdapter...")
    adapter = XAdapter()
    
    query = "$BTC OR $ETH OR crypto lang:en"
    print(f"Fetching posts with query: '{query}'...")
    
    try:
        posts = adapter.fetch(target=query, limit=5)
        print(f"\nSuccess! Successfully fetched {len(posts)} posts from X API.")
        for idx, post in enumerate(posts, 1):
            # Safely encode/decode to console encoding to prevent charmap/Unicode errors
            enc = sys.stdout.encoding or 'utf-8'
            author_safe = post.author.encode(enc, errors='replace').decode(enc)
            text_safe = post.text.encode(enc, errors='replace').decode(enc)
            
            print(f"\n--- Post {idx} ---")
            print(f"Author: {author_safe}")
            print(f"Created: {post.created_utc}")
            print(f"Likes: {post.likes} | Replies: {post.replies}")
            print(f"Text:\n{text_safe}")
            print(f"URL: {post.url}")
    except Exception as e:
        print(f"\nError running X connectivity test: {e}")

if __name__ == "__main__":
    main()
