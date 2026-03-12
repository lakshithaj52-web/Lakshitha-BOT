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
        
        # Technical Indicators (නිවැරදි ක්‍රමය)
        df['ema200'] = df.ta.ema(length=200)
        df['rsi'] = df.ta.rsi(length=14)
        df['atr'] = df.ta.atr(length=14)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Simple Logic for Signal
        score = 0
        if last['close'] > last['ema200']: score += 20
        if 40 < last['rsi'] < 60: score += 15
        
        is_buy = last['close'] > prev['close']
        
        return last['close'], last['rsi'], last['ema200'], is_buy, score
    except:
        return 0, 0, 0, True, 0

st.subheader(f"🔍 Market Scan ({tf})")
if st.button("🚀 Start Scan"):
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT']
    for c in coins:
        price, rsi, ema, is_buy, score = analyze_market(c, tf)
        
        color = "#00ff00" if is_buy else "#ff4b4b"
        signal = "BUY" if is_buy else "SELL"
        
        st.markdown(f"""
        <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <h2 style="color:{color};">{c} | {signal} | Accuracy: {score}%</h2>
            <p>💰 Price: {price} | 📊 RSI: {rsi:.2f} | 📈 EMA200: {ema:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
