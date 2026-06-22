import os
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, timezone
import tempfile

from zimbra.models import PostRecord
from zimbra.adapters.google_news import GoogleNewsAdapter
from zimbra.adapters.coindesk import CoindeskAdapter
from zimbra.adapters.cointelegraph import CointelegraphAdapter
from zimbra.adapters.binance import BinanceAdapter
from zimbra.adapters.commodity import CommodityAdapter
from zimbra.adapters.economic import InflationAdapter
from zimbra.database import init_db, save_prices, load_prices, save_economic_indicators, load_economic_indicators

class TestNewAdapters(unittest.TestCase):
    @patch('requests.get')
    def test_google_news_adapter(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<rss version="2.0">
            <channel>
                <item>
                    <title>ETH hits all time high</title>
                    <link>https://example.com/eth-ath</link>
                    <pubDate>Mon, 22 Jun 2026 12:00:00 GMT</pubDate>
                    <description>Ethereum hits a new high of $10000.</description>
                    <source>CryptoNews</source>
                </item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_response
        
        adapter = GoogleNewsAdapter()
        posts = adapter.fetch(target="ethereum", limit=5)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source, "google_news")
        self.assertEqual(posts[0].thread_title, "ETH hits all time high")
        self.assertEqual(posts[0].author, "CryptoNews")
        self.assertEqual(posts[0].url, "https://example.com/eth-ath")
        self.assertTrue("Ethereum hits a new high" in posts[0].text)

    @patch('requests.get')
    def test_coindesk_adapter(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
            <channel>
                <item>
                    <title>Coindesk Article</title>
                    <link>https://coindesk.com/article</link>
                    <pubDate>Mon, 22 Jun 2026 12:00:00 GMT</pubDate>
                    <description>Coindesk description details.</description>
                    <dc:creator>John Doe</dc:creator>
                </item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_response
        
        adapter = CoindeskAdapter()
        posts = adapter.fetch(target="ethereum", limit=5)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source, "coindesk")
        self.assertEqual(posts[0].author, "John Doe")
        self.assertEqual(posts[0].thread_title, "Coindesk Article")

    @patch('requests.get')
    def test_cointelegraph_adapter(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
            <channel>
                <item>
                    <title>Cointelegraph Article</title>
                    <link>https://cointelegraph.com/article</link>
                    <pubDate>Mon, 22 Jun 2026 12:00:00 GMT</pubDate>
                    <description>Cointelegraph description details.</description>
                    <dc:creator>Alice Smith</dc:creator>
                </item>
            </channel>
        </rss>"""
        mock_get.return_value = mock_response
        
        adapter = CointelegraphAdapter()
        posts = adapter.fetch(target="ethereum", limit=5)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source, "cointelegraph")
        self.assertEqual(posts[0].author, "Alice Smith")
        self.assertEqual(posts[0].thread_title, "Cointelegraph Article")

    @patch('requests.get')
    def test_binance_adapter(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [
                1700000000000, # Open time
                "3500.00",     # Open
                "3600.00",     # High
                "3400.00",     # Low
                "3550.00",     # Close
                "1000.00",     # Volume
                1700086399999, # Close time
                # ...
            ]
        ]
        mock_get.return_value = mock_response
        
        adapter = BinanceAdapter()
        prices = adapter.fetch(target="ETHUSDT", limit=5)
        
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0]["symbol"], "ETHUSDT")
        self.assertEqual(prices[0]["close"], 3550.00)
        self.assertEqual(prices[0]["volume"], 1000.00)

    @patch('yfinance.Ticker')
    def test_commodity_adapter(self, mock_ticker_class):
        mock_ticker = MagicMock()
        mock_df = pd.DataFrame({
            "Open": [2300.0],
            "High": [2350.0],
            "Low": [2280.0],
            "Close": [2320.0],
            "Volume": [500.0]
        }, index=[pd.Timestamp("2026-06-22")])
        mock_ticker.history.return_value = mock_df
        mock_ticker_class.return_value = mock_ticker
        
        adapter = CommodityAdapter()
        prices = adapter.fetch(target="gold", limit=5)
        
        self.assertEqual(len(prices), 1)
        self.assertEqual(prices[0]["symbol"], "GC=F")
        self.assertEqual(prices[0]["close"], 2320.0)
        self.assertEqual(prices[0]["timestamp"], "2026-06-22")

    @patch('pandas.read_html')
    def test_inflation_adapter(self, mock_read_html):
        mock_df = pd.DataFrame({
            "Year": [2026],
            "Jan": ["3.1%"],
            "Feb": ["3.2%"],
            "Mar": ["3.0%"],
            "Apr": ["3.4%"],
            "May": ["3.3%"],
            "Jun": ["3.5%"],
            "Jul": ["3.1%"],
            "Aug": ["3.2%"],
            "Sep": ["3.0%"],
            "Oct": ["3.2%"],
            "Nov": ["3.1%"],
            "Dec": ["3.3%"],
            "Annual": ["3.2%"]
        })
        mock_read_html.return_value = [mock_df]
        
        adapter = InflationAdapter()
        indicators = adapter.fetch(target="us")
        
        self.assertTrue(len(indicators) > 0)
        self.assertEqual(indicators[0]["indicator_name"], "US_INFLATION")
        self.assertEqual(indicators[0]["year"], 2026)
        jan_record = [ind for ind in indicators if ind["month"] == 1][0]
        self.assertEqual(jan_record["value"], 3.1)

    def test_database_extensions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_market_ext.db")
            init_db(db_path)
            
            prices_data = [
                {
                    "symbol": "BTCUSDT",
                    "timestamp": "2026-06-22",
                    "open": 65000.0,
                    "high": 66000.0,
                    "low": 64000.0,
                    "close": 65500.0,
                    "volume": 2000.0
                }
            ]
            save_prices(prices_data, db_path)
            df_prices = load_prices("BTCUSDT", db_path)
            self.assertFalse(df_prices.empty)
            self.assertEqual(len(df_prices), 1)
            self.assertEqual(df_prices.iloc[0]["close"], 65500.0)
            
            economic_data = [
                {
                    "indicator_name": "US_INFLATION",
                    "year": 2026,
                    "month": 6,
                    "value": 3.2
                }
            ]
            save_economic_indicators(economic_data, db_path)
            df_economic = load_economic_indicators("US_INFLATION", db_path)
            self.assertFalse(df_economic.empty)
            self.assertEqual(len(df_economic), 1)
            self.assertEqual(df_economic.iloc[0]["value"], 3.2)
