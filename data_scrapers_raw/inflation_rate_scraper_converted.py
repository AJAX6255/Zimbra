import pandas as pd
import datetime

inflation_rates_us = pd.read_html('https://www.rateinflation.com/inflation-rate/usa-historical-inflation-rate/')[0]

inflation_rates_us.head(3)

inflation_rates_us = pd.melt(inflation_rates_us, id_vars="Year", value_vars=[i for i in inflation_rates_us if i != "Annual" ])

inflation_rates_us.value = inflation_rates_us.value.str.replace("%", "")

inflation_rates_us.rename(columns={"Year":"year", "variable": "month", "value": "inflation_rate"}, inplace=True)

inflation_rates_us.inflation_rate = inflation_rates_us.inflation_rate.astype("float16")

inflation_rates_us.month = inflation_rates_us.month.apply(lambda x: datetime.datetime.strptime(x, "%b").month)

inflation_rates_us.sort_values(by=["year", "month"], inplace=True)

inflation_rates_us.dropna(subset=["inflation_rate"], inplace=True)

inflation_rates_us.reset_index(inplace=True, drop=True)

inflation_rates_us.head()

inflation_rates_us.to_csv("src/monthly/inflation_rates/us_inflation_rate_monthly.csv", index=False)



inflation_rates_eu = pd.read_html('https://www.rateinflation.com/inflation-rate/euro-area-historical-inflation-rate/')[0]

inflation_rates_eu.head(3)

inflation_rates_eu = pd.melt(inflation_rates_eu, id_vars="Year", value_vars=[i for i in inflation_rates_eu if i != "Annual" ])

inflation_rates_eu.value = inflation_rates_eu.value.str.replace("%", "")

inflation_rates_eu.rename(columns={"Year":"year", "variable": "month", "value": "inflation_rate"}, inplace=True)

inflation_rates_eu.inflation_rate = inflation_rates_eu.inflation_rate.astype("float16")

inflation_rates_eu.month = inflation_rates_eu.month.apply(lambda x: datetime.datetime.strptime(x, "%b").month)

inflation_rates_eu.sort_values(by=["year", "month"], inplace=True)

inflation_rates_eu.dropna(subset=["inflation_rate"], inplace=True)

inflation_rates_eu.reset_index(inplace=True, drop=True)

inflation_rates_eu.head()

inflation_rates_eu.to_csv("src/monthly/inflation_rates/eu_inflation_rate_monthly.csv", index=False)





