import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
import numpy as np
import time

# Versuche SciPy für Ultra-HD Interpolation der 3D-Fläche zu laden
try:
    from scipy.ndimage import zoom
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 1. Page Config & Ultra Dark Cyberpunk Theme
st.set_page_config(page_title="BTC Cyber Terminal v7 EXTREME", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Haupt-Hintergrund */
        .stApp {
            background-color: #020408 !important;
            color: #00F3FF !important;
        }
        
        /* Footer ausblenden, Header transparent lassen für den Sidebar-Pfeil */
        footer { visibility: hidden; }
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 99999 !important;
        }

        /* SIDEBAR TOGGLE BUTTON REPARATUR:
           Macht den Aufklapp-Pfeil oben links immer sichtbar & leuchtend */
        [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {
            color: #00F3FF !important;
            background-color: #071018 !important;
            border: 1px solid #00F3FF !important;
            border-radius: 6px !important;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.6) !important;
            margin: 8px !important;
        }
        [data-testid="stSidebarCollapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {
            background-color: #00F3FF !important;
            color: #020408 !important;
            box-shadow: 0 0 20px #00F3FF !important;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        
        /* Metric Cards Style */
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

        /* Paywall & Admin Boxen */
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
        
        @keyframes adminGlow {
            0% { box-shadow: 0 0 10px #00FF66; border-color: #00FF66; }
            50% { box-shadow: 0 0 25px #00FF66, 0 0 10px #00F3FF; border-color: #00F3FF; }
            100% { box-shadow: 0 0 10px #00FF66; border-color: #00FF66; }
        }
        
        .admin-unlocked-box {
            background: linear-gradient(135deg, rgba(8, 35, 20, 0.95) 0%, rgba(3, 15, 8, 0.95) 100%);
            border: 2px solid #00FF66;
            animation: adminGlow 2s infinite;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            color: #00FF66;
            margin-bottom: 15px;
            font-weight: bold;
            letter-spacing: 1.5px;
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
ADMIN_PASSWORD = "dein_secret_passwort"

# 3. Realtime Ticker Banner (Binance Live Stream)
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
        <span style="font-size: 0.75rem; color: #00A3AA; text-transform: uppercase; letter-spacing: 2px;">BTC/USDT Live Index</span><br>
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
            const res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
            const data = await res.json();
            if (data) {
                const price = parseFloat(data.lastPrice).toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('btc-price').innerText = '$' + price;
                const change = parseFloat(data.priceChangePercent).toFixed(2);
                const changeEl = document.getElementById('btc-change');
                changeEl.innerText = (change >= 0 ? '+' : '') + change + '%';
                changeEl.style.color = change >= 0 ? '#00FF66' : '#FF0055';
                document.getElementById('btc-range').innerText = '$' + parseFloat(data.highPrice).toFixed(0) + ' / $' + parseFloat(data.lowPrice).toFixed(0);
            }
        } catch (e) { console.error(e); }
    }
    fetchTicker();
    setInterval(fetchTicker, 1500);
</script>
"""
components.html(btc_header_html, height=90)

# 4. Navigation & Sidebar
st.sidebar.markdown("### ⚙️ Terminal Navigation")
view_mode = st.sidebar.radio(
    "Visualisierung wählen:", 
    ["3D ULTRA HD Modell", "Live Kerzenchart", "Put/Call Skew Radar", "2D Heatmap", "Volatility Smiles"]
)

# 3D Optionen
if view_mode == "3D ULTRA HD Modell":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧊 3D Mesh Optionen")
    three_d_style = st.sidebar.radio(
        "3D Stil wählen:",
        ["ULTRA HD Surface (Extrem Detaillierte Fläche)", "Wireframe Grid (Neon Net)"]
    )
    colorscale_choice = st.sidebar.selectbox(
        "Farb-Palette:",
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
        st.markdown('<div class="admin-unlocked-box">⚡ ADMIN MODUS AKTIV: UNLIMITED ACCESS</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="paywall-box">
                <h3 style="color: #FF0055; margin: 0;">🔒 PRO UPGRADE REQUIRED</h3>
                <p style="margin: 6px 0; font-size: 0.85rem;">Fast-Feeds erfordern einen PRO-Zugang.</p>
                <a href="https://www.paypal.com" target="_blank" class="paypal-btn">💳 Mit PayPal freischalten (9,99€)</a>
            </div>
        """, unsafe_allow_html=True)

# ANIMATION: Admin Unlock Konfetti
if is_admin:
    admin_confetti_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        var count = 200;
        var defaults = { origin: { y: 0.7 } };
        function fire(particleRatio, opts) {
            confetti(Object.assign({}, defaults, opts, {
                particleCount: Math.floor(count * particleRatio)
            }));
        }
        fire(0.25, { spread: 26, startVelocity: 55, colors: ['#00F3FF', '#00FF66'] });
        fire(0.2, { spread: 60, colors: ['#FF0055', '#FFFFFF'] });
        fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
        fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, colors: ['#00F3FF', '#00FF66'] });
    </script>
    """
    components.html(admin_confetti_js, height=0)

# Trade / Kauf Simulator Button
st.sidebar.markdown("---")
st.sidebar.markdown("### 🛒 Trade & Kauf Simulator")
if st.sidebar.button("🎉 Kauf / Order Testen"):
    buy_animation_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <div style="background: rgba(0, 243, 255, 0.15); border: 2px solid #00F3FF; border-radius: 10px; padding: 15px; text-align: center; color: #00F3FF; font-family: sans-serif; box-shadow: 0 0 25px rgba(0,243,255,0.4);">
        <h2>🚀 ORDER ERFOLGREICH AUSGEFÜHRT!</h2>
        <p>1.00 BTC @ Market Order bestätigt. PRO Status aktiv!</p>
    </div>
    <script>
        confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 }, colors: ['#00F3FF', '#00FF66', '#FF0055'] });
    </script>
    """
    components.html(buy_animation_js, height=120)

# --- NEON CYBERPUNK QR CODE GENERATOR ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Mobile Sync (QR-Code)")

url_mode = st.sidebar.radio("URL Typ:", ["WLAN (Lokales Netz)", "Cloud / Tunnel URL"])
if url_mode == "WLAN (Lokales Netz)":
    default_target = "http://192.168.1.50:8501" # Deine Terminal Network-URL
else:
    default_target = "https://deine-app.streamlit.app"

target_url = st.sidebar.text_input("Ziel-URL für QR-Code:", value=default_target)

if target_url:
    # Generiert QR-Code im Cyberpunk-Neon-Look (Cyan-Code auf tiefdunklem Hintergrund)
    qr_cyber_api = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={target_url}&color=00F3FF&bgcolor=020408"
    st.sidebar.image(qr_cyber_api, caption="📱 Scan mit Smartphone-Kamera", use_container_width=True)

# 5. Data Fetcher für Deribit Option IV
@st.cache_data(ttl=10)
def get_deribit_iv_data():
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        res = requests.get(url, timeout=10).json()
        return res.get("result", [])
    except Exception:
        return []

# 6. Live Kerzenchart Render (Binance Stream - Lädt garantiert immer!)
if view_mode == "Live Kerzenchart":
    binance_candlestick_html = """
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <div id="plotly-candle" style="width:100%; height:680px;"></div>
    <script>
        var layout = {
            paper_bgcolor: '#020408',
            plot_bgcolor: '#020408',
            font: { color: '#00F3FF' },
            title: 'BTC/USDT Realtime 1m Candlestick Chart (Binance Live Feed)',
            xaxis: { gridcolor: '#0D1622', rangeslider: {visible: false} },
            yaxis: { gridcolor: '#0D1622' },
            margin: { l: 50, r: 20, b: 40, t: 40 }
        };

        async function updateLiveCandles() {
            try {
                const res = await fetch('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100');
                const data = await res.json();

                if (data && data.length > 0) {
                    const times = data.map(d => new Date(d[0]).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
                    const opens = data.map(d => parseFloat(d[1]));
                    const highs = data.map(d => parseFloat(d[2]));
                    const lows = data.map(d => parseFloat(d[3]));
                    const closes = data.map(d => parseFloat(d[4]));

                    var trace = {
                        x: times,
                        open: opens,
                        high: highs,
                        low: lows,
                        close: closes,
                        type: 'candlestick',
                        increasing: {line: {color: '#00F3FF', width: 2}, fillcolor: 'rgba(0, 243, 255, 0.4)'},
                        decreasing: {line: {color: '#FF0055', width: 2}, fillcolor: 'rgba(255, 0, 85, 0.4)'}
                    };
                    Plotly.react('plotly-candle', [trace], layout, {responsive: true, displayModeBar: true, scrollZoom: true});
                }
            } catch (e) { console.error('Candle error:', e); }
        }

        updateLiveCandles();
        setInterval(updateLiveCandles, 2000);
    </script>
    """
    components.html(binance_candlestick_html, height=700)

# 7. Options & EXTREM Detaillierte 3D Render Engine
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
            z_values = pivot.values

            # EXTREM HOHE DETAILED INTERPOLATION (6x Zoom = ~100x100 High Density Grid)
            if HAS_SCIPY and len(strikes) > 2 and len(expiries) > 2:
                z_dense = zoom(z_values, (6.0, 6.0), order=3)
                strikes_dense = np.linspace(strikes[0], strikes[-1], z_dense.shape[0]).tolist()
                expiries_dense = []
                for idx in np.linspace(0, len(expiries) - 1, z_dense.shape[1]):
                    expiries_dense.append(expiries[int(round(idx))])
                z_final = z_dense.tolist()
            else:
                strikes_dense = strikes
                expiries_dense = expiries
                z_final = z_values.tolist()

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Max Volatilität</div><div class="metric-value">{df["iv"].max():.1f}%</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Min Volatilität</div><div class="metric-value">{df["iv"].min():.1f}%</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">⌀ Markt IV</div><div class="metric-value">{df["iv"].mean():.1f}%</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Options Kontrakte</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

            # 3D ULTRA HD MODEL RENDER
            if view_mode == "3D ULTRA HD Modell":
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
                else: # EXTREM Detaillierte Surface mit Glanz-Reflexionen
                    surface_config = "hidesurface: false,"
                    contours_config = """
                        contours: {
                            z: { show: true, usecolormap: true, highlightcolor: "#00FF66", project: { z: true }, width: 2 },
                            x: { show: true, color: "rgba(0, 243, 255, 0.25)", width: 1 },
                            y: { show: true, color: "rgba(255, 0, 85, 0.25)", width: 1 }
                        },
                    """
                    colorscale_script = f"colorscale: '{colorscale_choice}',"

                plotly_html = f"""
                <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
                <div id="plotly-surface" style="width:100%; height:650px;"></div>
                <script>
                    var data = [{{
                        x: {json.dumps(expiries_dense)},
                        y: {json.dumps(strikes_dense)},
                        z: {json.dumps(z_final)},
                        type: 'surface',
                        {surface_config}
                        {colorscale_script}
                        {contours_config}
                        lighting: {{
                            ambient: 0.4,
                            diffuse: 0.8,
                            fresnel: 0.5,
                            specular: 2.0,
                            roughness: 0.05
                        }}
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
                        z: {json.dumps(pivot.values.tolist())},
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
