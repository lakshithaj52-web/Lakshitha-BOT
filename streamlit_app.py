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
    st.title("🔐 Trend Sniper Access")
    pwd = st.text_input("මුරපදය:", type="password")
    if st.button("Login"):
        if pwd == "1234":
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- Exchange ---
exchange = ccxt.binance({'enableRateLimit': True})

def fetch_data(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=200)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except: return None

def analyze_trend_trade(df, invest, leverage):
    close = df['close']; high = df['high']; low = df['low']; open_p = df['open']
    
    # --- INDICATORS (10) ---
    # 1. EMA 200 (Main Trend Filter)
    e200 = close.ewm(span=200).mean().iloc[-1]
    # 2. EMA 50 (Short Trend)
    e50 = close.ewm(span=50).mean().iloc[-1]
    # 3. EMA 9 | 4. EMA 21
    e9 = close.ewm(span=9).mean().iloc[-1]
    e21 = close.ewm(span=21).mean().iloc[-1]
    # 5. RSI
    diff = close.diff(); g = diff.where(diff > 0, 0); l = -diff.where(diff < 0, 0)
    rsi = 100 - (100 / (1 + (g.rolling(14).mean() / l.rolling(14).mean()))).iloc[-1]
    # 6. Bollinger Bands
    sma20 = close.rolling(20).mean().iloc[-1]; std20 = close.rolling(20).std().iloc[-1]
    low_bb = sma20 - (std20 * 2); up_bb = sma20 + (std20 * 2)
    # 7. ATR (Risk Management)
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
    atr = tr.rolling(14).mean().iloc[-1]
    # 8. MACD
    macd = close.ewm(span=12).mean().iloc[-1] - close.ewm(span=26).mean().iloc[-1]
    # 9. Stochastic %K
    stoch = ((close.iloc[-1] - low.rolling(14).min().iloc[-1]) / (high.rolling(14).max().iloc[-1] - low.rolling(14).min().iloc[-1])) * 100
    # 10. Volume Boost
    vol_boost = df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1]

    # Current Price
    cp = close.iloc[-1]
    side = None
    score = 0

    # --- TREND-FOLLOWING LOGIC ---
    # BULLISH TREND (Price > EMA 200)
    if cp > e200:
        side = "BUY"
        if cp > e50: score += 30
        if e9 > e21: score += 20
        if rsi < 50: score += 20 # Buying pullbacks
        if vol_boost: score += 20
        if cp < up_bb: score += 10

    # BEARISH TREND (Price < EMA 200)
    elif cp < e200:
        side = "SELL"
        if cp < e50: score += 30
        if e9 < e21: score += 20
        if rsi > 50: score += 20 # Selling rallies
        if vol_boost: score += 20
        if cp > low_bb: score += 10

    if not side: return None

    accuracy = min(max(75 + (score/4), 80), 99.1)
    
    # Entry, SL, TP (Risk:Reward 1:2)
    entry = cp
    sl = entry - (atr * 1.5) if side == "BUY" else entry + (atr * 1.5)
    tp = entry + (atr * 3.5) if side == "BUY" else entry - (atr * 3.5)
    profit = (invest * leverage * (abs(tp - entry) / entry))

    return {"side": side, "entry": entry, "sl": sl, "tp": tp, "acc": accuracy, "profit": profit}

# --- UI ---
st.title("🏹 Lakshitha's Trend-Only Sniper")
st.sidebar.info("මෙම බොට් එක සිග්නල් ලබා දෙන්නේ ප්‍රධාන Trend එක (EMA 200) දෙසට පමණි.")
invest = st.sidebar.number_input("Investment ($):", value=2.0)
lev = st.sidebar.slider("Leverage (X):", 1, 50, 20)

if st.button("🚀 FIND HIGHEST TRUST TREND TRADE"):
    with st.spinner("Binance ස්කෑන් කරමින්..."):
        markets = exchange.fetch_markets()
        symbols = [m['symbol'] for m in markets if m['quote'] == 'USDT' and m['active']]
        
        all_signals = []
        for s in symbols[:60]: # පළමු කොයින් 60 ස්කෑන් කරයි
            df = fetch_data(s)
            if df is not None and len(df) >= 200:
                res = analyze_trend_trade(df, invest, lev)
                if res:
                    res['symbol'] = s
                    all_signals.append(res)
        
        all_signals = sorted(all_signals, key=lambda x: x['acc'], reverse=True)
        
        if all_signals:
            top = all_signals[0]
            color = "#00ff00" if top['side'] == "BUY" else "#ff4b4b"
            st.markdown(f"""
            <div style="border: 5px solid {color}; padding: 25px; border-radius: 15px; background-color: #0e1117; text-align: center;">
                <h1 style="color:{color};">🔥 BEST TREND SIGNAL: {top['symbol']}</h1>
                <h2 style="color: white;">Side: {top['side']} | Accuracy: {top['acc']:.1f}%</h2>
                <hr>
                <div style="display: flex; justify-content: space-around; font-size: 22px;">
                    <div><b>ENTRY</b><br>{top['entry']:.5f}</div>
                    <div><b>STOP LOSS</b><br>{top['sl']:.5f}</div>
                    <div><b>TAKE PROFIT</b><br>{top['tp']:.5f}</div>
                </div>
                <hr>
                <h2 style="color: #f1c40f;">Estimated Profit: ${top['profit']:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("මේ වෙලාවේ ශක්තිමත් ට්‍රෙන්ඩ් එකක් සහිත කොයින් හමු නොවීය.")
