import streamlit as st
import ccxt

st.set_page_config(page_title="Lakshitha Sniper AI")

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Pro Trader Access")
    pwd = st.text_input("මුරපදය:", type="password")
    if st.button("Login"):
        if pwd == "1234":
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("වැරදියි!")
    st.stop()

st.title("🚀 Lakshitha's Sniper Scanner")
exchange = ccxt.binance()

if st.button("🚀 Start Scan"):
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    for c in coins:
        try:
            ticker = exchange.fetch_ticker(c)
            price = ticker['last']
            st.success(f"✅ {c} | Price: {price}")
        except:
            st.error(f"❌ {c} Error")
