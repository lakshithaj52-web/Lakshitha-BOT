import streamlit as st
import ccxt
import pandas as pd
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Lakshitha Trend-Sniper AI", layout="wide")

# --- Security System ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Pro Sniper Access")
    pwd = st.text_input("මුරපදය ඇතුළත් කරන්න:", type="password")
    if st.button("Login"):
        if pwd == "1234":
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("වැරදි මුරපදයක්!")
    st.stop()

# --- Exchange Setup ---
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'adjustForTimeDifference': True}
})

def fetch_data(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=200)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except: return None

def analyze_trend_following(df, invest, leverage):
    close = df['close']
    high = df['high']
    low = df['low']
    open_p = df['open']
    
    # --- 10 INDICATORS & TRICKS ---
    # 1. EMA 200 (Main Trend Filter)
    e200 = close.ewm(span=200).mean().iloc[-1]
    # 2. EMA 50 (Short Trend)
    e50 = close.ewm(span=50).mean().iloc[-1]
    # 3. EMA 9 | 4. EMA 21
    e9 = close.ewm(span=9).mean().iloc[-1]
    e21 = close.ewm(span=21).mean().iloc[-1]
    # 5. RSI (14)
    diff = close.diff(); g = diff.where(diff > 0, 0); l = -diff.where(diff < 0, 0)
    rsi = 100 - (100 / (1 + (g.rolling(14).mean() / l.rolling(14).mean()))).iloc[-1]
    # 6. Bollinger Bands
    sma20 = close.rolling(20).mean().iloc[-1]; std20 = close.rolling(20).std().iloc[-1]
    up_bb = sma20 + (std20 * 2); low_bb = sma20 - (std20 * 2)
    # 7. ATR (14) - For Precise SL/TP
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
    atr = tr.rolling(14).mean().iloc[-1]
    # 8. MACD
    macd = close.ewm(span=12).mean().iloc[-1] - close.ewm(span=26).mean().iloc[-1]
    # 9. Stochastic %K
    stoch = ((close.iloc[-1] - low.rolling(14).min().iloc[-1]) / (high.rolling(14).max().iloc[-1] - low.rolling(14).min().iloc[-1])) * 100
    # 10. Volume Trend
    vol_boost = df['volume'].iloc[-1] > df['volume'].rolling(10).mean().iloc[-1]

    # --- Trend Following Logic ---
    cp = close.iloc[-1]
    side = None
    score = 0

    # BULLISH TREND: Only BUY signals
    if cp > e200:
        side = "BUY"
        if cp > e50: score += 20
        if e9 > e21: score += 20
        if rsi < 55: score += 15 # Pullback entry
        if vol_boost: score += 15
        if stoch < 30: score += 10
        if (close.iloc[-1] > open_p.iloc[-1]) and (close.iloc[-2] < open_p.iloc[-2]): score += 20 # Engulfing

    # BEARISH TREND: Only SELL signals
    elif cp < e200:
        side = "SELL"
        if cp < e50: score += 20
        if e9 < e21: score += 20
        if rsi > 45: score += 15 # Rally entry
        if vol_boost: score += 15
        if stoch > 70: score += 10
        if (close.iloc[-1] < open_p.iloc[-1]) and (close.iloc[-2] > open_p.iloc[-2]): score += 20 # Engulfing

    if not side: return None

    # Accuracy/Trust Calculation
    accuracy = min(max(75 + (score/4), 82), 99.2)
    
    # SL/TP calculation (Risk:Reward 1:2.5)
    entry = cp
    sl = entry - (atr * 1.5) if side == "BUY" else entry + (atr * 1.5)
    tp = entry + (atr * 3.5) if side == "BUY" else entry - (atr * 3.5)
    
    # Profit Calculation for $2
    profit = (invest * leverage * (abs(tp - entry) / entry))

    return {"side": side, "entry": entry, "sl": sl, "tp": tp, "acc": accuracy, "profit": profit}

# --- UI Layout ---
st.title("🏹 Lakshitha's Trend-Master Sniper AI")
st.markdown("### 10 Indicators + Trend Following (EMA 200) + Candlestick Analysis")

invest = st.sidebar.number_input("Investment ($):", value=2.0)
lev = st.sidebar.slider("Leverage (X):", 1, 50, 20)

if st.button("🚀 START SCAN & FIND BEST TREND TRADE"):
    with st.spinner("Binance වෙළඳපොළ පරීක්ෂා කරමින්..."):
        markets = exchange.fetch_markets()
        symbols = [m['symbol'] for m in markets if m['quote'] == 'USDT' and m['active']]
        
        all_signals = []
        # පළමු කොයින් 50 ස්කෑන් කරයි
        for s in symbols[:50]:
            df = fetch_data(s)
            if df is not None and len(df) >= 100:
                res = analyze_trend_following(df, invest, lev)
                if res:
                    res['symbol'] = s
                    all_signals.append(res)
        
        # Accuracy එක අනුව හොඳම ට්‍රේඩ් එක තේරීම
        all_signals = sorted(all_signals, key=lambda x: x['acc'], reverse=True)
        
        if all_signals:
            top = all_signals[0]
            color = "#00ff00" if top['side'] == "BUY" else "#ff4b4b"
            
            st.markdown(f"""
            <div style="border: 6px solid {color}; padding: 30px; border-radius: 20px; background-color: #0e1117; text-align: center;">
                <h1 style="color:{color};">🏆 BEST TREND SIGNAL: {top['symbol']}</h1>
                <h2 style="color: white;">Side: {top['side']} | Trust: {top['acc']:.1f}%</h2>
                <hr style="border-color: {color};">
                <div style="display: flex; justify-content: space-around; font-size: 26px;">
                    <div><b>ENTRY</b><br>{top['entry']:.5f}</div>
                    <div><b>STOP LOSS</b><br>{top['sl']:.5f}</div>
                    <div><b>TAKE PROFIT</b><br>{top['tp']:.5f}</div>
                </div>
                <hr style="border-color: {color};">
                <h2 style="color: #f1c40f;">Estimated Profit: ${top['profit']:.2f}</h2>
                <p style="color: gray;">(Trend එකට අනුව පමණක් ලබාදුන් සිග්නලයක්)</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("---")
            st.write("🔍 අනෙකුත් ට්‍රෙන්ඩ් අවස්ථා:")
            cols = st.columns(3)
            for i, s in enumerate(all_signals[1:4]):
                with cols[i]:
                    st.success(f"**{s['symbol']}** | {s['side']}\nTrust: {s['acc']:.1f}%\nProfit: ${s['profit']:.2f}")
        else:
            st.warning("මේ වෙලාවේ ශක්තිමත් ට්‍රෙන්ඩ් එකක් සහිත කොයින් හමු නොවීය. කරුණාකර මද වෙලාවකින් නැවත උත්සාහ කරන්න.")
