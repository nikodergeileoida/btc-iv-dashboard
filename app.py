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
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Chart (Candlestick)", "🧊 4D Tesseract (Hypercube)"])

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
    st.subheader(f"🧊 4D Tesseract (Hypercube) — {selected_market}")
    
    raw_tesseract_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body { margin: 0; background: #000000; color: white; font-family: sans-serif; }
            #plotly-div { width: 100%; height: 580px; background: #000000; }
            .market-badge {
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 16px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="market-badge">MARKET_NAME: $BASE_PRICE_VAL (4D Hypercube Rotation)</div>
        <div id="plotly-div"></div>
        <script>
            // 16 Eckpunkte eines 4D-Hyperwürfels generieren
            let vertices = [];
            for (let i = 0; i < 16; i++) {
                vertices.push([
                    (i & 1) ? 1 : -1,
                    (i & 2) ? 1 : -1,
                    (i & 4) ? 1 : -1,
                    (i & 8) ? 1 : -1
                ]);
            }

            // 32 Kanten definieren (Eckpunkte, die sich um exakt 1 Koordinate unterscheiden)
            let edges = [];
            for (let i = 0; i < 16; i++) {
                for (let j = i + 1; j < 16; j++) {
                    let diff = 0;
                    for (let k = 0; k < 4; k++) {
                        if (vertices[i][k] !== vertices[j][k]) diff++;
                    }
                    if (diff === 1) {
                        edges.push([i, j]);
                    }
                }
            }

            function getProjectedCoordinates(angle) {
                let projected_vertices = [];
                for (let i = 0; i < 16; i++) {
                    let v = [...vertices[i]];
                    
                    // 4D Rotation in der XW-Ebene
                    let x = v[0], w = v[3];
                    let cosA = Math.cos(angle), sinA = Math.sin(angle);
                    let x1 = x * cosA - w * sinA;
                    let w1 = x * sinA + w * cosA;
                    
                    // 4D Rotation in der YW-Ebene
                    let y = v[1];
                    let y1 = y * cosA - w1 * sinA;
                    let w2 = y * sinA + w1 * cosA;
                    
                    let z = v[2];
                    
                    // Perspektivische Projektion von 4D nach 3D
                    let distance = 2.5;
                    let w_factor = 1 / (distance - w2);
                    
                    projected_vertices.push([
                        x1 * w_factor * 1.8,
                        y1 * w_factor * 1.8,
                        z * w_factor * 1.8
                    ]);
                }

                let x_coords = [], y_coords = [], z_coords = [];
                for (let edge of edges) {
                    let p1 = projected_vertices[edge[0]];
                    let p2 = projected_vertices[edge[1]];
                    x_coords.push(p1[0], p2[0], null);
                    y_coords.push(p1[1], p2[1], null);
                    z_coords.push(p1[2], p2[2], null);
                }
                return { x: x_coords, y: y_coords, z: z_coords };
            }

            let initialCoords = getProjectedCoordinates(0);

            const data = [{
                type: 'scatter3d',
                mode: 'lines',
                x: initialCoords.x,
                y: initialCoords.y,
                z: initialCoords.z,
                line: { color: '#00ffcc', width: 5 }
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
                    camera: { eye: {x: 1.5, y: -1.5, z: 1.2} }
                }
            };

            Plotly.newPlot('plotly-div', data, layout, {responsive: true, scrollZoom: true, displayModeBar: true});

            let isInteracting = false;
            let plotDiv = document.getElementById('plotly-div');

            plotDiv.addEventListener('mousedown', () => { isInteracting = true; });
            window.addEventListener('mouseup', () => { isInteracting = false; });
            plotDiv.addEventListener('touchstart', () => { isInteracting = true; });
            window.addEventListener('touchend', () => { isInteracting = false; });

            let frame = 0;
            function runAnimation() {
                if (!isInteracting) {
                    frame += 0.025;
                    let coords = getProjectedCoordinates(frame);
                    Plotly.restyle('plotly-div', {
                        x: [coords.x],
                        y: [coords.y],
                        z: [coords.z]
                    }, [0]);
                }
                setTimeout(runAnimation, 40);
            }

            setTimeout(runAnimation, 40);
        </script>
    </body>
    </html>
    """
    
    tesseract_html = (
        raw_tesseract_html
        .replace("MARKET_NAME", selected_market)
        .replace("BASE_PRICE_VAL", f"{base_price:,.2f}")
    )
    
    components.html(tesseract_html, height=600)
    st.caption("ℹ️ **4D Tesseract:** Ein vierdimensionaler Hyperwürfel, der live rotiert und in den 3D-Raum projiziert wird. Du kannst das Modell jederzeit mit der Maus frei drehen und zoomen.")
