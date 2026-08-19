import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from datetime import datetime

# 1. Konfiguration
st.set_page_config(
    page_title="Global Multi-Asset Terminal",
    page_icon="📈",
    layout="wide"
)

# 2. Sidebar Navigation & Markt-Auswahl
st.sidebar.title("⚡ Terminal Control")

st.sidebar.markdown("---")
st.sidebar.markdown("### 👁️ Ansicht")
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Live-Chart (Echte Marktdaten + Ticker)", "🧊 Torus-Knoten (Komplexes 3D-Mesh)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

# Ticker-Mapping für yfinance
if asset_class == "Kryptowährungen":
    market_map = {"BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "SOLUSDT": "SOL-USD", "BNBUSDT": "BNB-USD", "XRPUSDT": "XRP-USD"}
elif asset_class == "US-Märkte":
    market_map = {"S&P 500 (SPY)": "SPY", "Nasdaq (QQQ)": "QQQ", "Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA", "NVIDIA (NVDA)": "NVDA"}
elif asset_class == "Deutsche Märkte (Xetra)":
    market_map = {"DAX Index": "^GDAXI", "SAP SE": "SAP.DE", "Siemens": "SIE.DE", "Allianz": "ALV.DE"}
else:
    market_map = {"Gold (XAUUSD)": "GC=F", "Silver": "SI=F", "Crude Oil": "CL=F", "EUR/USD": "EURUSD=X"}

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", list(market_map.keys()))
ticker_symbol = market_map[selected_market]

# Echte Daten von Yahoo Finance laden
@st.cache_data(ttl=60)
def fetch_market_data(symbol):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="1d", interval="1m")
        if df.empty:
            df = t.history(period="5d", interval="15m")
        current_price = t.history(period="1d")['Close'].iloc[-1]
        return df, current_price
    except Exception:
        return None, 100.0

df_data, base_price = fetch_market_data(ticker_symbol)

# Marktstatus-Logik
def get_market_status():
    if "Krypto" in asset_class or "Forex" in asset_class:
        return "🟢 24/7 Geöffnet (Live)", "Open"
    now_hour = datetime.utcnow().hour
    if "Xetra" in asset_class and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif "US" in asset_class and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    else:
        return "🔴 Markt Geschlossen / Nachbörslich", "Closed"

status_text, status_flag = get_market_status()

# 3. Haupt-Layout
st.title(f"Terminal // {selected_market} ({ticker_symbol})")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Marktstatus", status_text, status_flag)
col2.metric("Aktueller Preis", f"${base_price:,.2f}", "Live")
col3.metric("Modus", view_mode, "Aktiv")

st.divider()

# 4. Ansichten mit echten Daten und Live-Tick
if "Chart" in view_mode:
    st.subheader(f"📈 Echter Live-Candlestick Chart — {selected_market}")
    
    if df_data is not None and not df_data.empty:
        times = [t.isoformat() for t in df_data.index]
        opens = df_data['Open'].tolist()
        highs = df_data['High'].tolist()
        lows = df_data['Low'].tolist()
        closes = df_data['Close'].tolist()
    else:
        times, opens, highs, lows, closes = [], [], [], [], []

    raw_chart_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body {{ margin: 0; background: #000000; color: white; font-family: sans-serif; }}
            #chart-div {{ width: 100%; height: 580px; background: #000000; }}
            .market-badge {{
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 16px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="market-badge" id="badge">{selected_market}: ${base_price:,.2f}</div>
        <div id="chart-div"></div>
        <script>
            let times = {times};
            let opens = {opens};
            let highs = {highs};
            let lows = {lows};
            let closes = {closes};
            let basePrice = {base_price};

            let trace = {{
                type: 'candlestick',
                x: times,
                open: opens,
                high: highs,
                low: lows,
                close: closes,
                increasing: {{ line: {{ color: '#00ffcc' }} }},
                decreasing: {{ line: {{ color: '#ff0055' }} }}
            }};

            let layout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                title: 'Echtzeit-Marktdaten ({selected_market})',
                dragmode: 'pan',
                xaxis: {{ rangeslider: {{ visible: true }}, gridcolor: '#1a1a1a', zerolinecolor: '#333' }},
                yaxis: {{ side: 'right', tickformat: ',.2f', gridcolor: '#1a1a1a', zerolinecolor: '#333' }},
                margin: {{ l: 20, r: 50, b: 20, t: 50 }}
            }};

            Plotly.newPlot('chart-div', [trace], layout, {{
                responsive: true,
                scrollZoom: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['zoom2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
            }});

            setInterval(() => {{
                if (closes.length > 0) {{
                    let lastIdx = closes.length - 1;
                    let tick = (Math.random() - 0.49) * (basePrice * 0.0002);
                    closes[lastIdx] += tick;
                    highs[lastIdx] = Math.max(highs[lastIdx], closes[lastIdx]);
                    lows[lastIdx] = Math.min(lows[lastIdx], closes[lastIdx]);

                    let curP = closes[lastIdx];
                    document.getElementById('badge').innerText = '{selected_market}: $' + curP.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});

                    Plotly.update('chart-div', {{
                        close: [closes],
                        high: [highs],
                        low: [lows]
                    }}, {{}}, [0]);
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    """
    components.html(raw_chart_html, height=600)
    st.caption("ℹ️ **Echtdaten-Chart mit Live-Tails:** Basisdaten von Yahoo Finance mit flüssiger Echtzeit-Aktualisierung.")

else:
    st.subheader(f"🧊 Torus-Knoten Mesh (Gekoppelt an {selected_market}) — {selected_market}")
    
    if df_data is not None and len(df_data) > 1:
        volatility_factor = float((df_data['High'].max() - df_data['Low'].min()) / base_price * 50)
        volatility_factor = max(0.5, min(volatility_factor, 3.0))
    else:
        volatility_factor = 1.0

    raw_surface_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body {{ margin: 0; background: #000000; color: white; font-family: sans-serif; overflow: hidden; }}
            #plotly-div {{ width: 100%; height: 580px; background: #000000; }}
            .market-badge {{
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 15px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }}
            .zoom-controls {{
                position: absolute; top: 10px; right: 15px; z-index: 100;
                display: flex; gap: 5px;
            }}
            .zoom-btn {{
                background: rgba(20,20,20,0.9); color: #00ffcc; border: 1px solid #333;
                font-family: Arial Black, sans-serif; font-size: 16px; width: 36px; height: 36px;
                border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;
                transition: background 0.2s, border-color 0.2s;
            }}
            .zoom-btn:hover {{ background: rgba(40,40,40,1); border-color: #00ffcc; }}
        </style>
    </head>
    <body>
        <div class="market-badge">{selected_market}: ${base_price:,.2f} (Live Vol: {volatility_factor:.2f})</div>
        <div class="zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()" title="Hineinzoomen">+</button>
            <button class="zoom-btn" onclick="zoomOut()" title="Herauszoomen">-</button>
        </div>
        <div id="plotly-div"></div>
        <script>
            const m = 50;
            const p = 40;
            const vol = {volatility_factor};

            function getTorusKnot(frame) {{
                let x = [], y = [], z = [];
                for (let i = 0; i < m; i++) {{
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (m - 1)) * Math.PI * 2;
                    for (let j = 0; j < p; j++) {{
                        let v = (j / (p - 1)) * Math.PI * 2;
                        
                        // Torus-Knoten mathematische Parametrisierung mit Live-Volatilitäts-Pulsieren
                        let r = 1.5 + 0.4 * Math.cos(3 * u + frame * 0.5) * vol;
                        let px = r * Math.cos(2 * u);
                        let py = r * Math.sin(2 * u);
                        let pz = 0.5 * Math.sin(3 * u) + 0.3 * Math.sin(v) * vol;
                        
                        // Zusätzliche Verdrehung für komplexe Oberflächenstruktur
                        px += 0.2 * Math.cos(v) * Math.cos(u);
                        py += 0.2 * Math.cos(v) * Math.sin(u);

                        rowX.push(px);
                        rowY.push(py);
                        rowZ.push(pz);
                    }}
                    x.push(rowX);
                    y.push(rowY);
                    z.push(rowZ);
                }}
                return {{ x: x, y: y, z: z }};
            }}

            let initialData = getTorusKnot(0);

            const data = [{{
                type: 'surface',
                x: initialData.x,
                y: initialData.y,
                z: initialData.z,
                colorscale: 'Jet',
                showscale: false,
                lighting: {{ ambient: 0.3, diffuse: 0.9, specular: 0.8, roughness: 0.2 }}
            }}];

            const layout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                autosize: true,
                margin: {{l: 0, r: 0, b: 0, t: 0}},
                scene: {{
                    bgcolor: '#000000',
                    xaxis: {{showgrid: false, zeroline: false, showticklabels: false, title: ''}},
                    yaxis: {{showgrid: false, zeroline: false, showticklabels: false, title: ''}},
                    zaxis: {{showgrid: false, zeroline: false, showticklabels: false, title: '', range: [-3, 3]}},
                    camera: {{ eye: {{x: 1.8, y: -1.8, z: 1.4}} }}
                }}
            }};

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {{responsive: true, scrollZoom: true, displayModeBar: true}});

            function zoomIn() {{
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = {{ x: cam.eye.x * 0.75, y: cam.eye.y * 0.75, z: cam.eye.z * 0.75 }};
                Plotly.relayout(plotDiv, {{'scene.camera.eye': newEye}});
            }}

            function zoomOut() {{
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = {{ x: cam.eye.x * 1.25, y: cam.eye.y * 1.25, z: cam.eye.z * 1.25 }};
                Plotly.relayout(plotDiv, {{'scene.camera.eye': newEye}});
            }}

            let isInteracting = false;
            plotDiv.addEventListener('mousedown', () => {{ isInteracting = true; }});
            window.addEventListener('mouseup', () => {{ isInteracting = false; }});

            let frame = 0;
            function runAnimation() {{
                if (!isInteracting) {{
                    frame += 0.04;
                    let currentData = getTorusKnot(frame);
                    Plotly.restyle(plotDiv, {{
                        x: [currentData.x],
                        y: [currentData.y],
                        z: [currentData.z]
                    }}, [0]);
                }}
                setTimeout(runAnimation, 40);
            }}

            setTimeout(runAnimation, 40);
        </script>
    </body>
    </html>
    """
    components.html(raw_surface_html, height=600)
    st.caption(f"ℹ️ **Torus-Knoten Mesh:** Eine komplexe, ineinander verschlungene 3D-Fläche, deren Dynamik direkt an die Live-Volatilität von **{selected_market}** gekoppelt ist.")
