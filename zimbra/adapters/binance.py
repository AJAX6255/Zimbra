import requests
from datetime import datetime, timezone
from typing import List

from zimbra.config import DEFAULT_USER_AGENT

class BinanceAdapter:
    def fetch(self, target: str = "ETHUSDT", limit: int = 100, **kwargs) -> List[dict]:
        """Fetch daily OHLCV prices from Binance public REST API.
        
        :param target: Trading pair symbol (e.g., 'ETHUSDT', 'BTCUSDT')
        :param limit: Number of daily data points (default: 100)
        :return: List of price dicts
        """
        symbol = target.upper().strip()
        if symbol not in ["BTCUSDT", "ETHUSDT"]:
            # Default to ETHUSDT if target is just 'eth' or similar
            if "ETH" in symbol or symbol == "ETHER" or symbol == "ETHEREUM":
                symbol = "ETHUSDT"
            elif "BTC" in symbol:
                symbol = "BTCUSDT"
            else:
                symbol = "ETHUSDT"
                
        user_agent = kwargs.get("user_agent") or DEFAULT_USER_AGENT
        headers = {"User-Agent": user_agent}
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": min(limit, 1000)
        }
        
        prices_list = []
        try:
            res = requests.get(url, headers=headers, params=params, timeout=20)
            res.raise_for_status()
            
            data = res.json()
            for kline in data:
                # kline structure:
                # 0: Open time (millisec)
                # 1: Open
                # 2: High
                # 3: Low
                # 4: Close
                # 5: Volume
                open_time_ms = kline[0]
                dt = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
                
                prices_list.append({
                    "symbol": symbol,
                    "timestamp": dt.date().isoformat(),  # YYYY-MM-DD
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })
        except Exception as e:
            print(f"Error fetching from Binance API, falling back to yfinance: {e}")
            try:
                yf_symbol = "BTC-USD" if "BTC" in symbol else "ETH-USD"
                import yfinance as yf
                ticker = yf.Ticker(yf_symbol)
                # Fetch history based on configurable period
                period = kwargs.get("period", "3mo")
                df = ticker.history(period=period)
                for idx, row in df.iterrows():
                    prices_list.append({
                        "symbol": symbol,  # Keep symbol as BTCUSDT or ETHUSDT for database compatibility
                        "timestamp": idx.date().isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row["Volume"])
                    })
            except Exception as yf_err:
                print(f"yfinance fallback failed for {symbol}: {yf_err}")
            
        return prices_list
