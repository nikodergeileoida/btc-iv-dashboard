import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import time

# 1. Page Config & Dark High-Tech Terminal Styling
st.set_page_config(page_title="BTC Cyber Volatility Terminal", layout="wide")

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
        /* High-Tech Card Design */
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
        .metric-sub { font-size: 0.8rem; color: #00FF66; }

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

# 2. Realtime Ticker mit Live-Preis, 24h Change & High/Low (1s Web API Feed)
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
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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

# 3. Sidebar Controls
st.sidebar.markdown("### ⚙️ Terminal Navigation")
view_mode = st.sidebar.radio(
    "Visualisierung wählen:", 
    ["3D Surface (Pro Grid)", "ATM Term Structure", "2D Heatmap", "Volatility Smiles", "Live Kerzenchart"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 3D Mesh Rendering Engine")
colorscale_choice = st.sidebar.selectbox(
    "Farb-Palette:",
    ["Electric (Neon Cyber)", "Turbo (High Contrast)", "Plasma (Deep Gold)", "Viridis (Matrix)"]
)
color_map = {
    "Electric (Neon Cyber)": "Electric",
    "Turbo (High Contrast)": "Turbo",
    "Plasma (Deep Gold)": "Plasma",
    "Viridis (Matrix)": "Viridis"
}

auto_rotate = st.sidebar.checkbox("3D Orbit Auto-Rotation", value=True)
mesh_density = st.sidebar.slider("Wireframe-Gitter Dichte", min_value=1, max_value=3, value=1)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Data Stream Rate")
update_rate = st.sidebar.selectbox(
    "Intervall:",
    ["30 Sekunden (Free)", "15 Sekunden (PRO)", "5 Sekunden (PRO)", "1 Sekunde (Ultra PRO)"]
)

if "PRO" in update_rate:
    st.markdown("""
        <div class="paywall-box">
            <h3 style="color: #FF0055; margin: 0;">🔒 PRO UPGRADE REQUIRED</h3>
            <p style="margin: 6px 0; font-size: 0.85rem;">High-Speed Sub-30s Feeds sind für PRO User freigeschaltet.</p>
            <a href="https://www.paypal.com" target="_blank" class="paypal-btn">💳 Mit PayPal freischalten (9,99€)</a>
        </div>
    """, unsafe_allow_html=True)

# 4. Daten-Funktionen (Deribit Options & Perpetual Charts)
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
        start_ts = end_ts - (60 * 60 * 1000)
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

# 5. Visualisierungs-Engine
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
                increasing: {{line: {{color: '#00F3FF', width: 1.5}}, fillcolor: 'rgba(0, 243, 255, 0.3)'}},
                decreasing: {{line: {{color: '#FF0055', width: 1.5}}, fillcolor: 'rgba(255, 0, 85, 0.3)'}}
            }};
            var layout = {{
                paper_bgcolor: '#020408',
                plot_bgcolor: '#020408',
                font: {{ color: '#00F3FF' }},
                title: 'BTC-PERPETUAL Realtime 1m Candlestick Chart',
                xaxis: {{ gridcolor: '#0D1622', rangeslider: {{visible: false}} }},
                yaxis: {{ gridcolor: '#0D1622' }},
                margin: {{ l: 50, r: 20, b: 40, t: 40 }}
            }};
            Plotly.react('plotly-candle', [trace], layout, {{responsive: true, displayModeBar: false}});
        </script>
        """
        components.html(candlestick_html, height=700)
    else:
        st.info("Lade Realtime-Candlestick Daten...")

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
            
            # Ausdünnen des Gitters je nach Slider für bessere Performance/Optik
            pivot = pivot.iloc[::mesh_density, :]
            
            strikes = pivot.index.tolist()
            expiries = pivot.columns.tolist()
            z_values = pivot.values.tolist()

            # Market Overview Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Max Volatilität</div><div class="metric-value">{df["iv"].max():.1f}%</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Min Volatilität</div><div class="metric-value">{df["iv"].min():.1f}%</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">⌀ Markt IV</div><div class="metric-value">{df["iv"].mean():.1f}%</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Options Kontrakte</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

            selected_colorscale = color_map[colorscale_choice]

            # High-End 3D Surface Model
            if view_mode == "3D Surface (Pro Grid)":
                rotate_js = """
                var r = 1.25;
                var theta = 0;
                setInterval(function(){
                    theta += 0.01;
                    Plotly.relayout('plotly-surface', {
                        'scene.camera.eye': { x: r * Math.cos(theta), y: r * Math.sin(theta), z: 0.7 }
                    });
                }, 30);
                """ if auto_rotate else ""

                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-surface" style="width:100%; height:650px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(strikes)},
                        z: {json.dumps(z_values)},
                        type: 'surface',
                        colorscale: '{selected_colorscale}',
                        showscale: true,
                        wireframe: {{ show: true, color: '#00F3FF', width: 0.5 }},
                        contours: {{
                            z: {{ show: true, usecolormap: true, highlightcolor: "#00F3FF", project: {{ z: true }} }},
                            x: {{ show: true, color: 'rgba(0, 243, 255, 0.2)' }},
                            y: {{ show: true, color: 'rgba(255, 0, 85, 0.2)' }}
                        }},
                        lighting: {{
                            ambient: 0.4,
                            diffuse: 0.9,
                            fresnel: 0.4,
                            specular: 1.8,
                            roughness: 0.15
                        }},
                        colorbar: {{ len: 0.8, thickness: 12, tickfont: {{color: '#00F3FF'}} }}
                    }}];
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        margin: {{ l: 0, r: 0, b: 0, t: 10 }},
                        scene: {{
                            xaxis: {{ title: 'Expiry', gridcolor: '#0D1622', backgroundcolor: '#020408' }},
                            yaxis: {{ title: 'Strike ($)', gridcolor: '#0D1622', backgroundcolor: '#020408' }},
                            zaxis: {{ title: 'IV (%)', gridcolor: '#0D1622', backgroundcolor: '#020408' }},
                            aspectmode: 'manual',
                            aspectratio: {{ x: 1.2, y: 1.2, z: 0.55 }},
                            camera: {{ eye: {{ x: 0.9, y: 0.9, z: 0.65 }} }}
                        }}
                    }};
                    Plotly.react('plotly-surface', data, layout, {{responsive: true, displayModeBar: false}});
                    {rotate_js}
                </script>
                """
                components.html(plotly_html, height=670)

            # ATM Term Structure (Neue Ansicht)
            elif view_mode == "ATM Term Structure":
                atm_ivs = pivot.mean(axis=0).tolist()
                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-term" style="width:100%; height:650px;"></div>
                <script>
                    var trace = {{
                        x: {json.dumps(expiries)},
                        y: {json.dumps(atm_ivs)},
                        type: 'scatter',
                        mode: 'lines+markers',
                        line: {{ color: '#00F3FF', width: 3, shape: 'spline' }},
                        marker: {{ size: 8, color: '#FF0055' }}
                    }};
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        title: 'ATM Implied Volatility Term Structure Across Expiries',
                        xaxis: {{ title: 'Expiry Date', gridcolor: '#0D1622' }},
                        yaxis: {{ title: 'Average IV (%)', gridcolor: '#0D1622' }},
                        margin: {{ l: 50, r: 20, b: 50, t: 50 }}
                    }};
                    Plotly.react('plotly-term', [trace], layout, {{responsive: true, displayModeBar: false}});
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
                        colorscale: '{selected_colorscale}'
                    }}];
                    var layout = {{
                        paper_bgcolor: '#020408',
                        plot_bgcolor: '#020408',
                        font: {{ color: '#00F3FF' }},
                        xaxis: {{ title: 'Expiry', gridcolor: '#0D1622' }},
                        yaxis: {{ title: 'Strike ($)', gridcolor: '#0D1622' }},
                        margin: {{ l: 60, r: 20, b: 60, t: 20 }}
                    }};
                    Plotly.react('plotly-heatmap', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=670)

            # Volatility Smiles
            elif view_mode == "Volatility Smiles":
                traces = [{"x": strikes, "y": pivot[exp].tolist(), "mode": "lines+markers", "name": str(exp), "line": {"shape": "spline"}} for exp in expiries]
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
                    Plotly.react('plotly-smiles', data, layout, {{responsive: true, displayModeBar: false}});
                </script>
                """
                components.html(plotly_html, height=670)

# 6. Auto Refresh Loop
time.sleep(30)
st.rerun()
