# Adapters package init
from zimbra.adapters.base import BaseAdapter
from zimbra.adapters.reddit import RedditAdapter
from zimbra.adapters.x_api import XAdapter
from zimbra.adapters.yahoo import YahooAdapter
from zimbra.adapters.google_news import GoogleNewsAdapter
from zimbra.adapters.coindesk import CoindeskAdapter
from zimbra.adapters.cointelegraph import CointelegraphAdapter
from zimbra.adapters.binance import BinanceAdapter
from zimbra.adapters.commodity import CommodityAdapter
from zimbra.adapters.economic import InflationAdapter

__all__ = [
    "BaseAdapter", 
    "RedditAdapter", 
    "XAdapter", 
    "YahooAdapter", 
    "GoogleNewsAdapter",
    "CoindeskAdapter",
    "CointelegraphAdapter",
    "BinanceAdapter",
    "CommodityAdapter",
    "InflationAdapter"
]
