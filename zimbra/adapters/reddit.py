import time
import requests
from datetime import datetime, timezone
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from zimbra.adapters.base import BaseAdapter
from zimbra.config import REDDIT_USER_AGENT
from zimbra.models import PostRecord

class RedditAdapter(BaseAdapter):
    def fetch(self, target: str, limit: int = 50, **kwargs) -> List[PostRecord]:
        """Fetch posts from a subreddit using either the public Arctic Shift API or public JSON scraper fallback.
        
        :param target: Subreddit name (e.g., 'wallstreetbets')
        :param limit: Maximum number of posts to fetch (default: 50)
        :param query: Optional keyword search filter (passed in kwargs)
        :param after: Optional UNIX timestamp start date filter (passed in kwargs)
        :param before: Optional UNIX timestamp end date filter (passed in kwargs)
        :return: List of PostRecord
        """
        user_agent = kwargs.get("user_agent") or REDDIT_USER_AGENT
        query = kwargs.get("query")
        after = kwargs.get("after")
        before = kwargs.get("before")
        
        # 1. Try Arctic Shift API (Public JSON API) as Tier 1 / Scraper Fallback
        try:
            print("Using Arctic Shift public Reddit API...")
            session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("https://", adapter)
            session.headers.update({
                "User-Agent": user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
            })
            
            posts = []
            current_before = before
            remaining = limit
            
            while remaining > 0:
                batch_limit = min(remaining, 100)
                url = f"https://arctic-shift.photon-reddit.com/api/posts/search?subreddit={target}&limit={batch_limit}"
                if query:
                    url += f"&query={query}"
                if after:
                    url += f"&after={after}"
                if current_before:
                    url += f"&before={current_before}"
                    
                res = session.get(url, timeout=20)
                res.raise_for_status()
                data = res.json()
                
                batch_posts = []
                data_list = data.get("data")
                if not isinstance(data_list, list):
                    break
                    
                for p in data_list:
                    created_utc_val = p.get("created_utc", time.time())
                    created = datetime.fromtimestamp(created_utc_val, tz=timezone.utc)
                    title = p.get("title", "")
                    body = p.get("selftext", "")
                    text = f"{title}\n{body}".strip()
                    if not text:
                        continue
                    
                    batch_posts.append(PostRecord(
                        source="reddit",
                        platform_entity=target,
                        post_id=f"reddit_{p.get('id')}",
                        author=p.get("author", "unknown"),
                        created_utc=created,
                        text=text,
                        thread_id=f"reddit_thread_{p.get('id')}",
                        thread_title=title,
                        likes=float(p.get("ups", 0) or 0),
                        replies=float(p.get("num_comments", 0) or 0),
                        url=f"https://www.reddit.com{p.get('permalink','')}",
                    ))
                
                if not batch_posts:
                    break
                    
                posts.extend(batch_posts)
                remaining -= len(batch_posts)
                
                if len(data_list) < batch_limit:
                    break
                
                # Get the oldest post created_utc in data_list
                utcs = [p.get("created_utc") for p in data_list if p.get("created_utc")]
                if not utcs:
                    break
                oldest_post_utc = min(utcs)
                
                # If oldest_post_utc is not decreasing, break to prevent infinite loop
                if current_before and oldest_post_utc >= current_before:
                    break
                current_before = int(oldest_post_utc)
                
                # Small sleep to be nice to the API
                time.sleep(0.5)
                
            if posts:
                return posts[:limit]
        except Exception as e:
            print(f"Arctic Shift API failed, falling back to standard requests scraper: {e}")

        # 2. Fall back to requests-based JSON scraper with retries and backoff
        print("Using requests-based public JSON scraper fallback with retries & backoff...")
        session = requests.Session()
        retry = Retry(
            total=3, 
            backoff_factor=1, 
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        if query:
            url = f"https://www.reddit.com/r/{target}/search.json?q={query}&restrict_sr=on&limit={limit}&sort=new"
        else:
            url = f"https://www.reddit.com/r/{target}/hot.json?limit={limit}"
            
        res = session.get(url, timeout=20)
        res.raise_for_status()
        
        data = res.json()
        posts = []
        data_dict = data if isinstance(data, dict) else {}
        inner_data = data_dict.get("data", {})
        children = inner_data.get("children", []) if isinstance(inner_data, dict) else []
        for child in children:
            p = child.get("data", {}) if isinstance(child, dict) else {}
            created_utc_val = p.get("created_utc", time.time())
            created = datetime.fromtimestamp(created_utc_val, tz=timezone.utc)
            title = p.get("title", "")
            body = p.get("selftext", "")
            text = f"{title}\n{body}".strip()
            if not text:
                continue
            
            posts.append(PostRecord(
                source="reddit",
                platform_entity=target,
                post_id=f"reddit_{p.get('id')}",
                author=p.get("author", "unknown"),
                created_utc=created,
                text=text,
                thread_id=f"reddit_thread_{p.get('id')}",
                thread_title=title,
                likes=float(p.get("ups", 0) or 0),
                replies=float(p.get("num_comments", 0) or 0),
                url=f"https://www.reddit.com{p.get('permalink','')}",
            ))
        return posts
