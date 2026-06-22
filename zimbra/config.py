import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "market_forum_data.db"))

# X (Twitter) API Configuration
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")

# HTTP Scraping Settings
DEFAULT_USER_AGENT = os.getenv(
    "DEFAULT_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# Reddit API Configuration (Public Endpoints)
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "windows:zimbra.sentiment.analyzer:v1.0.0 (by /u/zimbrabot)")

# Supported platforms
SUPPORTED_SOURCES = {
    "reddit": "Reddit via JSON or Arctic Shift",
    "x": "X via official API",
    "yahoo": "Yahoo Finance / public board pages when accessible",
    "discord": "Discord via bot-connected servers and channels",
    "rss": "RSS / news feeds",
    "google_news": "Google News RSS",
    "coindesk": "CoinDesk RSS",
    "cointelegraph": "CoinTelegraph RSS",
    "binance": "Binance Price (BTC/ETH)",
    "commodity": "Commodity Price (Gold/Silver)",
    "economic": "Inflation Rates (US/EU)",
}

SOURCE_POLICY_NOTES = {
    "reddit": "Preferred for public retail sentiment because Reddit has a clear developer ecosystem and subreddit JSON endpoints exist, though authenticated API access is more robust for production.",
    "x": "Use the official X API only. X pricing is pay-per-use and recent/full-archive search availability depends on plan and credits.",
    "discord": "Only collect from servers and channels where the bot is present and collection is permitted; respect application and route rate limits.",
    "yahoo": "Treat Yahoo boards as optional because public page structure can change and scraping reliability is weaker than Reddit or direct APIs.",
    "google_news": "Fetch search results from Google News XML RSS feed.",
    "coindesk": "Fetch CoinDesk tag RSS feed for crypto-related news.",
    "cointelegraph": "Fetch CoinTelegraph tag RSS feed for crypto-related news.",
    "binance": "Fetch daily OHLCV candlestick data from Binance REST API.",
    "commodity": "Fetch Gold/Silver prices using yfinance ticker data.",
    "economic": "Fetch monthly US/EU historical inflation rates from rateinflation.com.",
}

