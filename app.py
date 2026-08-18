import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import numpy as np
import time

# 1. Page Config
st.set_page_config(page_title="Bitcoin Live Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp { background-color: #050505 !important; color: #FFFFFF !important; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }
        .btc-header { font-family: monospace; font-size: 1.3rem; color: #AAAAAA; margin-bottom: 0px; }
        .btc-price { font-size: 2.2rem; font-weight: 800; color: #FF9900; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Session State Initialisierung
if "btc_price" not in st.session_state:
    st.session_state.btc_price = 65000.0
if "candle_df" not in st.session_state:
    st.session_state.candle_df = None

# Sidebar
st.sidebar.title("⚙️ Terminal Steuerung")
view_mode = st.sidebar.radio("Ansicht wählen:", ["Live Kerzenchart", "3D Volatility Surface"])
update_sec = st.sidebar.slider("Update-Intervall (Sekunden):", min_value=1, max_value=10, value=1)


# 2. Datenbeschaffung (Historie fest eingefroren, nur neuste Kerze bewegt sich)
def get_crypto_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    price = st.session_state.btc_price
    
    # Preis abrufen
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", headers=headers, timeout=1.0).json()
        if "price" in res:
            price = float(res["price"])
            st.session_state.btc_price = price
    except Exception:
        price += np.random.normal(0, 2.0)
        st.session_state.btc_price = price

    # Einmaliges Laden der Historie
    if st.session_state.candle_df is None:
        try:
            res_k = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100", headers=headers, timeout=1.5).json()
            if isinstance(res_k, list) and len(res_k) > 0:
                df = pd.DataFrame(res_k, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'tb', 'tq', 'ignore'])
                df['time'] = pd.to_datetime(df['time'], unit='ms')
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col].astype(float)
                st.session_state.candle_df = df
        except Exception:
            pass

    # Fallback mit simulierter Historie
    if st.session_state.candle_df is None:
        times = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1min')
        returns = np.random.normal(0, 15, 100)
        closes = price + np.cumsum(returns)
        opens = closes - returns
        highs = np.maximum(opens, closes) + np.abs(np.random.normal(5, 3, 100))
        lows = np.minimum(opens, closes) - np.abs(np.random.normal(5, 3, 100))
        st.session_state.candle_df = pd.DataFrame({
            'time': times, 'open': opens, 'high': highs, 'low': lows, 'close': closes
        })
    
    df = st.session_state.candle_df.copy()
    
    # NUR DIE ALLERLETZTE KERZE (die neu entsteht) wird angepasst:
    df.iloc[-1, df.columns.get_loc('close')] = price
    df.iloc[-1, df.columns.get_loc('high')] = max(df.iloc[-1]['high'], price)
    df.iloc[-1, df.columns.get_loc('low')] = min(df.iloc[-1]['low'], price)

    return price, df


# 3. KERZENCHART FRAGMENT (Superflüssig & bewegt nur neuste Kerze)
@st.fragment(run_every=update_sec)
def render_candle_view():
    price, df = get_crypto_data()
    
    st.markdown('<div class="btc-header">Bitcoin (BTC/USDT) Live Terminal</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="btc-price">${price:,.2f}</div>', unsafe_allow_html=True)

    fig = go.Figure(data=[go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='#00FF88',
        increasing_fillcolor='#00FF88',
        decreasing_line_color='#FF0055',
        decreasing_fillcolor='#FF0055',
        name="BTC/USDT"
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#050505",
        plot_bgcolor="#050505",
        margin=dict(l=10, r=10, b=10, t=10),
        height=680,
        uirevision="candle_lock",
        xaxis=dict(gridcolor="#151515", rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor="#151515", side="right")
    )
    st.plotly_chart(fig, use_container_width=True, key="live_candlestick")


# 4. 3D-VIEW (Ohne automatisches Rerender-Flackern, manueller Refresh-Button für stabile Drehung)
def render_3d_view():
    price = st.session_state.btc_price
    
    st.markdown('<div class="btc-header">Bitcoin 3D Volatility Surface</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="btc-price">${price:,.2f}</div>', unsafe_allow_html=True)

    if st.button("🔄 3D Surface manuell aktualisieren"):
        fetch_price = get_crypto_data()

    strikes = np.linspace(price * 0.6, price * 1.4, 30)
    expiries = np.linspace(7, 180, 30)
    K, T = np.meshgrid(strikes, expiries)

    moneyness = np.log(K / price)
    Z_IV = (0.35 + 0.25 * (moneyness ** 2) + 0.08 * (1.0 / np.sqrt(T / 30.0))) * 100.0

    fig_3d = go.Figure(data=[go.Surface(
        x=K, y=T, z=Z_IV,
        colorscale=[
            [0.0, "#0D0887"],
            [0.35, "#6A00A8"],
            [0.70, "#B12A90"],
            [1.0, "#FCA636"]
        ],
        showscale=True,
        colorbar=dict(title="IV (%)", len=0.6)
    )])

    fig_3d.update_layout(
        template="plotly_dark",
        paper_bgcolor="#050505",
        plot_bgcolor="#050505",
        margin=dict(l=0, r=0, b=0, t=0),
        height=680,
        uirevision="3d_camera_static",
        scene=dict(
            xaxis=dict(title="Strike ($)", gridcolor="#333333"),
            yaxis=dict(title="Days to Expiry", gridcolor="#333333"),
            zaxis=dict(title="Implied Volatility (%)", gridcolor="#333333"),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=0.8))
        )
    )
    st.plotly_chart(fig_3d, use_container_width=True, key="static_3d_surface")


# 5. Router
if view_mode == "Live Kerzenchart":
    render_candle_view()
else:
    render_3d_view()
