import datetime as dt
import logging
import random
import pandas as pd
import time
import datetime as dt
from pmaw import PushshiftAPI

api = PushshiftAPI()

e = 0

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

dates = pd.DataFrame()

dates["start_date"] = pd.date_range(start='9/1/2017', end='3/8/2023')
dates["end_date"] = pd.date_range(start='9/2/2017', end='3/9/2023')

## Manual runs

#dates = dates[dates.start_date > dt.datetime(2018, 5, 31)]

dates = dates.astype("str")

for index, row in dates.iterrows():
    e += 1
    naming = row["start_date"]
    start_epoch = str(int(time.mktime(dt.datetime.strptime(row["start_date"], "%Y-%m-%d").timetuple())))
    end_epoch = str(int(time.mktime(dt.datetime.strptime(row["end_date"], "%Y-%m-%d").timetuple())))
    term = 'ethereum OR eth OR ether'
    api_request_generator_posts = api.search_submissions(q=f"{term}", before=end_epoch, after=start_epoch, search_window=1, score=1, limit=1000, sort_type="score", sort="desc")
    df_reddit = pd.DataFrame.from_dict(api_request_generator_posts)
    print("Current scrape index: {0} [%d%%]\r".format(e), end="")
    #df_reddit = df_reddit[['author', 'date', 'title', 'selftext', 'url', 'subreddit', 'score', 'num_comments', 'num_crossposts']]
    
    df_reddit.to_csv(f"src/section2/reddit/scrapes/posts/{naming}.csv", index=False)
    del df_reddit

for index, row in dates.iterrows():
    e += 1
    naming = row["start_date"]
    start_epoch = str(int(time.mktime(dt.datetime.strptime(row["start_date"], "%Y-%m-%d").timetuple())))
    end_epoch = str(int(time.mktime(dt.datetime.strptime(row["end_date"], "%Y-%m-%d").timetuple())))
    api_request_generator_posts = api.search_submissions(q=".", sub="ethereum", after=start_epoch, search_window=2048, limit=1000, sort_type="score", sort="desc")
    df_reddit = pd.DataFrame.from_dict(api_request_generator_posts)
    print("Current scrape index: {0} [%d%%]\r".format(e), end="")
    #df_reddit = df_reddit[['author', 'date', 'title', 'selftext', 'url', 'subreddit', 'score', 'num_comments', 'num_crossposts']]
    
    df_reddit.to_csv(f"src/section2/reddit/scrapes/posts/{naming}.csv", index=False)
    del df_reddit

for index, row in dates.iterrows():
    e += 1
    naming = row["start_date"]
    start_epoch = str(int(time.mktime(dt.datetime.strptime(row["start_date"], "%Y-%m-%d").timetuple())))
    end_epoch = str(int(time.mktime(dt.datetime.strptime(row["end_date"], "%Y-%m-%d").timetuple())))
    term = 'ethereum OR eth OR ether OR ETH OR ETHEREUM OR ETHER'
    api_request_generator_comments = api.search_comments(q=f"{term}", before=end_epoch, after=start_epoch, search_window=1, score=1, limit=1000, sort_type="score", sort="desc")
    df_reddit = pd.DataFrame.from_dict(api_request_generator_comments)
    print("Current scrape index: {0} [%d%%]\r".format(e), end="")
    #df_reddit = df_reddit[['author', 'date', 'title', 'selftext', 'url', 'subreddit', 'score', 'num_comments', 'num_crossposts']]
    
    df_reddit.to_csv(f"src/section2/reddit/scrapes/comments/{naming}.csv", index=False)
    del df_reddit

df_reddit.sort_values(by="date")

df_reddit["iso_date"] = df_reddit.date.apply(lambda x: x.date())

df_reddit[df_reddit.iso_date > dt.datetime.strptime("2017-09-01", "%Y-%m-%d").date()].sort_values(by="iso_date").to_csv("testeles.csv")







