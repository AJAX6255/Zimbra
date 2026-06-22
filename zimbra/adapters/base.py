from abc import ABC, abstractmethod
from typing import List
from zimbra.models import PostRecord

class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self, target: str, limit: int = 50, **kwargs) -> List[PostRecord]:
        """Fetch records from the data source.
        
        :param target: Subreddit, search query, or board URL depending on the adapter.
        :param limit: Maximum number of posts to fetch.
        :return: List of PostRecord.
        """
        pass
