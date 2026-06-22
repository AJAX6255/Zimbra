import yfinance as yf
from datetime import datetime
from typing import List

class CommodityAdapter:
    def fetch(self, target: str = "gold", limit: int = 100, **kwargs) -> List[dict]:
        """Fetch daily historical/recent prices for commodities using yfinance.
        
        :param target: Commodity name ('gold', 'silver', 'GC=F', 'SI=F')
        :param limit: Number of daily data points (implied by period e.g. '3mo')
        :return: List of price dicts
        """
        symbol_map = {
            "gold": "GC=F",
            "xau": "GC=F",
            "gc=f": "GC=F",
            "silver": "SI=F",
            "xag": "SI=F",
            "si=f": "SI=F"
        }
        
        normalized_target = target.lower().strip()
        symbol = symbol_map.get(normalized_target, "GC=F")
        
        prices_list = []
        try:
            ticker = yf.Ticker(symbol)
            # Fetch history based on configurable period
            period = kwargs.get("period", "3mo")
            df = ticker.history(period=period)
            
            for idx, row in df.iterrows():
                # idx is a pandas Timestamp
                prices_list.append({
                    "symbol": symbol,
                    "timestamp": idx.date().isoformat(),  # YYYY-MM-DD
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"])
                })
        except Exception as e:
            print(f"Error fetching from yfinance for commodity {symbol}: {e}")
            
        # Limit the number of records returned if needed
        return prices_list[-limit:] if limit > 0 else prices_list
