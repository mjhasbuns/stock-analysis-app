from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from stock import Stock

st.set_page_config(page_title="Stock Analysis", layout="wide")
st.title("Stock Analysis App")


# ---------- Data: all fetching goes through the Stock class ----------
@st.cache_data
# CHANGE: added ma_window_long (optional, so the Portfolio tab's call didn't need to change)
def get_stock(symbol, start, end, ma_window, ma_window_long=None):
    """Create a Stock object. Cached, so it only downloads again when an input changes."""
    return Stock(symbol, start=start, end=end, ma_window=ma_window, ma_window_long=ma_window_long)


# ---------- Sidebar (shared by both tabs) ----------
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker symbol", value="AAPL").strip().upper()
start_date = st.sidebar.date_input("Start date", value=date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("End date", value=date.today())
ma_window = st.sidebar.slider("Short moving average (days)", min_value=5, max_value=200, value=20)
# CHANGE: second slider for the long moving average
ma_window_long = st.sidebar.slider("Long moving average (days)", min_value=5, max_value=200, value=100)

# st.button is only True on the click itself, so remember the click in session_state
if st.sidebar.button("Fetch data"):
    st.session_state["fetched"] = True

if start_date >= end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

tab1, tab2 = st.tabs(["Single Stock Analysis", "Portfolio Comparison"])


# ---------- Tab 1: Single Stock Analysis ----------
with tab1:
    if not st.session_state.get("fetched"):
        st.info("Pick a ticker and dates in the sidebar, then click **Fetch data**.")
    else:
        with st.spinner(f"Fetching {ticker}..."):
            # CHANGE: pass the long window to the class
            stock = get_stock(ticker, str(start_date), str(end_date), ma_window, ma_window_long)

        if stock.data is None:
            st.error(stock.message)
        else:
            st.success(stock.message)
            data = stock.data

            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Last close", f"${data['Close'].iloc[-1]:,.2f}", f"{data['change'].iloc[-1]:+.2f}")
            col2.metric("Cumulative return", f"{data['return'].sum():.2%}")
            col3.metric("Trading days", len(data))

            # Close + moving average (no class method for this, so built here from stock.data)
            price_fig = go.Figure()
            price_fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Close", mode="lines"))
            price_fig.add_trace(go.Scatter(x=data.index, y=data["MA"], name=f"{ma_window}-day MA", mode="lines"))
            # CHANGE: draw the long moving average and update the title
            price_fig.add_trace(go.Scatter(x=data.index, y=data["MA_long"], name=f"{ma_window_long}-day MA", mode="lines"))
            price_fig.update_layout(
                title=f"{ticker} Close with {ma_window}- and {ma_window_long}-day Moving Averages",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode="x unified",
            )
            st.plotly_chart(price_fig)

            # The class's own charts
            left, right = st.columns(2)
            left.plotly_chart(stock.plot_performance())
            right.plotly_chart(stock.plot_return_dist())

            # Summary statistics for the return column
            st.subheader("Return statistics")
            st.dataframe(data["return"].describe().to_frame("return"))


# ---------- Tab 2: Portfolio Comparison ----------
with tab2:
    tickers_text = st.text_input("Tickers (comma-separated)", value="AAPL, MSFT, GOOG")
    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]

    comp_fig = go.Figure()
    for symbol in tickers:
        with st.spinner(f"Fetching {symbol}..."):
            s = get_stock(symbol, str(start_date), str(end_date), ma_window)

        if s.data is None:
            st.error(f"{symbol}: {s.message}")
            continue  # skip this ticker, keep going with the rest

        cum = s.data["return"].cumsum()
        cum = cum - cum.iloc[0]  # zero-based: every line starts at exactly 0.0
        comp_fig.add_trace(go.Scatter(x=cum.index, y=cum, name=symbol, mode="lines"))

    if comp_fig.data:
        comp_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        comp_fig.update_layout(
            title="Cumulative Performance (zero-based)",
            xaxis_title="Date",
            yaxis_title="Cumulative return",
            yaxis_tickformat=".1%",
            hovermode="x unified",
            legend_title="Ticker",
        )
        st.plotly_chart(comp_fig)