import pandas as pd
import datetime
from typing import List

from zimbra.config import DEFAULT_USER_AGENT

class InflationAdapter:
    def fetch(self, target: str = "us", **kwargs) -> List[dict]:
        """Fetch monthly historical inflation rates from rateinflation.com.
        
        :param target: Region ('us' or 'eu')
        :return: List of economic indicator dicts
        """
        region = target.lower().strip()
        if region not in ["us", "eu"]:
            if "euro" in region:
                region = "eu"
            else:
                region = "us"
                
        user_agent = kwargs.get("user_agent") or DEFAULT_USER_AGENT
        
        if region == "eu":
            url = "https://www.rateinflation.com/inflation-rate/euro-area-historical-inflation-rate/"
            indicator_name = "EU_INFLATION"
        else:
            url = "https://www.rateinflation.com/inflation-rate/usa-historical-inflation-rate/"
            indicator_name = "US_INFLATION"
            
        indicators = []
        try:
            # Fetch HTML table using pandas read_html with a user agent
            dfs = pd.read_html(url, storage_options={"User-Agent": user_agent})
            if not dfs:
                raise ValueError("No tables found on rateinflation.com")
                
            df = dfs[0]
            
            # Melt month columns into a single column
            month_cols = [c for c in df.columns if c not in ["Year", "Annual"]]
            df_melted = pd.melt(df, id_vars=["Year"], value_vars=month_cols)
            
            # Clean inflation value (remove % and convert to float)
            df_melted["value"] = df_melted["value"].astype(str).str.replace("%", "").str.strip()
            
            # Month name mapping to integers (e.g., 'jan' -> 1)
            month_map = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
            }
            
            for _, row in df_melted.iterrows():
                try:
                    val_str = row["value"]
                    if val_str == "nan" or val_str == "" or val_str is None:
                        continue
                    val = float(val_str)
                    
                    year = int(row["Year"])
                    m_name = str(row["variable"]).lower()[:3]
                    month = month_map.get(m_name, 1)
                    
                    indicators.append({
                        "indicator_name": indicator_name,
                        "year": year,
                        "month": month,
                        "value": val
                    })
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error fetching inflation data for {region}: {e}")
            
        return indicators
