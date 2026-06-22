import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import snscrape.modules.twitter as sntwitter
import twitter
import pandas as pd
import glob

from datetime import timedelta
from matplotlib.colors import ListedColormap
from time import sleep
from datetime import datetime, date
from matplotlib.pyplot import figure

#forma
tweets_list = []
e = 0
max_result = 15000

dates = pd.DataFrame()

dates["start_date"] = pd.date_range(start='9/1/2017', end='3/8/2023')
dates["end_date"] = pd.date_range(start='9/2/2017', end='3/9/2023')

## Manual runs

#dates = dates[dates.start_date > datetime(2023, 2, 5)]

dates = dates.astype("str")

from IPython.display import Image
Image("twitter.jpg")

##Napi scrapelés csv fájlba

for index, row in dates.iterrows():
    tweets_list = []
    naming = row['start_date']
    term = '(ethereum OR eth OR ether OR ETH OR ETHEREUM OR ETHER OR #eth OR #ethereum) since:'+row['start_date']+' until:'+row['end_date']+' lang:en'
    print(naming + " in progress!")
    for i, tweet in enumerate(twitter.TwitterSearchScraper(f'{term}').get_items()):
        e += 1
        print(f"Current scrape index: {e}", end="\r", flush=True)
        if i>max_result: #number of tweets you want to scrape
            break
            # print(movie_name, i
            , tweet)
        try:
            tweets_list.append([tweet.date, tweet.id, tweet.rawContent, tweet.likeCount, tweet.user.username, tweet.user.followersCount, tweet.user.location, tweet.user.verified, tweet.mentionedUsers, tweet.quoteCount, tweet.quotedTweet])  # declare the attributes to be returned
        except:
            continue
        
    tweets_df = pd.DataFrame(tweets_list, columns=['datetime', 'tweet_id', 'text', 'likes', 'username', 'user_followers', "user_location", "user_verified", "mentioned_users", "quote_count", "quoted_tweet_id"])
    tweets_df.to_csv("../src/section2/twitter/scrapes/{}.csv".format(naming), escapechar='\\') 
    ## ide kellett volna index=False na nembaj, illetve 2023 tól rakok escapechart











