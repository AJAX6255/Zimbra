import hashlib
import requests
from datetime import datetime, timezone
from typing import List
from bs4 import BeautifulSoup
from zimbra.adapters.base import BaseAdapter
from zimbra.config import DEFAULT_USER_AGENT
from zimbra.models import PostRecord

class YahooAdapter(BaseAdapter):
    def fetch(self, target: str, limit: int = 20, **kwargs) -> List[PostRecord]:
        """Fetch posts from a Yahoo Finance board URL by crawling HTML.
        
        :param target: Yahoo board URL (e.g. 'https://finance.yahoo.com/quote/AAPL/community')
        :param limit: Maximum posts to extract (default: 20)
        :return: List of PostRecord
        """
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        res = requests.get(target, headers=headers, timeout=20)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        texts = []
        for tag in soup.find_all(["p", "li", "span"]):
            txt = tag.get_text(" ", strip=True)
            if len(txt.split()) >= 8:
                texts.append(txt)
                
        posts = []
        for i, txt in enumerate(texts[:limit]):
            posts.append(PostRecord(
                source="yahoo",
                platform_entity=target,
                post_id=f"yahoo_{hashlib.md5((target+txt).encode()).hexdigest()[:12]}",
                author=f"anon_{i}",
                created_utc=datetime.now(timezone.utc),
                text=txt,
                thread_id=f"yahoo_thread_{i}",
                thread_title="Yahoo Finance board scrape",
                url=target,
            ))
        return posts
