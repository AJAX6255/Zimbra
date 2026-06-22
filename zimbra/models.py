from dataclasses import dataclass
from datetime import datetime

@dataclass
class PostRecord:
    source: str
    platform_entity: str
    post_id: str
    author: str
    created_utc: datetime
    text: str
    thread_id: str
    thread_title: str
    likes: float = 0.0
    replies: float = 0.0
    reposts: float = 0.0
    views: float = 0.0
    followers_est: float = 0.0
    author_role_hint: str = "unknown"
    url: str = ""
