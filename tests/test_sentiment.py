import pandas as pd
from zimbra.sentiment import clean_text, tokenize, sentiment_scores, categorize_stakeholder, influence_score

def test_clean_text():
    assert clean_text("Hello http://google.com world!") == "Hello world"
    assert clean_text("Buy $AAPL stock! 100%") == "Buy $AAPL stock 100%"

def test_tokenize():
    tokens = tokenize("This is a strong buy alert for $AAPL")
    assert "strong" in tokens
    assert "buy" in tokens
    assert "is" not in tokens

def test_sentiment_scores():
    score, subj, bias = sentiment_scores("This stock is a strong buy, undervalued and breakout expected!")
    assert score > 0.0
    assert bias > 0.0
    
    score, subj, bias = sentiment_scores("Terrible earnings miss, sell this stock immediately crash coming!")
    assert score < 0.0
    assert bias < 0.0

def test_categorize_stakeholder():
    assert categorize_stakeholder("Buying call and put options", "AAPL", "unknown") == "options trader"
    assert categorize_stakeholder("Chart support and resistance breakout", "AAPL", "unknown") == "technical trader"
    assert categorize_stakeholder("Earnings valuation dcf margin", "AAPL", "unknown") == "fundamental analyst"

def test_influence_score():
    row = pd.Series({"likes": 10.0, "replies": 5.0, "reposts": 2.0, "views": 1000.0, "followers_est": 5000.0, "text": "Short post."})
    score = influence_score(row)
    assert score > 0.0
