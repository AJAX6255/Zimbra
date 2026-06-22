import pandas as pd
from datetime import datetime, timezone
from zimbra.clustering import (
    extract_style_metrics, 
    build_features, 
    stakeholder_clusters, 
    cluster_keywords, 
    aggregate_guidance, 
    analyze_dataframe
)

def test_extract_style_metrics():
    metrics = extract_style_metrics("HELLOO!!! 12345")
    assert metrics["style_uppercase_ratio"] > 0.0
    assert metrics["style_excl_ratio"] > 0.0
    assert metrics["style_digit_ratio"] > 0.0
    assert metrics["style_vocab_richness"] == 1.0

def test_analyze_dataframe_lifecycle():
    now = datetime.now(timezone.utc)
    records = [
        {
            "source": "reddit",
            "platform_entity": "wallstreetbets",
            "post_id": "p1",
            "author": "user1",
            "created_utc": now,
            "text": "Buying call options now on $AAPL, leverage to the moon!",
            "thread_id": "thread1",
            "thread_title": "$AAPL Call options discussion",
            "likes": 5.0,
            "replies": 1.0,
            "reposts": 0.0,
            "views": 10.0,
            "followers_est": 100.0,
            "author_role_hint": "unknown",
            "url": "http://reddit.com"
        },
        {
            "source": "reddit",
            "platform_entity": "wallstreetbets",
            "post_id": "p2",
            "author": "user2",
            "created_utc": now,
            "text": "Earnings valuation and DCF model for Apple looks solid, valuation high margin.",
            "thread_id": "thread1",
            "thread_title": "$AAPL Call options discussion",
            "likes": 15.0,
            "replies": 3.0,
            "reposts": 0.0,
            "views": 50.0,
            "followers_est": 200.0,
            "author_role_hint": "unknown",
            "url": "http://reddit.com"
        },
        {
            "source": "reddit",
            "platform_entity": "wallstreetbets",
            "post_id": "p3",
            "author": "user3",
            "created_utc": now,
            "text": "Look at this chart support breakout and MACD indicator! Extremely bullish trend.",
            "thread_id": "thread2",
            "thread_title": "$AAPL Chart indicators",
            "likes": 20.0,
            "replies": 4.0,
            "reposts": 0.0,
            "views": 100.0,
            "followers_est": 500.0,
            "author_role_hint": "unknown",
            "url": "http://reddit.com"
        }
    ]
    df = pd.DataFrame(records)
    
    analyzed_df, authors_df, kws, guidance = analyze_dataframe(df)
    
    assert not analyzed_df.empty
    assert "sentiment" in analyzed_df.columns
    assert "influence" in analyzed_df.columns
    assert "stakeholder_class" in analyzed_df.columns
    assert "cluster" in analyzed_df.columns
    
    assert not authors_df.empty
    assert "cluster" in authors_df.columns
    
    assert isinstance(kws, dict)
    assert not guidance["daily"].empty
    assert not guidance["stakeholder"].empty
