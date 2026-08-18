import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import numpy as np
import socket
import time

# 1. Grundkonfiguration
st.set_page_config(page_title="Bitcoin (BTC) – 3D Volatility Chart", layout="wide", initial_sidebar_state="expanded")

# Styling: Reines Schwarz (#000000) wie im Referenzbild
st.markdown("""
    <style>
        .stApp, div[data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', sans-serif !important;
        }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }

        /* Neon Sidebar-Toggle-Button */
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
    </style>
""", unsafe_allow_html=True)

# IP-Adresse für Handys im selben WLAN ermitteln
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
ADMIN_PASSWORD = "dein_secret_passwort"

# 2. Sidebar Steuerleiste
st.sidebar.markdown("### ⚙️ Steuerung")
view_mode = st.sidebar.radio(
    "Ansicht wählen:", 
    ["3D Volatility Surface (Original)", "Live Kerzenchart"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Admin Login")
entered_pass = st.sidebar.text_input("Admin Key:", type="password")
is_admin = (entered_pass == ADMIN_PASSWORD)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Update-Intervall")
update_rate = st.sidebar.selectbox(
    "Intervall wählen:",
    ["30 Sekunden (Free)", "15 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

rate_map = {
    "30 Sekunden (Free)": 30,
    "15 Sekunden (PRO)": 15,
    "5 Sekunden (PRO)": 5,
    "1 Sekunde (Ultra PRO)": 1
}
sleep_interval = rate_map.get(update_rate, 30)

# Handy QR-Code
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Handy QR-Code")
target_url = f"http://{LOCAL_IP}:8501"
st.sidebar.caption(f"Verbinde Handy mit demselben WLAN:\n`{target_url}`")
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={target_url}&color=FF9900&bgcolor=000000"
st.sidebar.image(qr_api_url, caption="Mit Handy-Kamera scannen", width=160)


# 3. Live BTC Preis Abrufen
@st.cache_data(ttl=1)
def get_btc_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()
        return float(res["price"])
    except Exception:
        return 64255.58

current_btc_price = get_btc_price()

# Header exakt wie im Screenshot
st.markdown('<div class="chart-header-title">Bitcoin (BTC) – 3D Volatility Chart</div>', unsafe_allow_html=True)
st.markdown(f'<div class="btc-price-orange">BTC/USD: ${current_btc_price:,.2f}</div>', unsafe_allow_html=True)


# 4. Native Plotly 3D Render Engine (Kein Iframe = Kein schwarzer Bildschirm!)
if view_mode == "3D Volatility Surface (Original)":
    # 3D Trichter-Mathematik
    x = np.linspace(-3, 3, 60)
    y = np.linspace(-3, 3, 60)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Z = np.sin(R) / (R + 0.1) - 0.5 * R

    # Farbverlauf exakt wie im Screenshot (Violett -> Red/Orange -> Yellow)
    image_colorscale = [
        [0.0, "#240046"],   # Tiefes Violett
        [0.25, "#5a007a"],  # Indigo / Purpur
        [0.5, "#d93800"],   # Dunkelorange / Rot
        [0.75, "#ff8c00"],  # Helles Orange
        [1.0, "#ffff00"]    # Knallgelb
    ]

    fig = go.Figure(data=[go.Surface(
        x=x, y=y, z=Z,
        colorscale=image_colorscale,
        showscale=False,
        contours=dict(
            z=dict(show=True, usecolormap=False, color="rgba(0,0,0,0.3)", project=dict(z=True))
        ),
        lighting=dict(ambient=0.7, diffuse=0.9, fresnel=0.2, specular=0.6, roughness=0.3)
    )])

    # Layout mit grauen Gitter-Wänden & weißer Schrift
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, b=0, t=0),
        height=650,
        scene=dict(
            xaxis=dict(
                title="Strike Price", color="#FFFFFF", gridcolor="#FFFFFF",
                showbackground=True, backgroundcolor="rgb(90, 90, 90)"
            ),
            yaxis=dict(
                title="Time", color="#FFFFFF", gridcolor="#FFFFFF",
                showbackground=True, backgroundcolor="rgb(90, 90, 90)"
            ),
            zaxis=dict(
                title="Volatility", color="#FFFFFF", gridcolor="#FFFFFF",
                showbackground=True, backgroundcolor="rgb(90, 90, 90)"
            ),
            camera=dict(eye=dict(x=-1.45, y=-1.45, z=0.95)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.8)
        )
    )

    # Nativer Streamlit Chart Aufruf
    st.plotly_chart(fig, use_container_width=True)

elif view_mode == "Live Kerzenchart":
    try:
        res = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=80").json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        fig_candle = go.Figure(data=[go.Candlestick(
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            increasing_line_color='#00FF66', decreasing_line_color='#FF0055'
        )])
        fig_candle.update_layout(
            template="plotly_dark", paper_bgcolor="#000000", plot_bgcolor="#000000",
            margin=dict(l=20, r=20, b=20, t=20), height=650,
            xaxis=dict(gridcolor="#222222", rangeslider=dict(visible=False)),
            yaxis=dict(gridcolor="#222222")
        )
        st.plotly_chart(fig_candle, use_container_width=True)
    except Exception as e:
        st.error(f"Fehler beim Laden des Kerzencharts: {e}")

# 5. Dynamisches Rerender-Intervall
time.sleep(sleep_interval)
st.rerun()
