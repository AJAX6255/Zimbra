import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from zimbra.config import SUPPORTED_SOURCES, SOURCE_POLICY_NOTES, DATABASE_PATH, REDDIT_USER_AGENT, X_BEARER_TOKEN
from zimbra.database import (
    load_posts, save_posts, init_db,
    save_prices, load_prices, save_economic_indicators, load_economic_indicators
)
from zimbra.clustering import analyze_dataframe
from zimbra.adapters.reddit import RedditAdapter
from zimbra.adapters.x_api import XAdapter
from zimbra.adapters.yahoo import YahooAdapter
from zimbra.adapters.google_news import GoogleNewsAdapter
from zimbra.adapters.coindesk import CoindeskAdapter
from zimbra.adapters.cointelegraph import CointelegraphAdapter
from zimbra.adapters.binance import BinanceAdapter
from zimbra.adapters.commodity import CommodityAdapter
from zimbra.adapters.economic import InflationAdapter


APP_TITLE = "Stakeholder Sentiment Market Guidance"

def render_research_notes():
    st.markdown(
        """
        <div class="card">
            <h3>Forum Selection Rationale</h3>
            <ul>
                <li><strong>Reddit / WallStreetBets</strong> is the best first source for public retail sentiment because it has a mature developer ecosystem and widely used JSON/API workflows, making it more reproducible than brittle HTML scraping.</li>
                <li><strong>X</strong> is valuable for fast-moving market narratives and influential accounts, but production collection should use the official API because access is plan-dependent and billing is usage-based.</li>
                <li><strong>Discord</strong> can add high-signal niche communities, but only where your bot is present and you have permission; it also requires strong rate-limit handling.</li>
                <li><strong>Yahoo Finance boards</strong> fit the article historically, but should be treated as a secondary source because board availability and page structure can change.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

def inject_premium_css():
    st.markdown(
        """
        <style>
            /* Custom Fonts & Page Layout */
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif;
            }
            
            /* Premium Cards container */
            .card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
            }
            
            .card h3 {
                margin-top: 0;
                font-weight: 600;
                background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            /* Custom metrics display */
            .metrics-container {
                display: flex;
                gap: 20px;
                justify-content: space-between;
                margin-bottom: 30px;
            }
            
            .metric-box {
                flex: 1;
                background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.05) 100%);
                border: 1px solid rgba(255,255,255,0.08);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            }
            
            .metric-box-title {
                font-size: 0.85rem;
                text-transform: uppercase;
                color: #8a8d93;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
            }
            
            .metric-box-value {
                font-size: 2.2rem;
                font-weight: 700;
                color: #00f2fe;
                text-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    inject_premium_css()
    init_db()
    
    # Header Section
    st.markdown(
        """
        <div style="margin-bottom: 25px;">
            <h1 style="font-weight: 700; margin-bottom: 5px; background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Stakeholder Sentiment Market Guidance
            </h1>
            <p style="color: #8a8d93; font-size: 1.1rem; margin-top: 0;">
                Article-inspired stakeholder clustering & influence-weighted sentiment aggregation.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar controls
    with st.sidebar:
        st.header("Data Collection")
        source = st.selectbox("Select Source", list(SUPPORTED_SOURCES.keys()), format_func=lambda x: SUPPORTED_SOURCES[x])
        st.info(SOURCE_POLICY_NOTES[source])
        
        # Define fields based on active selection
        fetch_limit = 100
        if source in ["reddit", "x", "yahoo", "google_news", "coindesk", "cointelegraph"]:
            fetch_limit = st.slider(
                "Max Posts to Fetch",
                min_value=10,
                max_value=1000,
                value=200 if source == "reddit" else 100,
                step=10,
                help="Select the maximum number of posts/articles to fetch from the source."
            )
        
        if source == "reddit":
            subreddit = st.text_input("Reddit Subreddit", value="wallstreetbets")
            reddit_user_agent = st.text_input("Reddit User Agent", value=REDDIT_USER_AGENT)
        elif source == "x":
            x_query = st.text_input("X Search Query", value="AAPL OR $AAPL lang:en -is:retweet")
            x_bearer = st.text_input("X Bearer Token", type="password", value=X_BEARER_TOKEN)
        elif source == "yahoo":
            yahoo_url = st.text_input("Yahoo Board URL", value="https://finance.yahoo.com/quote/AAPL/community")
        elif source == "google_news":
            gnews_query = st.text_input("Google News Search Query", value="ethereum")
        elif source == "coindesk":
            coindesk_tag = st.text_input("CoinDesk Tag", value="ethereum")
        elif source == "cointelegraph":
            cointelegraph_tag = st.text_input("CoinTelegraph Tag", value="ethereum")
        elif source == "binance":
            binance_pair = st.selectbox("Binance Trading Pair", ["ETHUSDT", "BTCUSDT"])
            binance_limit = st.slider("Data Points (Days)", min_value=10, max_value=500, value=100)
        elif source == "commodity":
            commodity_target = st.selectbox("Commodity", ["gold", "silver"])
            commodity_limit = st.slider("Data Points (Days)", min_value=10, max_value=500, value=100)
        elif source == "economic":
            economic_target = st.selectbox("Region", ["us", "eu"])
            
        fetch_btn = st.button("Fetch New Data")
        st.markdown("---")
        st.write("SQLite Database Path:")
        st.caption(DATABASE_PATH)

    # Fetch Action
    if fetch_btn:
        with st.spinner("Fetching data from source..."):
            try:
                if source == "reddit":
                    adapter = RedditAdapter()
                    fetched = adapter.fetch(
                        target=subreddit, 
                        limit=fetch_limit,
                        user_agent=reddit_user_agent
                    )
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "x":
                    bearer = x_bearer or X_BEARER_TOKEN
                    if not bearer:
                        raise ValueError("Provide an X Bearer Token for official API access.")
                    adapter = XAdapter()
                    fetched = adapter.fetch(target=x_query, limit=fetch_limit, bearer_token=bearer)
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "yahoo":
                    adapter = YahooAdapter()
                    fetched = adapter.fetch(target=yahoo_url, limit=fetch_limit)
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "google_news":
                    adapter = GoogleNewsAdapter()
                    fetched = adapter.fetch(target=gnews_query, limit=fetch_limit)
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "coindesk":
                    adapter = CoindeskAdapter()
                    fetched = adapter.fetch(target=coindesk_tag, limit=fetch_limit)
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "cointelegraph":
                    adapter = CointelegraphAdapter()
                    fetched = adapter.fetch(target=cointelegraph_tag, limit=fetch_limit)
                    save_posts(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} records.")
                elif source == "binance":
                    adapter = BinanceAdapter()
                    fetched = adapter.fetch(target=binance_pair, limit=binance_limit)
                    save_prices(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} price records.")
                elif source == "commodity":
                    adapter = CommodityAdapter()
                    fetched = adapter.fetch(target=commodity_target, limit=commodity_limit)
                    save_prices(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} commodity price records.")
                elif source == "economic":
                    adapter = InflationAdapter()
                    fetched = adapter.fetch(target=economic_target)
                    save_economic_indicators(fetched)
                    st.sidebar.success(f"Successfully saved {len(fetched)} economic indicator records.")
                else:
                    raise ValueError(f"Unknown source: {source}")
            except Exception as exc:
                st.sidebar.error(f"Error fetching: {exc}")


    # Load and Analyze data
    df = load_posts()
    if not df.empty:
        df = df[df["text"].notna()].copy()
        
    # Retrieve visualization filters from the Tab 1 selectbox keys, defaulting if not set
    overview_period = st.session_state.get("overview_period_tab1", "3 Months")
    overview_ticker = st.session_state.get("overview_ticker_tab1", "All")
        
    df_filtered = df.copy()
    if not df_filtered.empty:
        # 1. Filter by date range
        days_map = {
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "1 Year": 365,
            "3 Years": 1095,
            "5 Years": 1825
        }
        days = days_map.get(overview_period, 90)
        ref_date = df_filtered["created_utc"].max()
        if pd.notna(ref_date):
            cutoff_date = ref_date - pd.Timedelta(days=days)
            df_filtered = df_filtered[df_filtered["created_utc"] >= cutoff_date]
            
        # 2. Filter by ticker keywords
        if overview_ticker != "All":
            ticker_keywords = {
                "BTC": "btc|bitcoin",
                "ETH": "eth|ethereum",
                "Gold": "gold",
                "Silver": "silver"
            }
            pattern = ticker_keywords[overview_ticker]
            df_filtered = df_filtered[df_filtered["text"].str.contains(pattern, case=False, na=False)]
            
    analyzed_df, authors_df, kws, guidance = analyze_dataframe(df_filtered)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview Dashboard", 
        "👥 Stakeholder Clusters", 
        "💬 Forum Posts", 
        "📊 Financial & Macro Data",
        "🔗 Connectors Strategy"
    ])

    with tab1:
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            overview_period = st.selectbox(
                "Visualization Time Span / Period of Interest",
                ["1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years"],
                index=["1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years"].index(overview_period),
                key="overview_period_tab1",
                help="Filter all sentiment metrics, clusters, and daily evolution charts to a specific time span."
            )
        with col_f2:
            overview_ticker = st.selectbox(
                "Filter Sentiment by Asset/Ticker",
                ["All", "BTC", "ETH", "Gold", "Silver"],
                index=["All", "BTC", "ETH", "Gold", "Silver"].index(overview_ticker),
                key="overview_ticker_tab1",
                help="Filter all sentiment charts and clusters to posts matching ticker keywords."
            )
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        # High-level metrics using customized premium styling
        posts_count = len(analyzed_df)
        authors_count = analyzed_df["author"].nunique() if not analyzed_df.empty else 0
        avg_sentiment = f"{analyzed_df['sentiment'].mean():.3f}" if not analyzed_df.empty else "0.000"
        avg_influence = f"{analyzed_df['influence'].mean():.3f}" if not analyzed_df.empty else "0.000"

        st.markdown(
            f"""
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-box-title">Total Posts</div>
                    <div class="metric-box-value">{posts_count}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-title">Unique Authors</div>
                    <div class="metric-box-value">{authors_count}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-title">Average Sentiment</div>
                    <div class="metric-box-value">{avg_sentiment}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-title">Average Influence</div>
                    <div class="metric-box-value">{avg_influence}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if not guidance["daily"].empty:
            # Visualization Charts
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Daily Sentiment Evolution")
                fig = px.line(
                    guidance["daily"], 
                    x="date", 
                    y=["avg_sentiment", "weighted_sentiment"], 
                    markers=True,
                    template="plotly_dark",
                    color_discrete_sequence=["#00f2fe", "#ff007f"]
                )
                fig.add_hline(y=0.0, line_dash="dash", line_color="#ffcc00", annotation_text="Neutral", annotation_position="bottom right")
                fig.update_layout(
                    font_family="Outfit",
                    font_color="#ffffff",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#161920",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("Source Sentiment Contributions")
                fig2 = px.bar(
                    guidance["source"], 
                    x="source", 
                    y="posts", 
                    color="avg_sentiment", 
                    template="plotly_dark",
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    color_continuous_midpoint=0.0
                )
                fig2.update_layout(
                    font_family="Outfit",
                    font_color="#ffffff",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#161920",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data yet. Use the sidebar to fetch from a source.")
            
        render_research_notes()

    with tab2:
        if not authors_df.empty:
            st.subheader("Latent Author Clusters (GMM + PCA)")
            st.dataframe(authors_df.reset_index(), use_container_width=True)
            
            st.subheader("Explicit Stakeholder Classification Summary")
            st.dataframe(guidance["stakeholder"], use_container_width=True)
            
            st.subheader("Cluster Key Expressions")
            for cluster_id, terms in kws.items():
                st.markdown(
                    f"""
                    <div style="padding: 10px; border-left: 4px solid #00f2fe; background: rgba(255,255,255,0.02); margin-bottom: 10px; border-radius: 0 8px 8px 0;">
                        <strong>Cluster {cluster_id}:</strong> {', '.join(terms[:12])}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Stakeholder summaries will appear after fetching/loading posts database.")

    with tab3:
        if not analyzed_df.empty:
            st.subheader("Stored Posts & NLP Metrics")
            show_cols = [c for c in ["source","author","created_utc","stakeholder_class","cluster","sentiment","subjectivity","influence","thread_title","text","url"] if c in analyzed_df.columns]
            st.dataframe(
                analyzed_df[show_cols].sort_values("created_utc", ascending=False), 
                use_container_width=True, 
                height=600
            )
        else:
            st.info("No posts stored in local SQLite database yet.")

    with tab4:
        st.markdown(
            """
            <div class="card">
                <h3>Financial & Macroeconomic Analysis</h3>
                <p>Correlate public stakeholder sentiment with asset prices (cryptocurrencies, commodities) and monthly macroeconomic indicators.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Prominent bootstrap button and period selection at the top of the tab
        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            bootstrap_period_label = st.selectbox(
                "Quick Bootstrap Time Span / Period of Interest", 
                ["1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years"],
                index=1,  # Default to 3 Months
                help="Select the historical timeframe to fetch and seed in the SQLite database."
            )
            st.caption("Populate or update the database. Runs the quick bootstrap to fetch market prices (BTC, ETH, Gold, Silver) and inflation rates for the selected timeframe.")
            
            period_mapping = {
                "1 Month": {"limit": 30, "period": "1mo"},
                "3 Months": {"limit": 90, "period": "3mo"},
                "6 Months": {"limit": 180, "period": "6mo"},
                "1 Year": {"limit": 365, "period": "1y"},
                "3 Years": {"limit": 1095, "period": "3y"},
                "5 Years": {"limit": 1825, "period": "5y"}
            }
            sel_config = period_mapping[bootstrap_period_label]
            limit_val = sel_config["limit"]
            period_val = sel_config["period"]
            
        with col_b2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True) # Spacer for button alignment
            bootstrap_clicked = st.button("🔄 Quick Bootstrap Data", use_container_width=True)
            
        if bootstrap_clicked:
                with st.spinner(f"Bootstrapping market and indicators data for {bootstrap_period_label}..."):
                    try:
                        # 1. Binance BTC and ETH (via yfinance fallback)
                        binance_adapter = BinanceAdapter()
                        for pair in ["BTCUSDT", "ETHUSDT"]:
                            prices = binance_adapter.fetch(target=pair, limit=limit_val, period=period_val)
                            if prices:
                                save_prices(prices)
                        # 2. Commodities (Gold & Silver)
                        commodity_adapter = CommodityAdapter()
                        for comm in ["gold", "silver"]:
                            prices = commodity_adapter.fetch(target=comm, limit=limit_val, period=period_val)
                            if prices:
                                save_prices(prices)
                        # 3. Macro indicators (US & EU inflation)
                        inflation_adapter = InflationAdapter()
                        for region in ["us", "eu"]:
                            indicators = inflation_adapter.fetch(target=region)
                            if indicators:
                                save_economic_indicators(indicators)
                        st.success(f"Successfully bootstrapped {bootstrap_period_label} of data! Refreshing...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during bootstrap: {e}")
                        
        st.write("---")
        
        # Load available symbols from db to see if we show the correlation controls
        import sqlite3
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            available_symbols_df = pd.read_sql_query("SELECT DISTINCT symbol FROM prices", conn)
            available_symbols = available_symbols_df["symbol"].tolist() if not available_symbols_df.empty else []
        except Exception:
            available_symbols = []
        conn.close()
        
        col_vis1, col_vis2 = st.columns([3, 1])
        with col_vis1:
            st.subheader("Price & Sentiment Correlation")
        with col_vis2:
            chart_period = st.selectbox(
                "Visualization Time Span / Period of Interest",
                ["1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years"],
                index=1,  # Default to 3 Months
                help="Select a specific time span to filter both the price/sentiment and inflation charts."
            )
            
        if not available_symbols:
            st.warning("No price data found in database. Fetch Binance Price or Commodity Price data from the sidebar, or use the Quick Bootstrap button above to view correlation charts.")
        else:
            selected_symbol = st.selectbox("Select Asset Symbol", available_symbols)
            
            df_price = load_prices(selected_symbol)
            
            if not df_price.empty:
                days_map = {
                    "1 Month": 30,
                    "3 Months": 90,
                    "6 Months": 180,
                    "1 Year": 365,
                    "3 Years": 1095,
                    "5 Years": 1825
                }
                days = days_map.get(chart_period, 90)
                ref_date = df_price["timestamp"].max()
                cutoff_date = ref_date - pd.Timedelta(days=days)
                df_price = df_price[df_price["timestamp"] >= cutoff_date]
            
            if not df_price.empty:
                if not analyzed_df.empty:
                    sentiment_df = analyzed_df.copy()
                    sentiment_df["date"] = sentiment_df["created_utc"].dt.date
                    daily_sent = sentiment_df.groupby("date")["sentiment"].mean().reset_index()
                    daily_sent["date"] = pd.to_datetime(daily_sent["date"])
                    
                    df_price["date"] = pd.to_datetime(df_price["timestamp"])
                    df_merged = pd.merge(df_price, daily_sent, on="date", how="left")
                    has_sentiment = df_merged["sentiment"].notna().any()
                    
                    if not has_sentiment:
                        st.info("No overlapping dates between fetched price data and fetched forum posts sentiment in this timeframe. Showing price series only.")
                        fig_price = px.line(
                            df_price, 
                            x="timestamp", 
                            y="close", 
                            title=f"{selected_symbol} Close Price Series",
                            template="plotly_dark",
                            color_discrete_sequence=["#00f2fe"]
                        )
                        fig_price.update_layout(
                            font_family="Outfit",
                            font_color="#ffffff",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#161920",
                            xaxis=dict(showgrid=False),
                            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                        )
                        st.plotly_chart(fig_price, use_container_width=True)
                    else:
                        import plotly.graph_objects as go
                        fig_dual = go.Figure()
                        fig_dual.add_trace(
                            go.Scatter(
                                x=df_merged["date"], 
                                y=df_merged["close"], 
                                name="Asset Close Price ($)", 
                                yaxis="y1", 
                                line=dict(color="#00f2fe", width=2.5)
                            )
                        )
                        fig_dual.add_trace(
                            go.Scatter(
                                x=df_merged["date"], 
                                y=df_merged["sentiment"], 
                                name="Average Sentiment", 
                                yaxis="y2", 
                                line=dict(color="#ff007f", width=2, dash="dot"),
                                marker=dict(size=6),
                                connectgaps=True
                            )
                        )
                        
                        fig_dual.add_hline(
                            y=0.0, 
                            line_dash="dash", 
                            line_color="#ffcc00", 
                            annotation_text="Neutral", 
                            annotation_position="bottom right",
                            yref="y2"
                        )
                        
                        fig_dual.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#161920",
                            font_family="Outfit",
                            font_color="#ffffff",
                            title=dict(text=f"{selected_symbol} Price vs. Daily Sentiment (Overlapping Dates)", font=dict(size=16)),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(
                                title=dict(text="Close Price ($)", font=dict(color="#00f2fe")),
                                tickfont=dict(color="#00f2fe"),
                                gridcolor="rgba(255,255,255,0.05)"
                            ),
                            yaxis2=dict(
                                title=dict(text="Sentiment Score", font=dict(color="#ff007f")),
                                tickfont=dict(color="#ff007f"),
                                anchor="x",
                                overlaying="y",
                                side="right",
                                range=[-1.0, 1.0],
                                showgrid=False
                            ),
                            legend=dict(
                                x=0.02,
                                y=0.98,
                                bgcolor="#1e222b",
                                bordercolor="rgba(255,255,255,0.2)",
                                borderwidth=1.5,
                                font=dict(
                                    family="Outfit",
                                    size=12,
                                    color="#ffffff"
                                )
                            )
                        )
                        st.plotly_chart(fig_dual, use_container_width=True)
                else:
                    fig_price = px.line(
                        df_price, 
                        x="timestamp", 
                        y="close", 
                        title=f"{selected_symbol} Close Price Series",
                        template="plotly_dark",
                        color_discrete_sequence=["#00f2fe"]
                    )
                    fig_price.update_layout(
                        font_family="Outfit",
                        font_color="#ffffff",
                        paper_bgcolor="#0e1117",
                        plot_bgcolor="#161920",
                        xaxis=dict(showgrid=False),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                    )
                    st.plotly_chart(fig_price, use_container_width=True)
                
                # Help caption for sentiment/price overlay
                st.caption(
                    "💡 **Data Coverage Note**: Price data spans the entire selected timeframe (fetched from Binance/Yahoo Finance API history). "
                    "Public stakeholder sentiment data is derived from RSS feeds and hot posts search, which only contain recent publications "
                    "(e.g. late June and July 2026). Consequently, sentiment points will only be overlaid on dates where posts were successfully crawled."
                )
            else:
                st.info(f"No price records found for {selected_symbol}.")

        st.write("---")
        st.subheader("Macro Indicators: USA & Eurozone Inflation")
        
        df_us = load_economic_indicators("US_INFLATION")
        df_eu = load_economic_indicators("EU_INFLATION")
        
        if df_us.empty and df_eu.empty:
            st.warning("No inflation data found in database. Fetch Inflation Rates (US/EU) from the sidebar, or use the Quick Bootstrap button at the top of this tab to view inflation charts.")
        else:
            # Parse dates first
            if not df_us.empty:
                df_us["date"] = pd.to_datetime(df_us["year"].astype(str) + "-" + df_us["month"].astype(str).str.zfill(2) + "-01")
            if not df_eu.empty:
                df_eu["date"] = pd.to_datetime(df_eu["year"].astype(str) + "-" + df_eu["month"].astype(str).str.zfill(2) + "-01")
                
            # Filter if a chart period is selected
            if True:  # Filter always applied as 'All Data' option is removed
                days_map = {
                    "1 Month": 30,
                    "3 Months": 90,
                    "6 Months": 180,
                    "1 Year": 365,
                    "3 Years": 1095,
                    "5 Years": 1825
                }
                days = days_map.get(chart_period, 90)
                ref_dates = []
                if not df_us.empty:
                    ref_dates.append(df_us["date"].max())
                if not df_eu.empty:
                    ref_dates.append(df_eu["date"].max())
                if ref_dates:
                    ref_date = max(ref_dates)
                    cutoff_date = ref_date - pd.Timedelta(days=days)
                    if not df_us.empty:
                        df_us = df_us[df_us["date"] >= cutoff_date]
                    if not df_eu.empty:
                        df_eu = df_eu[df_eu["date"] >= cutoff_date]
                        
            col_chart, col_table = st.columns([2, 1])
            with col_chart:
                import plotly.graph_objects as go
                fig_inf = go.Figure()
                if not df_us.empty:
                    fig_inf.add_trace(go.Scatter(x=df_us["date"], y=df_us["value"], name="US Inflation Rate (%)", line=dict(color="#4facfe", width=2.5)))
                if not df_eu.empty:
                    fig_inf.add_trace(go.Scatter(x=df_eu["date"], y=df_eu["value"], name="EU Inflation Rate (%)", line=dict(color="#ffb347", width=2.5)))
                
                fig_inf.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0e1117",
                    plot_bgcolor="#161920",
                    font_family="Outfit",
                    font_color="#ffffff",
                    title="US vs. EU Historical Inflation Rates",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(
                        title="Inflation Rate (%)",
                        gridcolor="rgba(255,255,255,0.05)"
                    ),
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        bgcolor="#1e222b",
                        bordercolor="rgba(255,255,255,0.2)",
                        borderwidth=1.5,
                        font=dict(
                            family="Outfit",
                            size=12,
                            color="#ffffff"
                        )
                    )
                )
                st.plotly_chart(fig_inf, use_container_width=True)
                
            with col_table:
                region_sel = st.radio("Display Table Data For:", ["US Inflation", "EU Inflation"])
                if region_sel == "US Inflation" and not df_us.empty:
                    st.dataframe(df_us[["year", "month", "value"]].sort_values(["year", "month"], ascending=False), use_container_width=True, height=350)
                elif region_sel == "EU Inflation" and not df_eu.empty:
                    st.dataframe(df_eu[["year", "month", "value"]].sort_values(["year", "month"], ascending=False), use_container_width=True, height=350)
                else:
                    st.write("No table records available for selected region.")

    with tab5:
        st.markdown(
            """
            <div class="card">
                <h3>🔄 Historical Reddit Sentiment Backfiller</h3>
                <p>Crawl and cache real historical Reddit posts from r/wallstreetbets using the Arctic Shift search API. 
                Specify a ticker symbol (search query) and historical timeframe to download and index posts. They will automatically be analyzed for sentiment and displayed in the Overview and Correlation dashboards.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col_bf1, col_bf2, col_bf3 = st.columns([1, 1, 1])
        with col_bf1:
            backfill_query = st.text_input("Asset Ticker / Keyword Search", value="ETH", help="The ticker symbol or keyword search query (e.g. BTC, ETH, Gold, Silver).")
        with col_bf2:
            backfill_period = st.selectbox(
                "Backfill Historical Timeframe",
                ["1 Month", "3 Months", "6 Months", "1 Year"],
                index=1,
                help="Select the historical period to backfill posts for."
            )
        with col_bf3:
            backfill_limit = st.number_input("Max Submissions to Fetch", min_value=10, max_value=1000, value=100, step=50)
            
        if st.button("🚀 Run Historical Reddit Backfill", use_container_width=True):
            import time
            from datetime import datetime, timezone
            
            # Calculate UNIX timestamps
            now_ts = int(time.time())
            period_days = {
                "1 Month": 30,
                "3 Months": 90,
                "6 Months": 180,
                "1 Year": 365
            }
            days = period_days.get(backfill_period, 90)
            after_timestamp = now_ts - (days * 24 * 3600)
            
            with st.spinner(f"Crawling real historical submissions for '{backfill_query}' from r/wallstreetbets from the past {backfill_period}..."):
                try:
                    adapter = RedditAdapter()
                    fetched_posts = adapter.fetch(
                        target="wallstreetbets",
                        limit=backfill_limit,
                        query=backfill_query,
                        after=after_timestamp,
                        before=now_ts
                    )
                    
                    if fetched_posts:
                        save_posts(fetched_posts)
                        st.success(f"Successfully fetched, analyzed, and cached {len(fetched_posts)} real submissions for '{backfill_query}' in the SQLite database!")
                        st.rerun()
                    else:
                        st.warning(f"No historical posts found matching query '{backfill_query}' in the selected timeframe.")
                except Exception as e:
                    st.error(f"Error during historical backfill: {e}")
                    
        st.write("---")
        st.markdown(
            """
            <div class="card">
                <h3>Connector & Scaffolding Strategy</h3>
                <p>Each source has been implemented as an independent adapter extending from <code>BaseAdapter</code>, outputting unified <code>PostRecord</code> objects. This structure isolates network failures and rate limits.</p>
                
                <h4>Required schema output fields:</h4>
                <ul>
                    <li><code>source</code>, <code>platform_entity</code>, <code>post_id</code>, <code>author</code>, <code>created_utc</code></li>
                    <li><code>text</code>, <code>thread_id</code>, <code>thread_title</code></li>
                    <li><code>likes</code>, <code>replies</code>, <code>reposts</code>, <code>views</code>, <code>followers_est</code></li>
                    <li><code>author_role_hint</code>, <code>url</code></li>
                </ul>
                
                <h4>Production Improvements Realized:</h4>
                <ol>
                    <li><strong>Decoupled Architecture</strong>: UI rendering is separated from ML clustering algorithms and data ingestion, facilitating automated test suites.</li>
                    <li><strong>Credential Security</strong>: API tokens are configured locally through dotenv configuration files.</li>
                    <li><strong>Reddit API compliant scraping</strong>: Replaced standard browser User-Agents with a unique identifying app User-Agent to resolve the 403 API blocking issues.</li>
                    <li><strong>Advanced Stylometrics</strong>: Enhanced writing-style metrics (uppercase, punctuation, digits, vocabulary richness ratios) for higher-resolution latent clustering.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
