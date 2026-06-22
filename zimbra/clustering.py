import re
import math
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from zimbra.sentiment import (
    clean_text,
    tokenize,
    sentiment_scores,
    categorize_stakeholder,
    influence_score
)

def extract_style_metrics(text: str) -> dict:
    char_count = len(text)
    if char_count == 0:
        return {
            "style_uppercase_ratio": 0.0,
            "style_digit_ratio": 0.0,
            "style_excl_ratio": 0.0,
            "style_quest_ratio": 0.0,
            "style_period_ratio": 0.0,
            "style_comma_ratio": 0.0,
            "style_vocab_richness": 0.0,
        }
    
    uppercase = sum(1 for c in text if c.isupper())
    digits = sum(1 for c in text if c.isdigit())
    excl = text.count('!')
    quest = text.count('?')
    period = text.count('.')
    comma = text.count(',')
    
    words = text.lower().split()
    unique_words = len(set(words))
    vocab_richness = unique_words / max(len(words), 1)
    
    return {
        "style_uppercase_ratio": uppercase / char_count,
        "style_digit_ratio": digits / char_count,
        "style_excl_ratio": excl / char_count,
        "style_quest_ratio": quest / char_count,
        "style_period_ratio": period / char_count,
        "style_comma_ratio": comma / char_count,
        "style_vocab_richness": vocab_richness,
    }

def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # 1. Base metadata aggregates per author
    grouped = df.groupby("author").agg(
        messages=("post_id", "count"),
        avg_len=("text", lambda x: float(np.mean([len(str(v).split()) for v in x]))),
        avg_sentiment=("sentiment", "mean"),
        std_sentiment=("sentiment", "std"),
        avg_subjectivity=("subjectivity", "mean"),
        mean_influence=("influence", "mean"),
        source_mode=("source", lambda x: x.mode().iloc[0] if not x.mode().empty else "unknown"),
    ).fillna(0)

    # 2. Textual Writing-Style Features (SFLT Textual meta-function)
    style_records = []
    for author, group in df.groupby("author"):
        combined_text = " ".join(str(v) for v in group["text"])
        style_metrics = extract_style_metrics(combined_text)
        style_metrics["author"] = author
        style_records.append(style_metrics)
    
    style_df = pd.DataFrame(style_records).set_index("author")

    # 3. Content Features (SFLT Ideational meta-function)
    docs = df.groupby("author")["text"].apply(lambda s: " ".join(clean_text(v) for v in s)).reindex(grouped.index)
    vect = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=300)
    X = vect.fit_transform(docs)
    text_features = pd.DataFrame(X.toarray(), index=grouped.index, columns=[f"txt_{c}" for c in vect.get_feature_names_out()])

    # 4. Social-Network Interaction Features (SFLT Interpersonal meta-function)
    interaction_pairs = []
    for _, g in df.groupby("thread_id"):
        authors = list(dict.fromkeys(g["author"].tolist()))
        for a in authors:
            for b in authors:
                if a != b:
                    interaction_pairs.append((a, b))
    
    if interaction_pairs:
        inter_df = pd.DataFrame(interaction_pairs, columns=["author", "peer"])
        inter_counts = inter_df.groupby(["author", "peer"]).size().unstack(fill_value=0)
        inter_counts = inter_counts.div(inter_counts.sum(axis=1).replace(0, 1), axis=0)
        inter_counts.columns = [f"peer_{c}" for c in inter_counts.columns]
    else:
        inter_counts = pd.DataFrame(index=grouped.index)

    # Combine all SFLT features
    feature_df = grouped.join(style_df, how="left").join(text_features, how="left").join(inter_counts, how="left").fillna(0)
    return grouped, feature_df

def stakeholder_clusters(feature_df: pd.DataFrame) -> pd.DataFrame:
    if feature_df.empty:
        return pd.DataFrame()
    
    # Filter numerical features for clustering
    numerical_df = feature_df.select_dtypes(include=[np.number])
    X = numerical_df.values
    
    if len(feature_df) < 3:
        out = pd.DataFrame(index=feature_df.index)
        out["cluster"] = 0
        out["cluster_prob"] = 1.0
        return out
        
    n_comp = min(max(2, X.shape[1] // 10), X.shape[0] - 1, 20)
    pca = PCA(n_components=n_comp)
    Xp = pca.fit_transform(X)
    
    best_bic = None
    best_model = None
    max_k = min(6, len(feature_df))
    for k in range(2, max_k + 1):
        model = GaussianMixture(n_components=k, covariance_type="diag", random_state=42)
        model.fit(Xp)
        bic = model.bic(Xp)
        if best_bic is None or bic < best_bic:
            best_bic = bic
            best_model = model
            
    probs = best_model.predict_proba(Xp)
    labels = probs.argmax(axis=1)
    
    out = pd.DataFrame(index=feature_df.index)
    out["cluster"] = labels
    out["cluster_prob"] = probs.max(axis=1)
    for i in range(probs.shape[1]):
        out[f"cluster_{i}_prob"] = probs[:, i]
    return out

def cluster_keywords(df: pd.DataFrame, author_clusters: pd.DataFrame, top_n: int = 10) -> Dict[int, List[str]]:
    if df.empty or author_clusters.empty:
        return {}
    
    author_docs = df.groupby("author")["text"].apply(lambda s: " ".join(clean_text(v) for v in s))
    
    # Use CountVectorizer to extract simple terms
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), max_features=400)
    try:
        X = vectorizer.fit_transform(author_docs)
        terms = np.array(vectorizer.get_feature_names_out())
    except ValueError:
        # If vocabulary is empty (e.g. no terms found)
        return {c: [] for c in author_clusters["cluster"].unique()}
        
    kws = {}
    for c in sorted(author_clusters["cluster"].unique()):
        members = author_clusters[author_clusters["cluster"] == c].index
        idx = [author_docs.index.get_loc(a) for a in members if a in author_docs.index]
        if not idx:
            kws[c] = []
            continue
        scores = np.asarray(X[idx].sum(axis=0)).ravel()
        top = scores.argsort()[::-1][:top_n]
        kws[c] = terms[top].tolist()
    return kws

def aggregate_guidance(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    if df.empty:
        return {"daily": pd.DataFrame(), "stakeholder": pd.DataFrame(), "source": pd.DataFrame()}
    
    d = df.copy()
    d["date"] = d["created_utc"].dt.date
    
    daily = d.groupby("date").agg(
        posts=("post_id", "count"),
        avg_sentiment=("sentiment", "mean"),
        avg_subjectivity=("subjectivity", "mean"),
        weighted_sentiment=("weighted_sentiment", "mean"),
        weighted_influence=("influence", "mean"),
    ).reset_index()
    
    stakeholder = d.groupby("stakeholder_class").agg(
        posts=("post_id", "count"),
        avg_sentiment=("sentiment", "mean"),
        avg_subjectivity=("subjectivity", "mean"),
        mean_influence=("influence", "mean"),
    ).reset_index().sort_values("posts", ascending=False)
    
    source = d.groupby("source").agg(
        posts=("post_id", "count"),
        avg_sentiment=("sentiment", "mean"),
        mean_influence=("influence", "mean"),
    ).reset_index().sort_values("posts", ascending=False)
    
    return {"daily": daily, "stakeholder": stakeholder, "source": source}

def analyze_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, List[str]], Dict[str, pd.DataFrame]]:
    if df.empty:
        return df, pd.DataFrame(), {}, {"daily": pd.DataFrame(), "stakeholder": pd.DataFrame(), "source": pd.DataFrame()}
    
    df = df.copy()
    scores = df["text"].apply(sentiment_scores)
    df[["sentiment", "subjectivity", "finance_bias"]] = pd.DataFrame(scores.tolist(), index=df.index)
    df["stakeholder_class"] = df.apply(
        lambda r: categorize_stakeholder(r["text"], r["thread_title"], r.get("author_role_hint", "unknown")), 
        axis=1
    )
    df["influence"] = df.apply(influence_score, axis=1)
    df["weighted_sentiment"] = df["sentiment"] * (1 + df["influence"])
    
    author_summary, feature_df = build_features(df)
    clusters = stakeholder_clusters(feature_df)
    
    if not clusters.empty:
        df = df.merge(clusters.reset_index().rename(columns={"index": "author"}), on="author", how="left")
    else:
        df["cluster"] = 0
        df["cluster_prob"] = 1.0
        
    kws = cluster_keywords(df, clusters if not clusters.empty else pd.DataFrame(index=df["author"].unique(), data={"cluster": 0}))
    guidance = aggregate_guidance(df)
    
    authors_result = author_summary.join(clusters, how="left") if not author_summary.empty else pd.DataFrame()
    return df, authors_result, kws, guidance
