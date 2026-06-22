import requests
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import email.utils
from typing import List
from urllib.parse import quote

from zimbra.adapters.base import BaseAdapter
from zimbra.models import PostRecord
from zimbra.config import DEFAULT_USER_AGENT

class CoindeskAdapter(BaseAdapter):
    def fetch(self, target: str, limit: int = 50, **kwargs) -> List[PostRecord]:
        """Fetch news articles from CoinDesk tag RSS feed.
        
        :param target: Search tag (e.g. 'ethereum')
        :param limit: Max articles to return (up to 50)
        :return: List of PostRecord
        """
        user_agent = kwargs.get("user_agent") or DEFAULT_USER_AGENT
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/xml, text/xml, */*",
        }
        
        # Format tag name
        tag = target.lower().strip()
        if tag == "ether":
            tag = "ethereum"
            
        url = f"https://www.coindesk.com/arc/outboundfeeds/rss/tag/{tag}/"
        
        posts = []
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200:
                # Fallback to main feed if tag feed fails
                url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
                res = requests.get(url, headers=headers, timeout=20)
                res.raise_for_status()
            
            root = ET.fromstring(res.content)
            items = root.findall(".//item")
            
            for item in items[:limit]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                desc_elem = item.find("description")
                creator_elem = item.find("{http://purl.org/dc/elements/1.1/}creator")
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                desc = desc_elem.text if desc_elem is not None else ""
                author = creator_elem.text if creator_elem is not None else "CoinDesk"
                
                # Parse pubDate
                created_utc = datetime.now(timezone.utc)
                if pub_date_elem is not None and pub_date_elem.text:
                    try:
                        created_utc = email.utils.parsedate_to_datetime(pub_date_elem.text)
                    except Exception:
                        pass
                
                from bs4 import BeautifulSoup
                desc_clean = desc
                if desc:
                    try:
                        desc_clean = BeautifulSoup(desc, "html.parser").get_text(" ", strip=True)
                    except Exception:
                        pass
                
                text = f"{title}\n{desc_clean}".strip()
                if not text:
                    continue
                
                post_id = f"coindesk_{hashlib.md5(link.encode('utf-8', errors='ignore')).hexdigest()[:16]}"
                
                posts.append(PostRecord(
                    source="coindesk",
                    platform_entity=tag,
                    post_id=post_id,
                    author=author,
                    created_utc=created_utc,
                    text=text,
                    thread_id=post_id,
                    thread_title=title,
                    url=link
                ))
                
        except Exception as e:
            print(f"Error fetching from CoinDesk RSS: {e}")
            
        return posts
