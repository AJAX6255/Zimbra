import re
import math
from typing import List, Tuple
import pandas as pd
from textblob import TextBlob

STOPWORDS = {
    "the","a","an","and","or","but","if","then","than","that","this","those","these","is","are","was","were","be","been",
    "to","for","of","in","on","at","by","with","from","as","it","its","he","she","they","them","their","you","your",
    "we","our","i","me","my","mine","us","rt","http","https","www","com"
}

FINANCE_BULL = {"buy","long","bull","bullish","undervalued","beat","beats","upgrade","accumulate","moon","rip","squeeze","breakout","strong"}
FINANCE_BEAR = {"sell","short","bear","bearish","overvalued","miss","downgrade","dump","rug","fraud","weak","crash","dilution"}

def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^A-Za-z0-9$%\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-]{1,}", text.lower()) if w.lower() not in STOPWORDS]

def sentiment_scores(text: str) -> Tuple[float, float, float]:
    txt = clean_text(text)
    blob = TextBlob(txt)
    polarity = float(blob.sentiment.polarity)
    subjectivity = float(blob.sentiment.subjectivity)
    tokens = tokenize(txt)
    bull = sum(t in FINANCE_BULL for t in tokens)
    bear = sum(t in FINANCE_BEAR for t in tokens)
    finance_bias = (bull - bear) / max(len(tokens), 1)
    score = max(-1.0, min(1.0, polarity + 3.5 * finance_bias))
    return score, subjectivity, finance_bias

def categorize_stakeholder(text: str, thread_title: str, author_role_hint: str) -> str:
    combined = f"{text} {thread_title}".lower()
    if any(k in combined for k in ["options", "call", "put", "gamma", "iv", "premium"]):
        return "options trader"
    if any(k in combined for k in ["earnings", "revenue", "ebitda", "valuation", "dcf", "margin"]):
        return "fundamental analyst"
    if any(k in combined for k in ["chart", "support", "resistance", "trend", "breakout", "rsi", "macd"]):
        return "technical trader"
    if any(k in combined for k in ["product", "customer", "store", "service", "shipment", "app"]):
        return "customer/operator"
    if any(k in combined for k in ["sec", "ftc", "fed", "rates", "tariff", "regulation", "lawsuit"]):
        return "macro/regulatory watcher"
    if any(k in combined for k in ["lol", "meme", "moon", "bagholder", "diamond hands", "ape"]):
        return "retail momentum"
    if author_role_hint and author_role_hint != "unknown":
        return author_role_hint
    return "general participant"

def influence_score(row: pd.Series) -> float:
    engagement = row.get("likes", 0) + 1.5 * row.get("replies", 0) + 1.2 * row.get("reposts", 0)
    followers = math.log1p(max(row.get("followers_est", 0), 0))
    views = math.log1p(max(row.get("views", 0), 0))
    text_len = math.log1p(len(str(row.get("text", ""))))
    return float(0.45 * math.log1p(max(engagement, 0)) + 0.3 * followers + 0.15 * views + 0.1 * text_len)
