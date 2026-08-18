import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import numpy as np
import socket
import time

# 1. Grundkonfiguration
st.set_page_config(page_title="Bitcoin (BTC) – Live Terminal", layout="wide", initial_sidebar_state="expanded")

# Pure Black Theme (#000000) & Custom Styling
st.markdown("""
    <style>
        .stApp, div[data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', sans-serif !important;
        }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }

        [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {
            color: #FF9900 !important;
            background-color: #111111 !important;
            border: 1px solid #FF9900 !important;
            border-radius: 4px !important;
            margin: 5px !important;
        }

        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .chart-header-title {
            font-size: 1.35rem;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 2px;
            font-family: monospace, sans-serif;
        }
        .btc-price-orange {
            font-size: 1.8rem;
            font-weight: 900;
            color: #FF9900;
            text-shadow: 0 0 10px rgba(255, 153, 0, 0.4);
            margin-bottom: 10px;
        }

        .paywall-banner {
            background: rgba(255, 0, 85, 0.15);
            border: 1px solid #FF0055;
            color: #FF4477;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# IP-Erkennung für Handys
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# 2. Sidebar Controls & Paywall
st.sidebar.markdown("### ⚙️ Terminal Steuerung")
view_mode = st.sidebar.radio(
    "Ansicht wählen:", 
    ["3D Volatility Surface (Accurate)", "Live Kerzenchart"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔒 PRO Freischaltung")
pro_key = st.sidebar.text_input("PRO Key eingeben:", type="password", help="Passwort für Updates unter 30 Sek.")
is_pro = (pro_key == "pro123")  # Passwort für Freischaltung

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Update-Intervall")
requested_interval_name = st.sidebar.selectbox(
    "Intervall wählen:",
    ["30 Sekunden (Kostenlos)", "15 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra Live PRO)"]
)

interval_map = {
    "30 Sekunden (Kostenlos)": 30,
    "15 Sekunden (PRO)": 15,
    "5 Sekunden (PRO)": 5,
    "1 Sekunde (Ultra Live PRO)": 1
}

requested_sec = interval_map[requested_interval_name]

# Paywall Logik: Unter 30s wird ohne PRO Key auf 30s gedrosselt
if requested_sec < 30 and not is_pro:
    active_interval = 30
    paywall_active = True
else:
    active_interval = requested_sec
    paywall_active = False

if paywall_active:
    st.sidebar.markdown("""
        <div class="paywall-banner">
            🔒 Updates unter 30s gesperrt!<br>
            Bitte PRO Key eingeben. (Läuft auf 30s)
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Mobile Sync")
target_url = f"http://{LOCAL_IP}:8501"
st.sidebar.caption(f"Netzwerk URL: `{target_url}`")
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={target_url}&color=FF9900&bgcolor=000000"
st.sidebar.image(qr_api_url, caption="Mit Handy scannen", width=150)


# 3. Live BTC Preis Abrufen
def get_btc_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=1.5).json()
        return float(res["price"])
    except Exception:
        return st.session_state.get("last_price", 64255.58)

current_price = get_btc_price()
st.session_state.last_price = current_price

# Header
st.markdown('<div class="chart-header-title">Bitcoin (BTC) – Live Terminal</div>', unsafe_allow_html=True)
st.markdown(f'<div class="btc-price-orange">BTC/USD: ${current_price:,.2f}</div>', unsafe_allow_html=True)

if paywall_active:
    st.markdown("""
        <div class="paywall-banner">
            🔒 PAYWALL AKTIV: Intervall unter 30 Sekunden erfordert PRO Status.
        </div>
    """, unsafe_allow_html=True)


# 4. ANSICHT 1: Mathematisch korrekte 3D Volatilitätsfläche (IV >= 0%)
if view_mode == "3D Volatility Surface (Accurate)":
    strikes = np.linspace(30000, 100000, 50)
    expiries = np.linspace(7, 180, 50)
    K, T = np.meshgrid(strikes, expiries)

    # Volatilität ist mathematisch immer positiv (IV >= 0%)
    moneyness = np.log(K / current_price)
    Z_IV = 0.35 + 0.30 * (moneyness ** 2) + 0.10 * (1.0 / np.sqrt(T / 30.0))
    Z_IV_percent = Z_IV * 100.0

    # Original Farbschema (Dunkelviolett -> Red/Orange -> Yellow)
    image_colorscale = [
        [0.0, "#240046"],   # Tiefes Violett
        [0.25, "#5a007a"],  # Indigo
        [0.5, "#d93800"],   # Dunkelorange
        [0.75, "#ff8c00"],  # Helles Orange
        [1.0, "#ffff00"]    # Knallgelb
    ]

    fig_3d = go.Figure(data=[go.Surface(
        x=K, y=T, z=Z_IV_percent,
        colorscale=image_colorscale,
        showscale=True,
        colorbar=dict(title="IV (%)", len=0.6),
        contours=dict(
            z=dict(show=True, usecolormap=False, color="rgba(0,0,0,0.3)", project=dict(z=True))
        ),
        lighting=dict(ambient=0.7, diffuse=0.9, fresnel=0.2, specular=0.6, roughness=0.3)
    )])

    fig_3d.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, b=0, t=0),
        height=650,
        scene=dict(
            xaxis=dict(title="Strike Price ($)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)"),
            yaxis=dict(title="Time to Expiry (Tage)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)"),
            zaxis=dict(title="Implied Volatility (%)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)", range=[0, max(Z_IV_percent.max(), 120)]),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=0.9)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.75)
        )
    )

    st.plotly_chart(fig_3d, use_container_width=True)


# 5. ANSICHT 2: Reiner Live Kerzenchart (mit Scroll-Zoom & ohne Overlays)
elif view_mode == "Live Kerzenchart":
    try:
        res = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100", timeout=2).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)

        # Aktuellste Kerze mit dem Live-Tick abgleichen
        df.iloc[-1, df.columns.get_loc('close')] = current_price
        if current_price > df.iloc[-1]['high']:
            df.iloc[-1, df.columns.get_loc('high')] = current_price
        if current_price < df.iloc[-1]['low']:
            df.iloc[-1, df.columns.get_loc('low')] = current_price

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name="BTC/USDT",
            increasing_line_color='#089981', decreasing_line_color='#f23645'
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=10, r=10, b=10, t=10),
            height=650,
            xaxis=dict(gridcolor="#1e222d", rangeslider=dict(visible=False)),
            yaxis=dict(gridcolor="#1e222d")
        )

        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    except Exception as e:
        st.error(f"Fehler beim Laden des Kerzencharts: {e}")

# 6. Dynamisches Rerender-Intervall
time.sleep(active_interval)
st.rerun()
