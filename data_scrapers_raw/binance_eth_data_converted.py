import os
import sys
import json
import requests
import pandas as pd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import binance
import yfinance as yf
import seaborn as sns
import datetime as dt

from binance.client import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# client configuration
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")  ## put your secrets in enviroment variables
client = Client(api_key, api_secret)

start_time = datetime.strptime('2017-09-01 00:00:00', '%Y-%m-%d %H:%M:%S') ## first timestamp available on Binance

list_of_millisecs =[]
now = datetime.now()

while start_time < now:
    millisec = start_time.timestamp() * 1000
    list_of_millisecs.append(str(int(millisec)))
    start_time = start_time + timedelta(hours=12)

df = pd.DataFrame()

for i in range(0, len(list_of_millisecs)):
    try:
        url = 'https://api.binance.com/api/v3/klines'
        symbol = 'ETHUSDT'
        interval = '1m'
        start = list_of_millisecs[i]
        if i+1 == len(list_of_millisecs):
            end = str(int(datetime.now().timestamp() * 1000))
        else:
            end = list_of_millisecs[i+1]

        par = {'symbol': symbol, 'interval': interval, 'startTime': start, 'endTime': end, 'limit': 1000}
        data = pd.DataFrame(json.loads(requests.get(url, params= par).text))

        #format columns name
        data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore']
        data.index = [dt.datetime.fromtimestamp(x/1000.0) for x in data.datetime]
        data=data.astype(float)
        
    except:
        pass
    
    
    df = pd.concat([df, data])

df.drop_duplicates(keep="first", inplace=True)

df.to_csv("dataframes/minute/ethereum_1_min_df.csv", index=False)

df.tail()



start_time = datetime.strptime('2016-06-30 00:00:00', '%Y-%m-%d %H:%M:%S') ## first timestamp available on Binance

list_of_millisecs =[]
now = datetime.now()

while start_time < dt.datetime(2017, 9, 1, 22, 9, 2):
    millisec = start_time.timestamp() * 1000
    list_of_millisecs.append(str(int(millisec)))
    start_time = start_time + timedelta(hours=12)

df = pd.DataFrame()

for i in range(0, len(list_of_millisecs)):
    try:
        url = 'https://api.binance.com/api/v3/klines'
        symbol = 'ETHUSDT'
        interval = '1d'
        start = list_of_millisecs[i]
        if i+1 == len(list_of_millisecs):
            end = str(int(datetime.now().timestamp() * 1000))
        else:
            end = list_of_millisecs[i+1]

        par = {'symbol': symbol, 'interval': interval, 'startTime': start, 'endTime': end, 'limit': 1000}
        data = pd.DataFrame(json.loads(requests.get(url, params= par).text))

        #format columns name
        data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore']
        data.index = [dt.datetime.fromtimestamp(x/1000.0) for x in data.datetime]
        data=data.astype(float)
        
    except:
        pass
    
    
    df = pd.concat([df, data])

df.to_csv("src/section1/daily/eth/ethereum_daily_df.csv", index=False)



df = pd.DataFrame()

for i in range(0, len(list_of_millisecs)):
    try:
        url = 'https://api.binance.com/api/v3/klines'
        symbol = 'ETHUSDT'
        interval = '1w'
        start = list_of_millisecs[i]
        if i+1 == len(list_of_millisecs):
            end = str(int(datetime.now().timestamp() * 1000))
        else:
            end = list_of_millisecs[i+1]

        par = {'symbol': symbol, 'interval': interval, 'startTime': start, 'endTime': end, 'limit': 1000}
        data = pd.DataFrame(json.loads(requests.get(url, params= par).text))

        #format columns name
        data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore']
        data.index = [dt.datetime.fromtimestamp(x/1000.0) for x in data.datetime]
        data=data.astype(float)
        
    except:
        pass
    
    
    df = pd.concat([df, data])

df.tail()

df.drop_duplicates(keep="first")

df.to_csv("dataframes/weekly/ethereum_weekly_df.csv", index=False)





