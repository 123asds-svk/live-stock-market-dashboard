import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import feedparser
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import BollingerBands

def screen_stock(symbol):

    try:

        df = yf.download(
            symbol,
            period="1y",
            progress=False
        )

        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]

        dma50 = SMAIndicator(
            close,
            window=50
        ).sma_indicator()

        dma200 = SMAIndicator(
            close,
            window=200
        ).sma_indicator()

        rsi = RSIIndicator(
            close,
            window=14
        ).rsi()

        bb = BollingerBands(
            close,
            window=20,
            window_dev=2
        )

        upper_band = bb.bollinger_hband()

        latest_price = float(
            close.iloc[-1]
        )

        latest_dma50 = float(
            dma50.iloc[-1]
        )

        latest_dma200 = float(
            dma200.iloc[-1]
        )

        latest_rsi = float(
            rsi.iloc[-1]
        )

        avg_volume = (
            df["Volume"]
            .tail(20)
            .mean()
        )

        latest_volume = float(
            df["Volume"].iloc[-1]
        )

        trend_condition = (
            latest_price > latest_dma50 > latest_dma200
        )

        rsi_condition = (
            55 <= latest_rsi <= 70
        )

        volume_condition = (
            latest_volume > (1.5 * avg_volume)
        )

        breakout_condition = (
            latest_price > float(
                upper_band.iloc[-1]
            )
        )

        buy_signal = (
            trend_condition
            and rsi_condition
            and volume_condition
            and breakout_condition
        )
        return {
    "Stock": symbol,
    "Price": round(latest_price, 2),
    "DMA50": round(latest_dma50, 2),
    "DMA200": round(latest_dma200, 2),
    "RSI": round(latest_rsi, 2),
    "Trend": trend_condition,
    "Breakout": breakout_condition,
    "Volume Spike": volume_condition,
    "BUY": buy_signal
}

    except Exception:
        return {
        "Stock": symbol,
        "Price": 0,
        "DMA50": 0,
        "DMA200": 0,
        "RSI": 0,
        "Trend": False,
        "Breakout": False,
        "Volume Spike": False,
        "BUY": False
    }


# Page Config
st.set_page_config(
    page_title="Live Stock Dashboard",
    layout="wide"
)

st.title("📈 Live Stock Market Dashboard")

# Refresh Button
if st.button("🔄 Refresh Data"):
    st.rerun()

# Stock Selector
stock = st.selectbox(
    "Select Stock",
    [
        "TCS.NS",
        "INFY.NS",
        "RELIANCE.NS",
        "HDFCBANK.NS",
        "SBIN.NS"
    ]
)

# Download Data
data = yf.download(
    stock,
    period="6mo"
)

# Fix MultiIndex Columns
if hasattr(data.columns, "levels"):
    data.columns = data.columns.get_level_values(0)

# Moving Average
data["MA20"] = data["Close"].rolling(20).mean()

# KPIs
current_price = float(data["Close"].iloc[-1])

daily_return = (
    (data["Close"].iloc[-1] - data["Close"].iloc[-2])
    / data["Close"].iloc[-2]
) * 100

volume = int(data["Volume"].iloc[-1])

volatility = (
    data["Close"]
    .pct_change()
    .std()
) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Current Price",
        f"₹{current_price:.2f}"
    )

with col2:
    st.metric(
        "Daily Return",
        f"{daily_return:.2f}%"
    )

with col3:
    st.metric(
        "Volume",
        f"{volume:,}"
    )

with col4:
    st.metric(
        "Volatility",
        f"{volatility:.2f}%"
    )

# Buy / Sell Signal
latest_ma20 = data["MA20"].iloc[-1]

if current_price > latest_ma20:
    st.success(
        "🟢 BUY SIGNAL (Price above MA20)"
    )
else:
    st.error(
        "🔴 SELL SIGNAL (Price below MA20)"
    )

# Price Trend Chart
st.subheader("📉 Price Trend")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        name="Close Price"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["MA20"],
        mode="lines",
        name="20 Day MA"
    )
)

fig.update_layout(
    title=f"{stock} Price Trend",
    xaxis_title="Date",
    yaxis_title="Price"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# Candlestick Chart
st.subheader("📈 Candlestick Chart")

candlestick = go.Figure(
    data=[
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Candlestick"
        )
    ]
)

candlestick.update_layout(
    title=f"{stock} Candlestick Chart",
    xaxis_title="Date",
    yaxis_title="Price"
)

st.plotly_chart(
    candlestick,
    use_container_width=True
)

# Multi Stock Comparison
st.subheader("📊 Multi Stock Comparison")

selected_stocks = st.multiselect(
    "Choose Stocks",
    [
        "TCS.NS",
        "INFY.NS",
        "RELIANCE.NS",
        "HDFCBANK.NS",
        "SBIN.NS"
    ],
    default=[
        "TCS.NS",
        "INFY.NS"
    ]
)

if selected_stocks:

    comparison_data = yf.download(
        selected_stocks,
        period="6mo"
    )

    comparison_close = comparison_data["Close"]

    st.line_chart(comparison_close)

# Top Gainer / Top Loser
st.subheader("🏆 Top Gainer & Top Loser")

stocks = [
    "TCS.NS",
    "INFY.NS",
    "RELIANCE.NS",
    "HDFCBANK.NS",
    "SBIN.NS"
]

performance = {}

for s in stocks:

    temp = yf.download(
        s,
        period="1mo"
    )

    if hasattr(temp.columns, "levels"):
        temp.columns = temp.columns.get_level_values(0)

    growth = (
        (
            temp["Close"].iloc[-1]
            - temp["Close"].iloc[0]
        )
        / temp["Close"].iloc[0]
    ) * 100

    performance[s] = growth

top_gainer = max(
    performance,
    key=performance.get
)

top_loser = min(
    performance,
    key=performance.get
)

col1, col2 = st.columns(2)

with col1:
    st.success(
        f"🏆 Top Gainer: {top_gainer} ({performance[top_gainer]:.2f}%)"
    )

with col2:
    st.error(
        f"📉 Top Loser: {top_loser} ({performance[top_loser]:.2f}%)"
    )

# Recent Data
st.subheader("📋 Recent Data")

st.dataframe(
    data.tail()
)

# Watchlist
st.subheader("⭐ My Watchlist")

watchlist = st.multiselect(
    "Choose Stocks for Watchlist",
    [
        "TCS.NS",
        "INFY.NS",
        "RELIANCE.NS",
        "HDFCBANK.NS",
        "SBIN.NS"
    ]
)

if watchlist:

    for item in watchlist:

        temp = yf.download(
            item,
            period="5d"
        )

        if hasattr(temp.columns, "levels"):
            temp.columns = temp.columns.get_level_values(0)

        price = float(
            temp["Close"].iloc[-1]
        )

        st.write(
            f"{item}: ₹{price:.2f}"
        )

# Stock Rankings
st.subheader("📊 Stock Rankings")

ranking_df = pd.DataFrame(
    performance.items(),
    columns=[
        "Stock",
        "Return (%)"
    ]
)

ranking_df = ranking_df.sort_values(
    by="Return (%)",
    ascending=False
)

st.dataframe(
    ranking_df
)

# Market News
st.subheader("📰 Market News")

feed = feedparser.parse(
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5ENSEI&region=US&lang=en-US"
)

for entry in feed.entries[:5]:
    st.write(
        "🔹",
        entry.title
    )
    # Papa's Stock Screener

st.subheader("Stock Screener")

stocks_to_screen = [
    # Large Caps
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",

    # Mid Caps
    "POLYCAB.NS",
    "COFORGE.NS",
    "PERSISTENT.NS",
    "MUTHOOTFIN.NS",
    "APLAPOLLO.NS"
]

results = []

for stock_name in stocks_to_screen:
  results.append(
     screen_stock(stock_name)
)

screen_df = pd.DataFrame(results)

st.dataframe(screen_df)
buy_count = screen_df["BUY"].sum()

st.metric(
    "Qualified Stocks",
    buy_count
)

qualified = screen_df[
screen_df["BUY"] == True
]
if buy_count > 0:
    st.success(
        f"{buy_count} stocks match the Momentum Breakout Strategy."
    )
else:
    st.warning(
        "No stocks currently match the Momentum Breakout Strategy."
    )

st.subheader("📈 Momentum Breakout Screener")

if len(qualified) > 0:
  st.dataframe(qualified)
else:
  st.warning(
 "No stocks satisfy all conditions today."
)
