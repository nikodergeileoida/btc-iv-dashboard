import streamlit as st
import streamlit.components.v1 as components
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
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Chart (Candlestick)", "🧊 Aizawa-Attraktor (Sphärisches Chaos)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    base_price = 64255.58
elif asset_class == "US-Märkte":
    market_list = ["S&P 500 (SPY)", "Nasdaq (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    base_price = 450.0
elif asset_class == "Deutsche Märkte (Xetra)":
    market_list = ["DAX Index", "SAP SE", "Siemens", "Allianz"]
    base_price = 18500.0
else:
    market_list = ["Gold (XAUUSD)", "Silver", "Crude Oil", "EUR/USD"]
    base_price = 2400.0

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", market_list)

# Marktstatus-Logik
def get_market_status():
    if "Krypto" in asset_class:
        return "🟢 24/7 Geöffnet (Live)", "Open"
    now_hour = datetime.utcnow().hour
    if "Xetra" in asset_class and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif "US" in asset_class and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    elif "Forex" in asset_class:
        return "🟢 Forex Aktiv", "Open"
    else:
        return "🔴 Markt Geschlossen", "Closed"

status_text, status_flag = get_market_status()

# 3. Haupt-Layout
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Marktstatus", status_text, status_flag)
col2.metric("Ausgewählter Asset", selected_market, "Aktiv")
col3.metric("Modus", view_mode, "Aktiv")

st.divider()

# 4. Ansichten via High-Performance JS-Komponenten
if "Chart" in view_mode:
    st.subheader(f"📈 Candlestick Chart — {selected_market}")
    
    raw_chart_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body { margin: 0; background: #000000; color: white; font-family: sans-serif; }
            #chart-div { width: 100%; height: 580px; background: #000000; }
            .market-badge {
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 16px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="market-badge" id="badge">MARKET_NAME: $BASE_PRICE_VAL (+0.00%)</div>
        <div id="chart-div"></div>
        <script>
            let basePrice = BASE_PRICE_NUM;
            let times = [];
            let opens = [], highs = [], lows = [], closes = [];
            let now = new Date();
            
            for(let i = 40; i >= 0; i--) {
                let d = new Date(now.getTime() - i * 60000);
                times.push(d.toISOString());
                let o = basePrice + (Math.random() - 0.5) * (basePrice * 0.002);
                let c = o + (Math.random() - 0.5) * (basePrice * 0.002);
                let h = Math.max(o, c) + Math.random() * (basePrice * 0.001);
                let l = Math.min(o, c) - Math.random() * (basePrice * 0.001);
                opens.push(o); highs.push(h); lows.push(l); closes.push(c);
                basePrice = c;
            }

            let trace = {
                type: 'candlestick',
                x: times,
                open: opens,
                high: highs,
                low: lows,
                close: closes,
                increasing: { line: { color: '#00ffcc' } },
                decreasing: { line: { color: '#ff0055' } }
            };

            let layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                title: 'Echtzeit-Kursverlauf (MARKET_NAME)',
                dragmode: 'pan',
                xaxis: { 
                    rangeslider: { visible: true }, 
                    gridcolor: '#1a1a1a', 
                    zerolinecolor: '#333',
                    fixedrange: false
                },
                yaxis: { 
                    side: 'right', 
                    tickformat: ',.2f', 
                    gridcolor: '#1a1a1a', 
                    zerolinecolor: '#333',
                    fixedrange: false
                },
                margin: { l: 20, r: 50, b: 20, t: 50 }
            };

            Plotly.newPlot('chart-div', [trace], layout, {
                responsive: true,
                scrollZoom: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['zoom2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
            });

            setInterval(() => {
                let lastIdx = closes.length - 1;
                let tick = (Math.random() - 0.5) * (basePrice * 0.0004);
                closes[lastIdx] += tick;
                highs[lastIdx] = Math.max(highs[lastIdx], closes[lastIdx]);
                lows[lastIdx] = Math.min(lows[lastIdx], closes[lastIdx]);

                let curP = closes[lastIdx];
                let diff = curP - opens[0];
                let pct = (diff / opens[0]) * 100;
                
                let sign = pct >= 0 ? '+' : '';
                document.getElementById('badge').innerText = 'MARKET_NAME: $' + curP.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' (' + sign + pct.toFixed(2) + '%)';

                Plotly.update('chart-div', {
                    close: [closes],
                    high: [highs],
                    low: [lows]
                }, {}, [0]);
            }, 1000);
        </script>
    </body>
    </html>
    """
    
    chart_html = (
        raw_chart_html
        .replace("MARKET_NAME", selected_market)
        .replace("BASE_PRICE_VAL", f"{base_price:,.2f}")
        .replace("BASE_PRICE_NUM", str(base_price))
    )
    
    components.html(chart_html, height=600)
    st.caption("ℹ️ **Tiefschwarzer Live-Chart:** Vollständig freies Verschieben (Pan) und Zoomen per Mausrad/Klick.")

else:
    st.subheader(f"🧊 Aizawa-Attraktor (Sphärisches Chaos) — {selected_market}")
    
    raw_aizawa_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body { margin: 0; background: #000000; color: white; font-family: sans-serif; overflow: hidden; }
            #plotly-div { width: 100%; height: 580px; background: #000000; }
            .market-badge {
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 15px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }
            .zoom-controls {
                position: absolute; top: 10px; right: 15px; z-index: 100;
                display: flex; gap: 5px;
            }
            .zoom-btn {
                background: rgba(20,20,20,0.9); color: #00ffcc; border: 1px solid #333;
                font-family: Arial Black, sans-serif; font-size: 16px; width: 36px; height: 36px;
                border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;
                transition: background 0.2s, border-color 0.2s;
            }
            .zoom-btn:hover { background: rgba(40,40,40,1); border-color: #00ffcc; }
        </style>
    </head>
    <body>
        <div class="market-badge">MARKET_NAME: $BASE_PRICE_VAL (Aizawa Chaos)</div>
        <div class="zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()" title="Hineinzoomen">+</button>
            <button class="zoom-btn" onclick="zoomOut()" title="Herauszoomen">-</button>
        </div>
        <div id="plotly-div"></div>
        <script>
            const a = 0.95;
            const b = 0.7;
            const c = 0.6;
            const d = 3.5;
            const e = 0.25;
            const f = 0.1;
            
            let x = 0.1, y = 0.0, z = 0.0;
            let dt = 0.01;
            
            let x_trail = [], y_trail = [], z_trail = [];
            const maxPoints = 2500;

            for (let i = 0; i < maxPoints; i++) {
                let dx = (z - b) * x - d * y;
                let dy = d * x + (z - b) * y;
                let dz = c + a * z - (Math.pow(z, 3) / 3.0) - (Math.pow(x, 2) + Math.pow(y, 2)) * (1.0 + e * z) + f * z * Math.pow(x, 3);
                x += dx * dt;
                y += dy * dt;
                z += dz * dt;
                x_trail.push(x);
                y_trail.push(y);
                z_trail.push(z);
            }

            const data = [{
                type: 'scatter3d',
                mode: 'lines',
                x: x_trail,
                y: y_trail,
                z: z_trail,
                line: {
                    color: z_trail,
                    colorscale: 'Turbo',
                    width: 3
                }
            }];

            const layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                autosize: true,
                margin: {l: 0, r: 0, b: 0, t: 0},
                scene: {
                    bgcolor: '#000000',
                    xaxis: {showgrid: false, zeroline: false, showticklabels: false, title: ''},
                    yaxis: {showgrid: false, zeroline: false, showticklabels: false, title: ''},
                    zaxis: {showgrid: false, zeroline: false, showticklabels: false, title: ''},
                    camera: { eye: {x: 1.5, y: 1.5, z: 1.2} }
                }
            };

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {responsive: true, scrollZoom: true, displayModeBar: true});

            function zoomIn() {
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = { x: cam.eye.x * 0.75, y: cam.eye.y * 0.75, z: cam.eye.z * 0.75 };
                Plotly.relayout(plotDiv, {'scene.camera.eye': newEye});
            }

            function zoomOut() {
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = { x: cam.eye.x * 1.25, y: cam.eye.y * 1.25, z: cam.eye.z * 1.25 };
                Plotly.relayout(plotDiv, {'scene.camera.eye': newEye});
            }

            let isInteracting = false;
            plotDiv.addEventListener('mousedown', () => { isInteracting = true; });
            window.addEventListener('mouseup', () => { isInteracting = false; });
            plotDiv.addEventListener('touchstart', () => { isInteracting = true; });
            window.addEventListener('touchend', () => { isInteracting = false; });

            function runAnimation() {
                if (!isInteracting) {
                    for(let s = 0; s < 4; s++) {
                        let dx = (z - b) * x - d * y;
                        let dy = d * x + (z - b) * y;
                        let dz = c + a * z - (Math.pow(z, 3) / 3.0) - (Math.pow(x, 2) + Math.pow(y, 2)) * (1.0 + e * z) + f * z * Math.pow(x, 3);
                        x += dx * dt;
                        y += dy * dt;
                        z += dz * dt;
                        
                        x_trail.push(x);
                        y_trail.push(y);
                        z_trail.push(z);
                        
                        if (x_trail.length > maxPoints) {
                            x_trail.shift();
                            y_trail.shift();
                            z_trail.shift();
                        }
                    }

                    Plotly.restyle(plotDiv, {
                        x: [x_trail],
                        y: [y_trail],
                        z: [z_trail],
                        'line.color': [z_trail]
                    }, [0]);
                }
                setTimeout(runAnimation, 40);
            }

            setTimeout(runAnimation, 40);
        </script>
    </body>
    </html>
    """
    
    aizawa_html = (
        raw_aizawa_html
        .replace("MARKET_NAME", selected_market)
        .replace("BASE_PRICE_VAL", f"{base_price:,.2f}")
    )
    
    components.html(aizawa_html, height=600)
    st.caption("ℹ️ **Aizawa-Attraktor (Sphärisches Chaos):** Ein lebendiges, tunnelartiges Strömungsmodell. Nutze die Zoom-Buttons oder drehe das Modell stufenlos per Maus.")
