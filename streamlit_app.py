import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta

# --- UI Setup ---
st.set_page_config(page_title="Lakshitha Precision AI", layout="wide")

# මුරපදය (Security)
MY_PASSWORD = "1234" 

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Pro Trader Access")
    pwd = st.text_input("මුරපදය ඇතුළත් කරන්න:", type="password")
    if st.button("Login"):
        if pwd == MY_PASSWORD:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("වැරදි මුරපදයක්!")
    st.stop()

# --- Main App ---
st.title("🚀 Lakshitha's Sniper Scanner")

st.sidebar.header("⚙️ Settings")
invest = st.sidebar.number_input("Investment ($):", value=10.0)
lev = st.sidebar.slider("Leverage (X):", 1, 50, 10)
tf = st.sidebar.selectbox("Timeframe:", ["5m", "15m", "1h", "4h", "1d"])

exchange = ccxt.binance()

def analyze_market(symbol, timeframe):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=250)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        # Technical Indicators
        df['ema200'] = ta.ema(df['close'], length=200)
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Support/Resistance (Pivot)
        last_high, last_low, last_close = df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        pivot = (last_high + last_low + last_close) / 3
        res1 = (2 * pivot) - last_low
        sup1 = (2 * pivot) - last_high
        
        # Candle Analysis
        last = df.iloc[-1]
        body = abs(last['close'] - last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        
        # Accuracy % Logic
        score = 0
        if last['close'] > df['ema200'].iloc[-1]: score += 20
        if 40 < last['rsi'] < 60: score += 15
        if lower_wick > (body * 1.5): score += 25
        if last['close'] < sup1 * 1.02: score += 20
        if last['volume'] > ta.ema(df['volume'], 20).iloc[-1]: score += 20
        
        acc = max(min(score, 98), 40)
        return acc, last['close'], last['atr'], res1, sup1, score > 50
    except: return 0, 0, 0, 0, 0, True

st.subheader(f"🔍 Market Scan ({tf})")
if st.button("🚀 Start Scan"):
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'AVAX/USDT', 'DOGE/USDT', 'LINK/USDT']
    for c in coins:
        acc, price, atr, r1, s1, is_buy = analyze_market(c, tf)
        if acc > 60:
            color = "#00ff00" if is_buy else "#ff4b4b"
            tp = price + (atr * 3) if is_buy else price - (atr * 3)
            sl = price - (atr * 1.5) if is_buy else price + (atr * 1.5)
            
            st.markdown(f"""
            <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #0e1117;">
                <h2 style="color:{color};">{c} | {'🟢 BUY' if is_buy else '🔴 SELL'} | Accuracy: {acc}%</h2>
                <p>📉 Support: {s1:.4f} | 📈 Resistance: {r1:.4f}</p>
                <p>💰 Entry: {price} | 🎯 TP: {tp:.4f} | 🛑 SL: {sl:.4f}</p>
            </div>
            """, unsafe_allow_all_html=True)
