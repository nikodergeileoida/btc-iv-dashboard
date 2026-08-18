import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import time

# 1. Konfiguration & Tiefschwarzer Style
st.set_page_config(page_title="BTC Live IV & Trading Terminal", layout="wide")

st.markdown("""
    <style>
        /* Schwarzer Hintergrund & Neon Styling */
        .stApp {
            background-color: #000000 !important;
            color: #00FFCC !important;
        }
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Live Preis Card */
        .price-card {
            background: linear-gradient(135deg, rgba(15,15,20,0.9) 0%, rgba(5,5,10,0.95) 100%);
            border: 1px solid #00FFCC;
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
            border-radius: 10px;
            padding: 12px 20px;
            text-align: center;
            margin-bottom: 15px;
        }
        .price-val {
            font-size: 2.2rem;
            font-weight: 800;
            color: #00FFCC;
            text-shadow: 0 0 10px rgba(0, 255, 204, 0.6);
        }
        /* Paywall Banner */
        .paywall-box {
            background: linear-gradient(135deg, rgba(40,10,20,0.9) 0%, rgba(20,5,10,0.95) 100%);
            border: 1px solid #FF0055;
            box-shadow: 0 0 20px rgba(255, 0, 85, 0.5);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            color: #FFDDDD;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Daten von Deribit abrufen (BTC Index Preis & IV Surface Data)
@st.cache_data(ttl=3)
def get_btc_price():
    try:
        res = requests.get("https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd", timeout=5).json()
        return res["result"]["index_price"]
    except Exception:
        return 0.0

@st.cache_data(ttl=10)
def get_deribit_iv_data():
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("result", [])
    except Exception:
        return []

@st.cache_data(ttl=10)
def get_btc_ohlc():
    # Binance API für Kerzenchart
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=40"
        res = requests.get(url, timeout=5).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['time'] = pd.to_datetime(df['time'], unit='ms').dt.strftime('%H:%M')
        return df
    except Exception:
        return pd.DataFrame()

# 3. Live Price Header
btc_price = get_btc_price()
st.markdown(f"""
    <div class="price-card">
        <span style="font-size: 1.1rem; color: #888888; text-transform: uppercase; letter-spacing: 2px;">Bitcoin Live Index Price</span><br>
        <span class="price-val">${btc_price:,.2f} USD</span>
    </div>
""", unsafe_allow_html=True)

# 4. Sidebar Einstellungen & Paywall Logik
st.sidebar.markdown("### ⚙️ Terminal Control")
view_mode = st.sidebar.radio(
    "Visualisierung wählen:", 
    ["3D Surface", "2D Heatmap", "2D Volatility Smiles", "Live Kerzenchart (Candlestick)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Live Feed Rate")
update_rate = st.sidebar.selectbox(
    "Update Intervall:",
    ["30 Sekunden (Kostenlos)", "20 Sekunden (PRO)", "10 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

is_pro = "PRO" in update_rate
actual_refresh_sec = 30

if is_pro:
    st.markdown("""
        <div class="paywall-box">
            <h3 style="color: #FF0055; margin: 0;">🔒 PRO FUNKTION GESPERRT</h3>
            <p style="margin: 5px 0;">Updates unter 30 Sekunden (20s, 10s, 5s, 1s) erfordern ein <b>VIP Subscription Upgrade</b>.</p>
            <p style="font-size: 0.85rem; color: #FFAAAA;">Signal wird auf das kostenlose 30-Sekunden Intervall drosselt.</p>
        </div>
    """, unsafe_allow_html=True)
    actual_refresh_sec = 30
else:
    actual_refresh_sec = 30

# 5. Visualisierungen (WebGL rendert mit 60-120 FPS auf dem Client)
if view_mode == "Live Kerzenchart (Candlestick)":
    ohlc_df = get_btc_ohlc()
    if not ohlc_df.empty:
        times = ohlc_df['time'].tolist()
        opens = ohlc_df['open'].tolist()
        highs = ohlc_df['high'].tolist()
        lows = ohlc_df['low'].tolist()
        closes = ohlc_df['close'].tolist()

        candlestick_html = f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <div id="plotly-candle" style="width:100%; height:700px;"></div>
        <script>
            var trace = {{
                x: {json.dumps(times)},
                open: {json.dumps(opens)},
                high: {json.dumps(highs)},
                low: {json.dumps(lows)},
                close: {json.dumps(closes)},
                type: 'candlestick',
                increasing: {{line: {{color: '#00FFCC'}}, fillcolor: '#00FFCC'}},
                decreasing: {{line: {{color: '#FF0055'}}, fillcolor: '#FF0055'}}
            }};
            var layout = {{
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                font: {{ color: '#00FFCC' }},
                title: 'BTC/USDT Realtime 1m Candlestick Chart',
                xaxis: {{ gridcolor: '#222222', rangeslider: {{visible: false}} }},
                yaxis: {{ gridcolor: '#222222' }},
                margin: {{ l: 50, r: 20, b: 40, t: 40 }}
            }};
            Plotly.react('plotly-candle', [trace], layout, {{responsive: true, displayModeBar: false}});
        </script>
        """
        components.html(candlestick_html, height=720)

else:
    raw_data = get_deribit_iv_data()
    if raw_data:
        parsed = []
        for item in raw_data:
            parts = item["instrument_name"].split("-")
            if len(parts) == 4 and item.get("mark_iv", 0) > 0:
                parsed.append({
                    "expiry": parts[1],
                    "strike": float(parts[2]),
                    "iv": item["mark_iv"]
                })

        df = pd.DataFrame(parsed)
        if not df.empty:
            pivot = df.pivot_table(index="strike", columns="expiry", values="iv", aggfunc="mean").dropna()
            strikes = pivot.index.tolist()
            expiries = pivot.columns.tolist()
            z_values = pivot.values.tolist()

            # 3D Surface
            if view_mode == "3D Surface":
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-surface" style="width:100%; height:720px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'surface',
                        colorscale: 'Plasma',
                        colorbar: {{ len: 0.8, thickness: 15, tickfont: {{color: '#00FFCC'}} }}
                    }}];
                    var layout = {{
                        paper_bgcolor: '#000000',
                        plot_bgcolor: '#000000',
                        font: {{ color: '#00FFCC' }},
                        margin: {{ l: 0, r: 0, b: 0, t: 10 }},
                        scene: {{
                            xaxis: {{ title: 'Expiry', gridcolor: '#333333' }},
                            yaxis: {{ title: 'Strike ($)', gridcolor: '#333333' }},
                            zaxis: {{ title: 'IV (%)', gridcolor: '#333333' }},
                            aspectmode: 'manual',
                            aspectratio: {{ x: 1.1, y: 1.1, z: 0.5 }},
                            camera: {{ eye: {{ x: 0.95, y: 0.95, z: 0.6 }} }}
                        }}
                    }};
                    Plotly.react('plotly-surface', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=740)

            # 2D Heatmap
            elif view_mode == "2D Heatmap":
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-heatmap" style="width:100%; height:720px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'heatmap',
                        colorscale: 'Plasma'
                    }}];
                    var layout = {{
                        paper_bgcolor: '#000000',
                        plot_bgcolor: '#000000',
                        font: {{ color: '#00FFCC' }},
                        xaxis: {{ title: 'Expiry', gridcolor: '#222222' }},
                        yaxis: {{ title: 'Strike ($)', gridcolor: '#222222' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-heatmap', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=740)

            # 2D Volatility Smiles
            elif view_mode == "2D Volatility Smiles":
                traces = []
                for exp in expiries:
                    traces.append({
                        "x": strikes,
                        "y": pivot[exp].tolist(),
                        "mode": "lines+markers",
                        "name": str(exp)
                    })
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-smiles" style="width:100%; height:720px;"></div>
                <script>
                    var data = {json.dumps(traces)};
                    var layout = {{
                        paper_bgcolor: '#000000',
                        plot_bgcolor: '#000000',
                        font: {{ color: '#00FFCC' }},
                        xaxis: {{ title: 'Strike ($)', gridcolor: '#222222' }},
                        yaxis: {{ title: 'IV (%)', gridcolor: '#222222' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-smiles', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=740)

# 6. Automatischer Loop (Aktualisierung alle 30 Sekunden im Free Tier)
time.sleep(actual_refresh_sec)
st.rerun()
