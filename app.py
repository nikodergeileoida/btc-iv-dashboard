import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import time

# 1. Page Config & Ultra Dark Cyberpunk Theme
st.set_page_config(page_title="BTC Cyber Terminal v4", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-color: #020408 !important;
            color: #00F3FF !important;
        }
        header, footer { visibility: hidden; }
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        .metric-card {
            background: linear-gradient(145deg, rgba(10, 20, 32, 0.9), rgba(4, 8, 15, 0.95));
            border: 1px solid rgba(0, 243, 255, 0.3);
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.15);
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }
        .metric-title { font-size: 0.75rem; color: #507090; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { font-size: 1.4rem; font-weight: 800; color: #00F3FF; text-shadow: 0 0 8px rgba(0,243,255,0.4); }

        .paywall-box {
            background: linear-gradient(135deg, rgba(35, 8, 20, 0.95) 0%, rgba(15, 3, 10, 0.95) 100%);
            border: 1px solid #FF0055;
            box-shadow: 0 0 20px rgba(255, 0, 85, 0.4);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            color: #FFDDDD;
            margin-bottom: 15px;
        }
        .admin-unlocked-box {
            background: linear-gradient(135deg, rgba(8, 35, 20, 0.95) 0%, rgba(3, 15, 8, 0.95) 100%);
            border: 1px solid #00FF66;
            box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            color: #00FF66;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .paypal-btn {
            background-color: #0070BA;
            color: #FFFFFF !important;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin-top: 8px;
            box-shadow: 0 0 10px rgba(0, 112, 186, 0.5);
        }
    </style>
""", unsafe_allow_html=True)

# 2. Admin Passwort
ADMIN_PASSWORD = "niko2002"

# 3. Realtime Ticker Banner
btc_header_html = """
<div id="ticker-card" style="
    background: linear-gradient(135deg, #071018 0%, #020508 100%);
    border: 1px solid #00F3FF;
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    border-radius: 10px;
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: sans-serif;
">
    <div style="text-align: left;">
        <span style="font-size: 0.75rem; color: #00A3AA; text-transform: uppercase; letter-spacing: 2px;">BTC/USD Index Feed</span><br>
        <span id="btc-price" style="font-size: 2.2rem; font-weight: 900; color: #00F3FF; text-shadow: 0 0 12px rgba(0, 243, 255, 0.5);">--.--</span>
    </div>
    <div style="text-align: center;">
        <span style="font-size: 0.75rem; color: #507090; text-transform: uppercase;">24h Veränderung</span><br>
        <span id="btc-change" style="font-size: 1.4rem; font-weight: 700; color: #00FF66;">--%</span>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 0.75rem; color: #507090; text-transform: uppercase;">24h High / Low</span><br>
        <span id="btc-range" style="font-size: 1.1rem; font-weight: 600; color: #A0C0E0;">-- / --</span>
    </div>
</div>

<script>
    async function fetchTicker() {
        try {
            const res = await fetch('https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=future');
            const data = await res.json();
            const perp = data.result.find(i => i.instrument_name === 'BTC-PERPETUAL');
            if (perp) {
                document.getElementById('btc-price').innerText = '$' + perp.mark_price.toLocaleString('en-US', {minimumFractionDigits: 2});
                const change = (((perp.mark_price - perp.open_interest) / perp.mark_price) * 100).toFixed(2);
                const changeEl = document.getElementById('btc-change');
                changeEl.innerText = (change >= 0 ? '+' : '') + change + '%';
                changeEl.style.color = change >= 0 ? '#00FF66' : '#FF0055';
                document.getElementById('btc-range').innerText = '$' + perp.high.toFixed(0) + ' / $' + perp.low.toFixed(0);
            }
        } catch (e) { console.error(e); }
    }
    fetchTicker();
    setInterval(fetchTicker, 1000);
</script>
"""
components.html(btc_header_html, height=90)

# 4. Navigation & Sidebar
st.sidebar.markdown("### ⚙️ Terminal Navigation")
view_mode = st.sidebar.radio(
    "Visualisierung wählen:", 
    ["3D Modell (Surface / Grid)", "Live Kerzenchart", "Put/Call Skew Radar", "2D Heatmap", "Volatility Smiles"]
)

# Spezifische 3D-Einstellungen nur anzeigen, wenn 3D gewählt ist
if view_mode == "3D Modell (Surface / Grid)":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧊 3D Modus Option")
    three_d_style = st.sidebar.radio(
        "3D Stil wählen:",
        ["Wireframe Grid (Neon Net)", "Solid Surface (3D Fläche)"]
    )
    colorscale_choice = st.sidebar.selectbox(
        "Farb-Palette (nur bei Surface):",
        ["Electric", "Turbo", "Plasma", "Viridis"]
    )
    auto_rotate = st.sidebar.checkbox("3D Orbit Auto-Rotation", value=False)
else:
    auto_rotate = False

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Admin Login")
entered_pass = st.sidebar.text_input("Admin Key:", type="password")
is_admin = (entered_pass == ADMIN_PASSWORD)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Data Stream Rate")
update_rate = st.sidebar.selectbox(
    "Intervall wählen:",
    ["30 Sekunden (Free)", "15 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

if "PRO" in update_rate:
    if is_admin:
        st.markdown('<div class="admin-unlocked-box">⚡ ADMIN MODUS AKTIV</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="paywall-box">
                <h3 style="color: #FF0055; margin: 0;">🔒 PRO UPGRADE REQUIRED</h3>
                <p style="margin: 6px 0; font-size: 0.85rem;">Fast-Feeds erfordern einen PRO-Zugang.</p>
                <a href="https://www.paypal.com" target="_blank" class="paypal-btn">💳 Mit PayPal freischalten (9,99€)</a>
            </div>
        """, unsafe_allow_html=True)

# 5. Data Fetcher
@st.cache_data(ttl=10)
def get_deribit_iv_data():
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("result", [])
    except Exception:
        return []

@st.cache_data(ttl=5)
def get_btc_candles():
    try:
        end_ts = int(time.time() * 1000)
        start_ts = end_ts - (120 * 60 * 1000)
        url = f"https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name=BTC-PERPETUAL&start_timestamp={start_ts}&end_timestamp={end_ts}&resolution=1"
        res = requests.get(url, timeout=5).json()
        data = res.get("result", {})
        if "ticks" in data and len(data["ticks"]) > 0:
            return pd.DataFrame({
                'time': [time.strftime('%H:%M', time.localtime(t/1000)) for t in data['ticks']],
                'open': data['open'],
                'high': data['high'],
                'low': data['low'],
                'close': data['close']
            })
    except Exception:
        pass
    return pd.DataFrame()

# 6. Live Kerzenchart Render
if view_mode == "Live Kerzenchart":
    candles_df = get_btc_candles()
    if not candles_df.empty:
        candlestick_html = f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <div id="plotly-candle" style="width:100%; height:680px;"></div>
        <script>
            var trace = {{
                x: {json.dumps(candles_df['time'].tolist())},
                open: {json.dumps(candles_df['open'].tolist())},
                high: {json.dumps(candles_df['high'].tolist())},
                low: {json.dumps(candles_df['low'].tolist())},
                close: {json.dumps(candles_df['close'].tolist())},
                type: 'candlestick',
                increasing: {{line: {{color: '#00F3FF', width: 2}}, fillcolor: 'rgba(0, 243, 255, 0.4)'}},
                decreasing: {{line: {{color: '#FF0055', width: 2}}, fillcolor: 'rgba(255, 0, 85, 0.4)'}}
            }};
            var layout = {{
                paper_bgcolor: '#020408',
                plot_bgcolor: '#020408',
                font: {{ color: '#00F3FF' }},
                title: 'BTC-PERPETUAL Realtime Candlestick Chart',
                xaxis: {{ gridcolor: '#0D1622', rangeslider: {{visible: false}} }},
                yaxis: {{ gridcolor: '#0D1622' }},
                margin: {{ l: 50, r: 20, b: 40, t: 40 }}
            }};
            Plotly.react('plotly-candle', [trace], layout, {{responsive: true, displayModeBar: true, scrollZoom: true}});
        </script>
        """
        components.html(candlestick_html, height=700)
    else:
        st.warning("Lade Live-Kerzen von Deribit...")

# 7. Options & 3D Render
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
                    "type": parts[3],
                    "iv": item["mark_iv"]
                })

        df = pd.DataFrame(parsed)
        if not df.empty:
            pivot = df.pivot_table(index="strike", columns="expiry", values="iv", aggfunc="mean").dropna()
            strikes = pivot.index.tolist()
            expiries = pivot.columns.tolist()
            z_values = pivot.values.tolist()

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Max Volatilität</div><div class="metric-value">{df["iv"].max():.1f}%</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Min Volatilität</div><div class="metric-value">{df["iv"].min():.1f}%</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">⌀ Markt IV</div><div class="metric-value">{df["iv"].mean():.1f}%</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Options Kontrakte</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

            # 3D MODELL RENDER (WIRE FRAME vs SOLID SURFACE)
            if view_mode == "3D Modell (Surface / Grid)":
                rotate_js = """
                var r = 1.35; var theta = 0;
                setInterval(function(){
                    theta += 0.008;
                    Plotly.relayout('plotly-surface', { 'scene.camera.eye': { x: r * Math.cos(theta), y: r * Math.sin(theta), z: 0.75 } });
                }, 30);
                """ if auto_rotate else ""

                if three_d_style == "Wireframe Grid (Neon Net)":
                    surface_config = "hidesurface: true,"
                    contours_config = """
                        contours: {
                            x: { show: true, color: '#00F3FF', width: 2 },
                            y: { show: true, color: '#FF0055', width: 2 },
                            z: { show: true, color: '#00FF66', width: 2 }
                        },
                    """
                    colorscale_script = "colorscale: 'Electric',"
                else: # Solid Surface
                    surface_config = "hidesurface: false,"
                    contours_config = """
                        contours: {
                            z: { show: true, usecolormap: true, highlightcolor: "#00F3FF", project: { z: true } }
                        },
                    """
                    colorscale_script = f"colorscale: '{colorscale_choice}',"

                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-surface" style="width:100%; height:650px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'surface',
                        {surface_config}
                        {colorscale_script}
                        {contours_config}
                        lighting: {{ ambient: 0.5, diffuse: 0.8, specular: 1.5, roughness: 0.2 }}
                    }}];
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        margin: {{ l: 0, r: 0, b: 0, t: 10 }},
                        scene: {{
                            xaxis: {{ title: 'Expiry', gridcolor: '#0D1622', showbackground: false }},
                            yaxis: {{ title: 'Strike ($)', gridcolor: '#0D1622', showbackground: false }},
                            zaxis: {{ title: 'IV (%)', gridcolor: '#0D1622', showbackground: false }},
                            aspectmode: 'manual',
                            aspectratio: {{ x: 1.2, y: 1.2, z: 0.55 }},
                            camera: {{ eye: {{ x: 0.95, y: 0.95, z: 0.65 }} }}
                        }}
                    }};
                    Plotly.react('plotly-surface', data, layout, {{responsive: true, displayModeBar: true, scrollZoom: true}});
                    {rotate_js}
                </script>
                """
                components.html(plotly_html, height=670)

            # Put/Call Skew Radar
            elif view_mode == "Put/Call Skew Radar":
                puts_avg = df[df['type'] == 'P']['iv'].mean()
                calls_avg = df[df['type'] == 'C']['iv'].mean()
                skew = puts_avg - calls_avg

                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-skew" style="width:100%; height:650px;"></div>
                <script>
                    var data = [{{
                        domain: {{ x: [0, 1], y: [0, 1] }},
                        value: {skew:.2f},
                        title: {{ text: "Put/Call Volatilitäts Skew (Crash Risk Gauge)" }},
                        type: "indicator",
                        mode: "gauge+number+delta",
                        delta: {{ reference: 0 }},
                        gauge: {{
                            axis: {{ range: [-20, 20], tickcolor: "#00F3FF" }},
                            bar: {{ color: "#00F3FF" }},
                            steps: [
                                {{ range: [-20, -5], color: "rgba(0, 255, 102, 0.3)" }},
                                {{ range: [-5, 5], color: "rgba(0, 243, 255, 0.2)" }},
                                {{ range: [5, 20], color: "rgba(255, 0, 85, 0.4)" }}
                            ]
                        }}
                    }}];
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        margin: {{ l: 50, r: 50, b: 50, t: 50 }}
                    }};
                    Plotly.react('plotly-skew', data, layout, {{responsive: true, displayModeBar: true, scrollZoom: true}});
                </script>
                """
                components.html(plotly_html, height=670)

            # 2D Heatmap
            elif view_mode == "2D Heatmap":
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-heatmap" style="width:100%; height:650px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'heatmap',
                        colorscale: 'Electric'
                    }}];
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        xaxis: {{ title: 'Expiry', gridcolor: '#0D1622' }},
                        yaxis: {{ title: 'Strike ($)', gridcolor: '#0D1622' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-heatmap', data, layout, {{responsive: true, displayModeBar: true, scrollZoom: true}});
                </script>
                """
                components.html(plotly_html, height=670)

            # Volatility Smiles
            elif view_mode == "Volatility Smiles":
                traces = [{"x": strikes, "y": pivot[exp].tolist(), "mode": "lines+markers", "name": str(exp)} for exp in expiries]
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-smiles" style="width:100%; height:650px;"></div>
                <script>
                    var data = {json.dumps(traces)};
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        xaxis: {{ title: 'Strike ($)', gridcolor: '#0D1622' }},
                        yaxis: {{ title: 'IV (%)', gridcolor: '#0D1622' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-smiles', data, layout, {{responsive: true, displayModeBar: true, scrollZoom: true}});
                </script>
                """
                components.html(plotly_html, height=670)

# 8. Auto Refresh Loop
time.sleep(30)
st.rerun()
