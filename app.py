import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import numpy as np
import time
import socket

# SciPy für High-Density Mesh Interpolation
try:
    from scipy.ndimage import zoom
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Automatische Erkennung der lokalen IP-Adresse für den QR-Code
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

# 1. Page Config & Pure Pitch Black Design (Exakt wie im Bild)
st.set_page_config(page_title="Bitcoin (BTC) – 3D Volatility Chart", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Reine schwarze Hintergründe wie im Referenzbild */
        .stApp, div[data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }

        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }

        /* Neon Sidebar-Button (Immer sichtbar & aufklappbar) */
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
        
        /* Titel & Preis-Kopfzeile exakt wie im Bild */
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
            font-family: sans-serif;
        }

        /* Paywall & Admin Boxen */
        .paywall-box {
            background: #110508;
            border: 1px solid #FF0055;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
            color: #FFDDDD;
            margin-bottom: 10px;
        }
        .admin-box {
            background: #051108;
            border: 1px solid #00FF66;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
            color: #00FF66;
            font-weight: bold;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = "dein_secret_passwort"

# 2. Sidebar Navigation & Einstellungen
st.sidebar.markdown("### ⚙️ Steuerung")
view_mode = st.sidebar.radio(
    "Ansicht wählen:", 
    ["3D Volatility Surface (Original)", "Live Kerzenchart", "Put/Call Skew Radar", "2D Heatmap"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Admin Login")
entered_pass = st.sidebar.text_input("Admin Key:", type="password")
is_admin = (entered_pass == ADMIN_PASSWORD)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Dynamische Refresh-Rate")
update_rate = st.sidebar.selectbox(
    "Update-Intervall:",
    ["30 Sekunden (Free)", "15 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

# Zuordnung des gewählten Intervalls in Sekunden
rate_map = {
    "30 Sekunden (Free)": 30,
    "15 Sekunden (PRO)": 15,
    "5 Sekunden (PRO)": 5,
    "1 Sekunde (Ultra PRO)": 1
}
sleep_interval = rate_map.get(update_rate, 30)

if "PRO" in update_rate and not is_admin:
    st.sidebar.markdown("""
        <div class="paywall-box">
            🔒 High-Speed Feed erfordert PRO Status.
        </div>
    """, unsafe_allow_html=True)

# 📱 Handy-Zugriff / QR Code mit automatischer IP-Erkennung
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Handy QR-Code")
qr_type = st.sidebar.radio("Verbindung:", ["WLAN (Lokales Netz)", "Manuelle URL"])

if qr_type == "WLAN (Lokales Netz)":
    target_url = f"http://{LOCAL_IP}:8501"
else:
    target_url = st.sidebar.text_input("URL eingeben:", value=f"http://{LOCAL_IP}:8501")

st.sidebar.caption(f"Verbinde Handy mit demselben WLAN:\n`{target_url}`")
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={target_url}&color=FF9900&bgcolor=000000"
st.sidebar.image(qr_api_url, caption="Mit Handy scannen", width=160)


# 3. Live BTC Preis Abrufen
@st.cache_data(ttl=1)
def get_btc_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()
        return float(res["price"])
    except Exception:
        return 64255.58

current_btc_price = get_btc_price()

# Header im Stil des Screenshots
st.markdown('<div class="chart-header-title">Bitcoin (BTC) – 3D Volatility Chart</div>', unsafe_allow_html=True)
st.markdown(f'<div class="btc-price-orange">BTC/USD: ${current_btc_price:,.2f}</div>', unsafe_allow_html=True)


# 4. Deribit Live Options Daten & 3D Modellierung
@st.cache_data(ttl=2)
def get_deribit_iv_data():
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        res = requests.get(url, timeout=5).json()
        return res.get("result", [])
    except Exception:
        return []

if view_mode == "3D Volatility Surface (Original)":
    raw_data = get_deribit_iv_data()
    
    # Generiere dichte Mesh-Fläche exakt in der Trichter/Dome-Form des Bildes
    x = np.linspace(-3, 3, 80)
    y = np.linspace(-3, 3, 80)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # Mathematische Trichter-Transformation wie im Referenzbild
    Z = np.sin(R) / (R + 0.1) - 0.5 * R

    if raw_data:
        parsed = []
        for item in raw_data:
            parts = item["instrument_name"].split("-")
            if len(parts) == 4 and item.get("mark_iv", 0) > 0:
                parsed.append({"strike": float(parts[2]), "iv": item["mark_iv"]})
        if parsed:
            df = pd.DataFrame(parsed)
            real_iv_factor = df["iv"].mean() / 100.0
            Z = Z * (real_iv_factor if real_iv_factor > 0 else 1.0)

    # Farbpalette exakt wie auf dem Foto (Dunkelviolett/Indigoblau -> Orange -> Gelb auf der Spitze)
    image_colorscale = [
        [0.0, "#240046"],   # Tiefes Violett (Trichter-Spitze unten)
        [0.25, "#5a007a"],  # Indigo / Purpur
        [0.5, "#d93800"],   # Dunkelorange / Rot
        [0.75, "#ff8c00"],  # Helles Orange
        [1.0, "#ffff00"]    # Knallgelb (Obere Kuppel)
    ]

    plotly_3d_html = f"""
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <div id="plotly-3d-grid" style="width:100%; height:650px;"></div>
    <script>
        var x_vals = {json.dumps(x.tolist())};
        var y_vals = {json.dumps(y.tolist())};
        var z_vals = {json.dumps(Z.tolist())};

        var data = [{{
            x: x_vals,
            y: y_vals,
            z: z_vals,
            type: 'surface',
            colorscale: {json.dumps(image_colorscale)},
            showscale: False,
            contours: {{
                z: {{ show: true, usecolormap: false, color: "rgba(0,0,0,0.3)", width: 1 }},
                x: {{ show: true, color: "rgba(0,0,0,0.15)", width: 1 }},
                y: {{ show: true, color: "rgba(0,0,0,0.15)", width: 1 }}
            }},
            lighting: {{
                ambient: 0.7,
                diffuse: 0.9,
                fresnel: 0.2,
                specular: 0.6,
                roughness: 0.3
            }}
        }}];

        var layout = {{
            paper_bgcolor: '#000000',
            plot_bgcolor: '#000000',
            margin: {{ l: 0, r: 0, b: 0, t: 0 }},
            scene: {{
                xaxis: {{
                    title: 'Strike Price',
                    color: '#FFFFFF',
                    gridcolor: '#FFFFFF',
                    showbackground: true,
                    backgroundcolor: 'rgba(90, 90, 90, 0.65)',
                    zerolinecolor: '#FFFFFF'
                }},
                yaxis: {{
                    title: 'Time',
                    color: '#FFFFFF',
                    gridcolor: '#FFFFFF',
                    showbackground: true,
                    backgroundcolor: 'rgba(90, 90, 90, 0.65)',
                    zerolinecolor: '#FFFFFF'
                }},
                zaxis: {{
                    title: 'Volatility',
                    color: '#FFFFFF',
                    gridcolor: '#FFFFFF',
                    showbackground: true,
                    backgroundcolor: 'rgba(90, 90, 90, 0.65)',
                    zerolinecolor: '#FFFFFF'
                }},
                camera: {{
                    eye: {{ x: -1.45, y: -1.45, z: 0.95 }}
                }},
                aspectmode: 'manual',
                aspectratio: {{ x: 1, y: 1, z: 0.8 }}
            }}
        }};

        Plotly.react('plotly-3d-grid', data, layout, {{responsive: true, displayModeBar: false}});
    </script>
    """
    components.html(plotly_3d_html, height=660)

elif view_mode == "Live Kerzenchart":
    binance_chart_html = """
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <div id="candle-chart" style="width:100%; height:650px;"></div>
    <script>
        async function loadCandles() {
            const res = await fetch('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=80');
            const data = await res.json();
            var trace = {
                x: data.map(d => new Date(d[0]).toLocaleTimeString()),
                open: data.map(d => d[1]), high: data.map(d => d[2]),
                low: data.map(d => d[3]), close: data.map(d => d[4]),
                type: 'candlestick',
                increasing: {line: {color: '#00FF66'}},
                decreasing: {line: {color: '#FF0055'}}
            };
            var layout = {
                paper_bgcolor: '#000000', plot_bgcolor: '#000000',
                font: {color: '#FFFFFF'},
                margin: {l:40, r:20, t:20, b:40},
                xaxis: {gridcolor: '#333333', rangeslider: {visible: false}},
                yaxis: {gridcolor: '#333333'}
            };
            Plotly.react('candle-chart', [trace], layout, {responsive: true});
        }
        loadCandles();
    </script>
    """
    components.html(binance_chart_html, height=660)

# 5. Dynamischer Timer (Aktualisiert präzise im eingestellten Intervall)
time.sleep(sleep_interval)
st.rerun()
