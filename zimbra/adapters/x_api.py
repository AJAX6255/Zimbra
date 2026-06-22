import requests
from datetime import datetime
from typing import List
from zimbra.adapters.base import BaseAdapter
from zimbra.config import X_BEARER_TOKEN
from zimbra.models import PostRecord

class XAdapter(BaseAdapter):
    def fetch(self, target: str, limit: int = 25, **kwargs) -> List[PostRecord]:
        """Fetch tweets matching a query using the official X API v2.
        
        :param target: Search query (e.g. 'AAPL OR $AAPL lang:en')
        :param limit: Maximum tweets to fetch (default: 25)
        :param bearer_token: Optional bearer token override, otherwise uses config
        :return: List of PostRecord
        """
        bearer_token = kwargs.get("bearer_token") or X_BEARER_TOKEN
        if not bearer_token:
            raise ValueError("Provide an X Bearer Token for official API access.")
            
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            "query": target,
            "max_results": max(10, min(limit, 100)),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "public_metrics,username,name"
        }
        res = requests.get("https://api.x.com/2/tweets/search/recent", headers=headers, params=params, timeout=30)
        res.raise_for_status()
        payload = res.json()
        
        users = {u["id"]: u for u in payload.get("includes", {}).get("users", [])}
        posts = []
        for t in payload.get("data", []):
            user = users.get(t.get("author_id"), {})
            metrics = t.get("public_metrics", {})
            created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            author = user.get("username", t.get("author_id", "unknown"))
            
            posts.append(PostRecord(
                source="x",
                platform_entity=target,
                post_id=f"x_{t['id']}",
                author=author,
                created_utc=created,
                text=t.get("text", ""),
                thread_id=f"x_thread_{t['id']}",
                thread_title=target,
                likes=float(metrics.get("like_count", 0)),
                replies=float(metrics.get("reply_count", 0)),
                reposts=float(metrics.get("retweet_count", 0)),
                followers_est=float(user.get("public_metrics", {}).get("followers_count", 0)),
                url=f"https://x.com/{author}/status/{t['id']}",
            ))
        return posts
