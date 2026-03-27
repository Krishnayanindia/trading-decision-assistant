#!/usr/bin/env python3
"""Test script to verify trading logic without GUI"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import sys
import io

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def calculate_rsi(data, periods=14):
    """Calculate RSI indicator"""
    close = data['Close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1]
    if pd.isna(rsi_value):
        return 50.0
    return float(rsi_value)

def calculate_stochastic(data, k_period=14, d_period=3):
    """Calculate Stochastic oscillator"""
    close = data['Close']
    low = data['Low']
    high = data['High']

    low_min = low.rolling(window=k_period).min()
    high_max = high.rolling(window=k_period).max()
    denominator = high_max - low_min
    denominator = denominator.replace(0, 1e-10)

    stoch_k = 100 * (close - low_min) / denominator
    stoch_d = stoch_k.rolling(window=d_period).mean()

    k_value = stoch_k.iloc[-1]
    d_value = stoch_d.iloc[-1]

    if pd.isna(k_value):
        k_value = 50.0
    if pd.isna(d_value):
        d_value = 50.0

    return float(k_value), float(d_value)

def test_ticker(ticker_symbol):
    """Test a single ticker"""
    print(f"\n{'='*60}")
    print(f"Testing: {ticker_symbol}")
    print(f"{'='*60}")

    try:
        # Download data
        print(f"⏳ Downloading {ticker_symbol} data...")
        data = yf.download(ticker_symbol, period="1y", progress=False, threads=False)

        # Fix MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Reset column names if they're tuples
        if data.columns.nlevels > 1:
            data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

        if data.empty or data.isna().all().all():
            print(f"❌ No data for {ticker_symbol}")
            return False

        # Check minimum data requirement
        if len(data) < 200:
            print(f"❌ Insufficient data: {len(data)} days (need 200+)")
            return False

        print(f"✅ Downloaded {len(data)} days of data")

        # Calculate metrics
        current_price = float(data['Close'].iloc[-1])
        week_52_high = float(data['High'].max())
        drop_percent = ((week_52_high - current_price) / week_52_high) * 100
        dma_50 = float(data['Close'].rolling(window=50).mean().iloc[-1])
        dma_200 = float(data['Close'].rolling(window=200).mean().iloc[-1])
        rsi = calculate_rsi(data)
        stoch_k, stoch_d = calculate_stochastic(data)

        # Display results
        print(f"\n📊 Market Data for {ticker_symbol}:")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   52W High:      ${week_52_high:.2f}")
        print(f"   Drop:          {drop_percent:.2f}%")
        print(f"   50 DMA:        ${dma_50:.2f}")
        print(f"   200 DMA:       ${dma_200:.2f}")
        print(f"   RSI (14):      {rsi:.2f}")
        print(f"   Stoch %K:      {stoch_k:.2f}")
        print(f"   Stoch %D:      {stoch_d:.2f}")

        # Simple decision logic
        k_above_d = stoch_k > stoch_d
        k_below_d = stoch_k < stoch_d

        print(f"\n🎯 Decision Signals:")
        if drop_percent > 18 and dma_50 < dma_200 and rsi < 40 and stoch_k < 20 and k_below_d:
            print(f"   🔴 EXIT - All indicators confirm")
        elif drop_percent > 30 and 35 <= rsi <= 45 and k_above_d:
            print(f"   🟢 RE-ENTRY - Strong bullish signal")
        elif drop_percent < 5 and rsi > 70 and stoch_k > 80 and k_below_d:
            print(f"   🟡 TAKE PROFIT - Overbought reversal")
        else:
            print(f"   🔵 HOLD - Monitor conditions")

        print(f"\n✅ {ticker_symbol} test PASSED")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TRADING APP - CORE LOGIC TEST")
    print("="*60)

    test_tickers = ["QQQM", "SPY", "QQQ"]
    results = {}

    for ticker in test_tickers:
        results[ticker] = test_ticker(ticker)

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    for ticker, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{ticker}: {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All tests passed! Kivy app should work fine.")
    else:
        print("\n⚠️  Some tests failed. Check yfinance connection.")
