import streamlit as st
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime, timedelta

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
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Chart (Candlestick)", "🧊 3D Surface"])

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

# Session State für stabile Kursdaten
if "market_data" not in st.session_state or st.session_state.get("current_market") != selected_market:
    np.random.seed(sum(map(ord, selected_market)))
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(40, 0, -1)]
    
    opens, highs, lows, closes = [], [], [], []
    curr = base_price
    for _ in timestamps:
        o = curr
        c = o + np.random.randn() * (base_price * 0.001)
        h = max(o, c) + abs(np.random.randn() * (base_price * 0.0005))
        l = min(o, c) - abs(np.random.randn() * (base_price * 0.0005))
        opens.append(o)
        highs.append(h)
        lows.append(l)
        closes.append(c)
        curr = c
        
    st.session_state.market_data = {
        "times": timestamps,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes
    }
    st.session_state.current_market = selected_market

data = st.session_state.market_data
current_price = data["closes"][-1]
price_diff = current_price - data["opens"][0]
diff_percent = (price_diff / data["opens"][0]) * 100

# 3. Haupt-Layout
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
col2.metric("Marktstatus", status_text, status_flag)
col3.metric("Ausgewählter Asset", selected_market, "Aktiv")

st.divider()

# 4. Ansichten
if "Chart" in view_mode:
    st.subheader(f"📈 Candlestick Chart — {selected_market}")
    
    fig_candle = go.Figure(data=[go.Candlestick(
        x=data["times"],
        open=data["opens"],
        high=data["highs"],
        low=data["lows"],
        close=data["closes"]
    )])
    
    fig_candle.update_layout(
        template="plotly_dark",
        title=f"Echtzeit-Kursverlauf ({selected_market})",
        xaxis_rangeslider_visible=True,
        dragmode='pan',  # Nur Verschieben beim Halten, kein Zoom-Kasten!
        height=600,
        margin=dict(l=20, r=50, b=20, t=50)
    )
    
    fig_candle.update_yaxes(side="right", tickformat=",.2f", fixedrange=False)
    fig_candle.update_xaxes(fixedrange=False)
    
    fig_candle.add_annotation(
        text=f"{selected_market}: ${current_price:,.2f} ({diff_percent:+.2f}%)",
        xref="paper", yref="paper",
        x=0.98, y=0.95,
        showarrow=False,
        font=dict(size=16, color="orange", family="Arial Black"),
        bgcolor="rgba(0,0,0,0.8)",
        bordercolor="gray",
        borderwidth=1
    )

    # Entfernt Zoom-Box-Tools aus der Toolbar komplett
    st.plotly_chart(
        fig_candle, 
        use_container_width=True, 
        config={
            'scrollZoom': True, 
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['zoom2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
        },
        key="candlestick_final_v3"
    )
    st.caption("ℹ️ **TradingView-Modus:** Klicken & Ziehen verschiebt den Chart butterweich. Mausrad zum Zoomen.")

else:
    st.subheader(f"🧊 3D Volatility Surface — {selected_market}")
    
    # Durchgehende, asymmetrische High-Volatility Live-Animation per JS Component
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body {{ margin: 0; background: #0e1117; color: white; font-family: sans-serif; }}
            #plotly-div {{ width: 100%; height: 580px; }}
            .market-badge {{
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 16px; color: orange;
                background: rgba(0,0,0,0.8); padding: 5px 10px; border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="market-badge">{selected_market}: ${current_price:,.2f} ({diff_percent:+.2f}%)</div>
        <div id="plotly-div"></div>
        <script>
            const n = 40;
            let x = [], y = [];
            for(let i=0; i<n; i++) {{
                x.push(-3 + (i / (n-1)) * 6);
                y.push(-3 + (i / (n-1)) * 6);
            }}
            
            let X = [], Y = [], Z0 = [];
            for (let i = 0; i < n; i++) {{
                let rowX = [], rowY = [], rowZ = [];
                for (let j = 0; j < n; j++) {{
                    let xi = x[j];
                    let yj = y[i];
                    rowX.push(xi);
                    rowY.push(yj);
                    let skew = 0.3 * xi;
                    let smile = 0.25 * (xi * xi) + 0.15 * (yj * yj);
                    rowZ.push(Math.max(0.2, 1.2 + smile - skew));
                }}
                X.push(rowX);
                Y.push(rowY);
                Z0.push(rowZ);
            }}

            const data = [{{
                z: Z0,
                x: X,
                y: Y,
                type: 'surface',
                colorscale: 'Viridis'
            }}];

            const layout = {{
                template: 'plotly_dark',
                autosize: true,
                margin: {{l: 0, r: 0, b: 0, t: 0}},
                scene: {{
                    xaxis: {{title: 'Strike Price (Skew)', backgroundcolor: 'black', gridcolor: '#333'}},
                    yaxis: {{title: 'Time to Maturity', backgroundcolor: 'black', gridcolor: '#333'}},
                    zaxis: {{title: 'Implied Volatility', range: [0.2, 3.2], backgroundcolor: 'black', gridcolor: '#333'}},
                    camera: {{ eye: {{x: 1.6, y: -1.6, z: 1.3}} }}
                }}
            }};

            Plotly.newPlot('plotly-div', data, layout, {{responsive: true, scrollZoom: true, displayModeBar: true}});

            let frame = 0;
            function runAnimation() {{
                frame += 0.05;
                let Z = [];
                for (let i = 0; i < n; i++) {{
                    let rowZ = [];
                    for (let j = 0; j < n; j++) {{
                        let xi = X[i][j];
                        let yj = Y[i][j];
                        // Asymmetrischer Volatility-Smile mit hoher Amplitude & Dynamik
                        let skew = 0.3 * xi;
                        let smile = 0.28 * (xi * xi) + 0.18 * (yj * yj);
                        let wave = 0.4 * Math.sin(xi * 0.9 - frame) * Math.cos(yj * 0.7 + frame);
                        let z = 1.4 + smile - skew + wave;
                        rowZ.push(Math.max(0.2, z));
                    }}
                    Z.push(rowZ);
                }}
                
                Plotly.animate('plotly-div', {{
                    data: [{{z: Z}}],
                    traces: [0],
                    layout: {{}}
                }}, {{
                    transition: {{duration: 40, easing: 'linear'}},
                    frame: {{duration: 40, redraw: true}}
                }});
                
                requestAnimationFrame(runAnimation);
            }

            requestAnimationFrame(runAnimation);
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=600)
    st.caption("ℹ️ **Live 3D-Volatilität:** Läuft vollautomatisch, flüssig, asymmetrisch und ohne Button-Klicks. Du kannst das Modell jederzeit mit der Maus drehen.")
