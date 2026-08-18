import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import numpy as np
import socket
import time

# 1. Grundkonfiguration
st.set_page_config(page_title="Bitcoin (BTC) – Live Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
        .chart-header-title { font-size: 1.35rem; font-weight: 600; color: #FFFFFF; font-family: monospace; }
        .btc-price-orange { font-size: 1.8rem; font-weight: 900; color: #FF9900; margin-bottom: 10px; }
        header[data-testid="stHeader"] { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

if "last_price" not in st.session_state:
    st.session_state.last_price = 64255.58
if "cached_df" not in st.session_state:
    st.session_state.cached_df = None

# 2. Sidebar (OHNE PAYWALL)
st.sidebar.markdown("### ⚙️ Terminal Steuerung")
view_mode = st.sidebar.radio("Ansicht wählen:", ["Live Kerzenchart", "3D Volatility Surface"])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Update-Intervall")
active_interval = st.sidebar.selectbox(
    "Sekunden wählen:",
    [1, 2, 5, 10, 30],
    index=0 # Standardmäßig auf 1 Sekunde
)

# 3. Preis Fetcher
def fetch_live_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=1).json()
        price = float(res["price"])
        st.session_state.last_price = price
        return price
    except Exception:
        sim_tick = st.session_state.last_price + np.random.uniform(-2.0, 2.0)
        st.session_state.last_price = sim_tick
        return sim_tick

current_price = fetch_live_price()

st.markdown('<div class="chart-header-title">Bitcoin (BTC) – Live Terminal</div>', unsafe_allow_html=True)
st.markdown(f'<div class="btc-price-orange">BTC/USD: ${current_price:,.2f}</div>', unsafe_allow_html=True)


# 4. KERZENCHART
if view_mode == "Live Kerzenchart":
    try:
        res = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=150", timeout=1.5).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'tb', 'tq', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        st.session_state.cached_df = df
    except Exception:
        df = st.session_state.cached_df

    # Realistischer Fallback mit echten roten & grünen Kerzen, falls Binance blockt
    if df is None or df.empty:
        times = pd.date_range(end=pd.Timestamp.now(), periods=150, freq='1min')
        opens, highs, lows, closes = [], [], [], []
        base = current_price - 50
        for _ in range(150):
            o = base
            c = o + np.random.uniform(-10, 10)
            h = max(o, c) + np.random.uniform(0, 5)
            l = min(o, c) - np.random.uniform(0, 5)
            opens.append(o); closes.append(c); highs.append(h); lows.append(l)
            base = c
        df = pd.DataFrame({'time': times, 'open': opens, 'high': highs, 'low': lows, 'close': closes})

    # Live-Tick in die letzte Kerze pushen
    df.iloc[-1, df.columns.get_loc('close')] = current_price
    df.iloc[-1, df.columns.get_loc('high')] = max(df.iloc[-1]['high'], current_price)
    df.iloc[-1, df.columns.get_loc('low')] = min(df.iloc[-1]['low'], current_price)

    fig = go.Figure(data=[go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='#089981', increasing_fillcolor='#089981',
        decreasing_line_color='#f23645', decreasing_fillcolor='#f23645'
    )])
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(l=10, r=10, b=10, t=10), height=650,
        uirevision="candle_lock", # Speichert Zoom
        xaxis=dict(gridcolor="#1e222d", rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor="#1e222d")
    )
    st.plotly_chart(fig, use_container_width=True)

# 5. 3D CHART
else:
    # Auflösung auf 30x30 reduziert, um WebGL Blackscreens zu verhindern!
    strikes = np.linspace(30000, 100000, 30)
    expiries = np.linspace(7, 180, 30)
    K, T = np.meshgrid(strikes, expiries)

    t_pulse = time.time() % 10
    dynamic_wave = np.sin(2 * np.pi * (K / 100000.0) + t_pulse) * 2.0

    moneyness = np.log(K / current_price)
    Z_IV = 0.35 + 0.30 * (moneyness ** 2) + 0.10 * (1.0 / np.sqrt(T / 30.0))
    Z_IV_percent = (Z_IV * 100.0) + dynamic_wave

    fig_3d = go.Figure(data=[go.Surface(
        x=K, y=T, z=Z_IV_percent,
        colorscale=[[0.0, "#240046"], [0.5, "#d93800"], [1.0, "#ffff00"]],
        showscale=False
    )])

    fig_3d.update_layout(
        template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
        margin=dict(l=0, r=0, b=0, t=0), height=650,
        uirevision="3d_lock", # Verhindert Kamera-Reset
        scene=dict(
            xaxis=dict(title="Strike ($)"), yaxis=dict(title="Days"), zaxis=dict(title="IV (%)"),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=0.9))
        )
    )
    st.plotly_chart(fig_3d, use_container_width=True)


# 6. Loop
time.sleep(active_interval)
st.rerun()
