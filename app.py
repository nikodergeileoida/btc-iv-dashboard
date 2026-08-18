import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import time

# 1. Konfiguration & Dark Green Matrix / Emerald Style
st.set_page_config(page_title="BTC Terminal (Emerald Edition)", layout="wide")

st.markdown("""
    <style>
        /* Tiefschwarzer / Dunkelgrüner Hintergrund */
        .stApp {
            background-color: #030a05 !important;
            color: #00FF66 !important;
        }
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Paywall Box */
        .paywall-box {
            background: linear-gradient(135deg, rgba(5,30,12,0.9) 0%, rgba(2,15,5,0.95) 100%);
            border: 1px solid #00FF66;
            box-shadow: 0 0 15px rgba(0, 255, 102, 0.3);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            color: #CCFFDD;
            margin-bottom: 15px;
        }
        /* PayPal Button Styling */
        .paypal-btn {
            background-color: #0070BA;
            color: #FFFFFF !important;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin-top: 10px;
            box-shadow: 0 0 10px rgba(0, 112, 186, 0.5);
        }
        .paypal-btn:hover {
            background-color: #005EA6;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Bitcoin Live-Preis Banner (Aktualisiert jede 1 Sekunde via JS ohne Streamlit-Rerun)
btc_ticker_html = """
<div id="btc-card" style="
    background: linear-gradient(135deg, #051a0b 0%, #020b04 100%);
    border: 1px solid #00FF66;
    box-shadow: 0 0 20px rgba(0, 255, 102, 0.2);
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    font-family: sans-serif;
">
    <span style="font-size: 0.9rem; color: #00AA44; text-transform: uppercase; letter-spacing: 2px;">Bitcoin Live Index Price (1s Feed)</span><br>
    <span id="btc-price" style="font-size: 2.2rem; font-weight: 800; color: #00FF66; text-shadow: 0 0 10px rgba(0, 255, 102, 0.5);">Lade Preis...</span>
</div>

<script>
    async function updateBtcPrice() {
        try {
            const res = await fetch('https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd');
            const data = await res.json();
            const price = data.result.index_price;
            document.getElementById('btc-price').innerText = '$' + price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' USD';
        } catch (e) {
            console.error(e);
        }
    }
    updateBtcPrice();
    setInterval(updateBtcPrice, 1000); // Genau jede Sekunde
</script>
"""
components.html(btc_ticker_html, height=95)

# 3. Sidebar mit PRO Intervallen & PayPal Paywall
st.sidebar.markdown("### ⚙️ Terminal Control")
view_mode = st.sidebar.radio(
    "Visualisierung wählen:", 
    ["3D Surface", "2D Heatmap", "2D Volatility Smiles", "Live Kerzenchart (Candlestick)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Update Intervall")
update_rate = st.sidebar.selectbox(
    "Frequenz wählen:",
    ["30 Sekunden (Kostenlos)", "20 Sekunden (PRO)", "10 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

is_pro = "PRO" in update_rate

if is_pro:
    st.markdown("""
        <div class="paywall-box">
            <h3 style="color: #00FF66; margin: 0;">🔒 PRO UPGRADE ERFORDERLICH</h3>
            <p style="margin: 8px 0; font-size: 0.9rem;">Schnellere Signal-Updates (20s, 10s, 5s, 1s) stehen erst nach Freischaltung bereit.</p>
            <p style="font-size: 0.85rem; color: #88FFAA;">Jetzt freischalten für nur <b>9,99€ / Monat</b>:</p>
            <a href="https://www.paypal.com" target="_blank" class="paypal-btn">
                💳 Mit PayPal bezahlen
            </a>
        </div>
    """, unsafe_allow_html=True)

# 4. Daten-Funktionen
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
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=40"
        res = requests.get(url, timeout=5).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        df['time'] = pd.to_datetime(df['time'], unit='ms').dt.strftime('%H:%M')
        return df
    except Exception:
        return pd.DataFrame()

# 5. Charts Rendern (Dunkelgrüne Farbpalette)
if view_mode == "Live Kerzenchart (Candlestick)":
    ohlc_df = get_btc_ohlc()
    if not ohlc_df.empty:
        candlestick_html = f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <div id="plotly-candle" style="width:100%; height:680px;"></div>
        <script>
            var trace = {{
                x: {json.dumps(ohlc_df['time'].tolist())},
                open: {json.dumps(ohlc_df['open'].tolist())},
                high: {json.dumps(ohlc_df['high'].tolist())},
                low: {json.dumps(ohlc_df['low'].tolist())},
                close: {json.dumps(ohlc_df['close'].tolist())},
                type: 'candlestick',
                increasing: {{line: {{color: '#00FF66'}}, fillcolor: '#00FF66'}},
                decreasing: {{line: {{color: '#FF0055'}}, fillcolor: '#FF0055'}}
            }};
            var layout = {{
                paper_bgcolor: '#030a05',
                plot_bgcolor: '#030a05',
                font: {{ color: '#00FF66' }},
                title: 'BTC/USDT Realtime Candlestick Chart',
                xaxis: {{ gridcolor: '#09240f', rangeslider: {{visible: false}} }},
                yaxis: {{ gridcolor: '#09240f' }},
                margin: {{ l: 50, r: 20, b: 40, t: 40 }}
            }};
            Plotly.react('plotly-candle', [trace], layout, {{responsive: true, displayModeBar: false}});
        </script>
        """
        components.html(candlestick_html, height=700)

else:
    raw_data = get_deribit_iv_data()
    if raw_data:
        parsed = []
        for item in raw_data:
            parts = item["instrument_name"].split("-")
            if len(parts) == 4 and item.get("mark_iv", 0) > 0:
                parsed.append({"expiry": parts[1], "strike": float(parts[2]), "iv": item["mark_iv"]})

        df = pd.DataFrame(parsed)
        if not df.empty:
            pivot = df.pivot_table(index="strike", columns="expiry", values="iv", aggfunc="mean").dropna()
            strikes = pivot.index.tolist()
            expiries = pivot.columns.tolist()
            z_values = pivot.values.tolist()

            if view_mode == "3D Surface":
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-surface" style="width:100%; height:680px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'surface',
                        colorscale: 'Greens',
                        colorbar: {{ len: 0.8, thickness: 15, tickfont: {{color: '#00FF66'}} }}
                    }}];
                    var layout = {{
                        paper_bgcolor: '#030a05',
                        plot_bgcolor: '#030a05',
                        font: {{ color: '#00FF66' }},
                        margin: {{ l: 0, r: 0, b: 0, t: 10 }},
                        scene: {{
                            xaxis: {{ title: 'Expiry', gridcolor: '#09240f' }},
                            yaxis: {{ title: 'Strike ($)', gridcolor: '#09240f' }},
                            zaxis: {{ title: 'IV (%)', gridcolor: '#09240f' }},
                            aspectmode: 'manual',
                            aspectratio: {{ x: 1.1, y: 1.1, z: 0.5 }},
                            camera: {{ eye: {{ x: 0.95, y: 0.95, z: 0.6 }} }}
                        }}
                    }};
                    Plotly.react('plotly-surface', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=700)

            elif view_mode == "2D Heatmap":
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-heatmap" style="width:100%; height:680px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'heatmap',
                        colorscale: 'Greens'
                    }}];
                    var layout = {{
                        paper_bgcolor: '#030a05',
                        plot_bgcolor: '#030a05',
                        font: {{ color: '#00FF66' }},
                        xaxis: {{ title: 'Expiry', gridcolor: '#09240f' }},
                        yaxis: {{ title: 'Strike ($)', gridcolor: '#09240f' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-heatmap', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=700)

            elif view_mode == "2D Volatility Smiles":
                traces = [{"x": strikes, "y": pivot[exp].tolist(), "mode": "lines+markers", "name": str(exp)} for exp in expiries]
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-smiles" style="width:100%; height:680px;"></div>
                <script>
                    var data = {json.dumps(traces)};
                    var layout = {{
                        paper_bgcolor: '#030a05',
                        plot_bgcolor: '#030a05',
                        font: {{ color: '#00FF66' }},
                        xaxis: {{ title: 'Strike ($)', gridcolor: '#09240f' }},
                        yaxis: {{ title: 'IV (%)', gridcolor: '#09240f' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-smiles', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=700)

# 6. Auto-Refresh Loop für die Diagramme (alle 30 Sekunden im Free Tier)
time.sleep(30)
st.rerun()
