#!/usr/bin/env python3
"""
Trading Robot - Main Entry Point
A beginner-friendly algorithmic trading system
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

def get_market_data(symbol, period="1d"):
    """
    Get basic market data for a symbol
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        return data
    except Exception as e:
        print(f"Error getting data for {symbol}: {e}")
        return None

def simple_moving_average(data, window=20):
    """
    Calculate simple moving average
    """
    return data['Close'].rolling(window=window).mean()

def main():
    """
    Main function to run our trading robot
    """
    print("🤖 Trading Robot Starting...")
    print("=" * 50)
    
    # Test with Gold futures
    symbol = "GC=F"  # Gold futures
    print(f"📊 Getting data for {symbol}")
    
    # Get market data
    data = get_market_data(symbol, "1mo")
    
    if data is not None:
        print(f"✅ Successfully got {len(data)} data points")
        print(f"📈 Latest price: ${data['Close'].iloc[-1]:.2f}")
        
        # Calculate simple moving average
        sma_20 = simple_moving_average(data, 20)
        latest_sma = sma_20.iloc[-1]
        
        if not pd.isna(latest_sma):
            print(f"📊 20-day Moving Average: ${latest_sma:.2f}")
            
            # Simple signal logic
            current_price = data['Close'].iloc[-1]
            if current_price > latest_sma:
                print("🟢 Signal: Price above MA - Potential BUY")
            else:
                print("🔴 Signal: Price below MA - Potential SELL")
        
        print("\n📋 Last 3 days of data:")
        print(data[['Open', 'High', 'Low', 'Close']].tail(3))
        
    else:
        print("❌ Failed to get market data")
    
    print("\n🤖 Trading Robot Finished!")

if __name__ == "__main__":
    main()

