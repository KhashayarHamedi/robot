#!/usr/bin/env python3
"""
Modern Trading Robot Dashboard
Beautiful, responsive web interface with real-time data
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import asyncio

# Page configuration
st.set_page_config(
    page_title="Trading Robot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    /* Card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Signal indicators */
    .signal-buy {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
    }
    
    .signal-sell {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
    }
    
    .signal-neutral {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Status indicators */
    .status-online {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #4CAF50;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_market_data(symbol, period="1mo"):
    """Get market data with caching"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_technical_indicators(data):
    """Calculate technical indicators"""
    if data is None or len(data) < 20:
        return None
    
    # Simple Moving Averages
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    data['BB_Middle'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
    data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)
    
    return data

def generate_signal(data):
    """Generate trading signal"""
    if data is None or len(data) < 20:
        return "INSUFFICIENT_DATA", "Not enough data", 0
    
    current_price = data['Close'].iloc[-1]
    sma_20 = data['SMA_20'].iloc[-1]
    rsi = data['RSI'].iloc[-1]
    
    # Signal logic
    if pd.isna(sma_20) or pd.isna(rsi):
        return "NEUTRAL", "Calculating...", 50
    
    # Multi-factor signal
    price_signal = "BUY" if current_price > sma_20 else "SELL"
    rsi_signal = "OVERSOLD" if rsi < 30 else "OVERBOUGHT" if rsi > 70 else "NEUTRAL"
    
    # Combine signals
    if price_signal == "BUY" and rsi < 70:
        confidence = min(80, 50 + (current_price - sma_20) / sma_20 * 1000)
        return "BUY", f"Price above SMA20, RSI: {rsi:.1f}", confidence
    elif price_signal == "SELL" and rsi > 30:
        confidence = min(80, 50 + (sma_20 - current_price) / sma_20 * 1000)
        return "SELL", f"Price below SMA20, RSI: {rsi:.1f}", confidence
    else:
        return "NEUTRAL", f"Mixed signals, RSI: {rsi:.1f}", 40

def create_candlestick_chart(data, symbol):
    """Create beautiful candlestick chart"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} Price Chart', 'Volume', 'RSI'),
        row_width=[0.7, 0.15, 0.15]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ), row=1, col=1
    )
    
    # Moving averages
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['SMA_20'],
            name='SMA 20', line=dict(color='#ff9500', width=2)
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['SMA_50'],
            name='SMA 50', line=dict(color='#0099ff', width=2)
        ), row=1, col=1
    )
    
    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['BB_Upper'],
            name='BB Upper', line=dict(color='rgba(128,128,128,0.5)', width=1)
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['BB_Lower'],
            name='BB Lower', line=dict(color='rgba(128,128,128,0.5)', width=1),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)'
        ), row=1, col=1
    )
    
    # Volume
    fig.add_trace(
        go.Bar(
            x=data.index, y=data['Volume'],
            name='Volume', marker_color='rgba(158,202,225,0.6)'
        ), row=2, col=1
    )
    
    # RSI
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['RSI'],
            name='RSI', line=dict(color='purple', width=2)
        ), row=3, col=1
    )
    
    # RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} Trading Analysis',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

# Main Dashboard
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Trading Robot Dashboard</h1>
        <p>Professional Algorithmic Trading System</p>
        <span class="status-online"></span> System Online
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Controls")
        
        # Asset selection
        assets = {
            "Gold (GC=F)": "GC=F",
            "Silver (SI=F)": "SI=F", 
            "Crude Oil (CL=F)": "CL=F",
            "Natural Gas (NG=F)": "NG=F",
            "Copper (HG=F)": "HG=F"
        }
        
        selected_asset = st.selectbox("📊 Select Asset", list(assets.keys()))
        symbol = assets[selected_asset]
        
        # Time period
        period = st.selectbox("⏰ Time Period", ["1mo", "3mo", "6mo", "1y"])
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto Refresh (30s)", value=True)
        
        # Trading mode
        st.subheader("🎯 Trading Mode")
        trading_mode = st.radio("", ["Paper Trading", "Live Trading"], index=0)
        
        if trading_mode == "Live Trading":
            st.warning("⚠️ Live trading involves real money risk!")
        
        # Risk settings
        st.subheader("🛡️ Risk Management")
        max_risk = st.slider("Max Risk per Trade (%)", 0.1, 5.0, 1.0, 0.1)
        stop_loss = st.slider("Stop Loss (%)", 1.0, 10.0, 2.0, 0.5)
    
    # Get data
    with st.spinner("📡 Fetching market data..."):
        data = get_market_data(symbol, period)
        
        if data is not None:
            data = calculate_technical_indicators(data)
    
    if data is None:
        st.error("❌ Could not fetch market data. Please try again.")
        return
    
    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    with col1:
        st.metric(
            "💰 Current Price",
            f"${current_price:,.2f}",
            f"{price_change:+.2f} ({price_change_pct:+.1f}%)",
            delta_color="normal"
        )
    
    with col2:
        volume = data['Volume'].iloc[-1]
        st.metric("📊 Volume", f"{volume:,.0f}")
    
    with col3:
        if not pd.isna(data['RSI'].iloc[-1]):
            rsi = data['RSI'].iloc[-1]
            st.metric("📈 RSI", f"{rsi:.1f}")
    
    with col4:
        # Generate signal
        signal, reason, confidence = generate_signal(data)
        if signal == "BUY":
            st.markdown(f'<div class="signal-buy">🟢 {signal}<br>Confidence: {confidence:.0f}%</div>', unsafe_allow_html=True)
        elif signal == "SELL":
            st.markdown(f'<div class="signal-sell">🔴 {signal}<br>Confidence: {confidence:.0f}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="signal-neutral">🟡 {signal}<br>Confidence: {confidence:.0f}%</div>', unsafe_allow_html=True)
    
    # Chart
    st.plotly_chart(create_candlestick_chart(data, selected_asset), use_container_width=True)
    
    # Signal details
    st.subheader("🎯 Signal Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Signal:** {signal}")
        st.info(f"**Reason:** {reason}")
        st.info(f"**Confidence:** {confidence:.1f}%")
    
    with col2:
        if not pd.isna(data['SMA_20'].iloc[-1]):
            sma_20 = data['SMA_20'].iloc[-1]
            sma_distance = ((current_price - sma_20) / sma_20) * 100
            st.metric("📊 Distance from SMA20", f"{sma_distance:+.1f}%")
        
        if len(data) >= 50 and not pd.isna(data['SMA_50'].iloc[-1]):
            sma_50 = data['SMA_50'].iloc[-1]
            sma_distance_50 = ((current_price - sma_50) / sma_50) * 100
            st.metric("📊 Distance from SMA50", f"{sma_distance_50:+.1f}%")
    
    # Recent data table
    st.subheader("📋 Recent Data")
    recent_data = data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(5)
    recent_data = recent_data.round(2)
    st.dataframe(recent_data, use_container_width=True)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
