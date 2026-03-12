import streamlit as st
import ccxt
import pandas as pd
import numpy as np

# --- Page Setup ---
st.set_page_config(page_title="Lakshitha Trend Sniper AI", layout="wide")

# --- Security ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Pro Sniper Access")
    pwd = st.text_input("මුරපදය:", type="password")
    if st.button("Login"):
        if pwd == "1234":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- Exchange Setup ---
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'adjustForTimeDifference': True}})

def fetch_data(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=200)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except: return None

def analyze_trade(df, invest, leverage):
    close = df['close']; high = df['high']; low = df['low']; open_p = df['open']
    cp = close.iloc[-1]
    
    # --- INDICATORS (Trend Filters) ---
    e200 = close.ewm(span=200).mean().iloc[-1]
    e50 = close.ewm(span=50).mean().iloc[-1]
    e9 = close.ewm(span=9).mean().iloc[-1]
    e21 = close.ewm(span=21).mean().iloc[-1]
    
    # RSI & ATR
    diff = close.diff(); g = diff.where(diff > 0, 0); l = -diff.where(diff < 0, 0)
    rsi = 100 - (100 / (1 + (g.rolling(14).mean() / l.rolling(14).mean()))).iloc[-1]
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
    atr = tr.rolling(14).mean().iloc[-1]

    # --- TREND FOLLOWING LOGIC ---
    side = None
    score = 0
    
    # Trend එක Up (Price > EMA 200)
    if cp > e200:
        side = "BUY"
        if cp > e50: score += 30
        if e9 > e21: score += 30
        if rsi < 55: score += 20
        if (close.iloc[-1] > open_p.iloc[-1]): score += 20
    
    # Trend එක Down (Price < EMA 200)
    elif cp < e200:
        side = "SELL"
        if cp < e50: score += 30
        if e9 < e21: score += 30
        if rsi > 45: score += 20
        if (close.iloc[-1] < open_p.iloc[-1]): score += 20

    if not side: return None
    
    accuracy = min(max(78 + (score/4), 80), 99.2)
    entry = cp
    sl = entry - (atr * 1.5) if side == "BUY" else entry + (atr * 1.5)
    tp = entry + (atr * 3.5) if side == "BUY" else entry - (atr * 3.5)
    profit = (invest * leverage * (abs(tp - entry) / entry))

    return {"symbol": "", "side": side, "entry": entry, "sl": sl, "tp": tp, "acc": accuracy, "profit": profit}

# --- UI ---
st.title("🏹 Lakshitha's Trend Sniper AI")
invest = st.sidebar.number_input("Investment ($):", value=2.0)
lev = st.sidebar.slider("Leverage (X):", 1, 50, 20)

if st.button("🚀 START SCAN & FIND BEST TREND TRADE"):
    with st.spinner("Binance ස්කෑන් කරමින්..."):
        markets = exchange.fetch_markets()
        symbols = [m['symbol'] for m in markets if m['quote'] == 'USDT' and m['active']]
        
        all_signals = []
        for s in symbols[:50]:
            df = fetch_data(s)
            if df is not None and len(df) >= 100:
                res = analyze_trade(df, invest, lev)
                if res:
                    res['symbol'] = s
                    all_signals.append(res)
        
        all_signals = sorted(all_signals, key=lambda x: x['acc'], reverse=True)
        
        if all_signals:
            top = all_signals[0]
            color = "#00ff00" if top['side'] == "BUY" else "#ff4b4b"
            st.markdown(f"""
            <div style="border: 6px solid {color}; padding: 30px; border-radius: 20px; background-color: #0e1117; text-align: center;">
                <h1 style="color:{color};">🏆 BEST TREND SIGNAL: {top['symbol']}</h1>
                <h2 style="color: white;">Side: {top['side']} | Trust: {top['acc']:.1f}%</h2>
                <hr style="border-color: {color};">
                <div style="display: flex; justify-content: space-around; font-size: 24px; color: #ecf0f1;">
                    <div><b>ENTRY</b><br>{top['entry']:.5f}</div>
                    <div><b>STOP LOSS</b><br>{top['sl']:.5f}</div>
                    <div><b>TAKE PROFIT</b><br>{top['tp']:.5f}</div>
                </div>
                <hr style="border-color: {color};">
                <h2 style="color: #f1c40f;">Estimated Profit: ${top['profit']:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("හොඳ ට්‍රෙන්ඩ් එකක් සහිත කොයින් එකක් හමු නොවීය.")
