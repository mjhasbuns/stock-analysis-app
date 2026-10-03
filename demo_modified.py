from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

END = date.today()
START = date.today() - timedelta(days=365)

st.set_page_config(layout="wide",
                   page_title="Stock Price Analysis")

st.title("Stock Analysis")

st.sidebar.title("Inputs")
ticker = st.sidebar.text_input("Enter stock ticker symbol",
                               value="AAPL",)
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", START)
end_date = col2.date_input("End Date", END)
mv_avg = st.sidebar.slider("Moving Average",
                           min_value=5,
                           max_value=100,
                           value=50,
                           step=1)
# CHANGE 1: second slider for the long moving average
mv_avg_long = st.sidebar.slider("Long Moving Average",
                                min_value=20,
                                max_value=200,
                                value=100,
                                step=1)
run_analysis = st.sidebar.button("Run Analysis",
                                 type="primary")


def get_stock_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start_date, end_date)
        if data.empty:
            return None, f"No data for {ticker}"
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data, f"Successfully downloaded data {ticker}"
    except Exception as e:
        return None, f"Download failed due to {e}"


if run_analysis:
    with st.spinner(f"Downloading {ticker}..."):
        data, message = get_stock_data(ticker, start_date, end_date)

    if data is None:
        st.error(message)
    else:
        st.success(message)

        # Calculations, done right here in the script
        data["change"] = data["Close"] - data["Close"].shift()
        data["return"] = np.round(np.log(data["Close"]).diff(), 4)
        data = data.dropna().copy()
        data["MA"] = data["Close"].rolling(mv_avg).mean()
        # CHANGE 2: calculate the long moving average
        data["MA_long"] = data["Close"].rolling(mv_avg_long).mean()

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Last close", f"${data['Close'].iloc[-1]:,.2f}")
        m2.metric("Cumulative return", f"{data['return'].sum():.2%}")
        m3.metric("Trading days", len(data))

        # Price + moving average
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Close", mode="lines"))
        fig.add_trace(go.Scatter(x=data.index, y=data["MA"], name=f"{mv_avg}-day MA", mode="lines"))
        # CHANGE 3: draw the long moving average and update the title
        fig.add_trace(go.Scatter(x=data.index, y=data["MA_long"], name=f"{mv_avg_long}-day MA", mode="lines"))
        fig.update_layout(title=f"{ticker} Close with {mv_avg}- and {mv_avg_long}-day Moving Averages",
                          xaxis_title="Date",
                          yaxis_title="Price ($)",
                          hovermode="x unified")
        st.plotly_chart(fig)

        # Cumulative performance and return distribution
        left, right = st.columns(2)
        left.plotly_chart(px.line(data["return"].cumsum(), title=f"Performance of {ticker}"))
        right.plotly_chart(px.histogram(data["return"], title=f"Return distribution of {ticker}"))