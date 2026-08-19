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

if "chart_counter" not in st.session_state:
    st.session_state.chart_counter = 0

data = st.session_state.market_data

# 3. Haupt-Layout
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)

# 4. Ansichten
if "Chart" in view_mode:
    @st.fragment(run_every=1.0)
    def render_live_candlestick():
        # Live-Tick auf den letzten Kurs anwenden
        tick_change = np.random.randn() * (base_price * 0.0004)
        data["closes"][-1] += tick_change
        data["highs"][-1] = max(data["highs"][-1], data["closes"][-1])
        data["lows"][-1] = min(data["lows"][-1], data["closes"][-1])
        
        st.session_state.chart_counter += 1
        
        current_price = data["closes"][-1]
        price_diff = current_price - data["opens"][0]
        diff_percent = (price_diff / data["opens"][0]) * 100

        col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
        col2.metric("Marktstatus", status_text, status_flag)
        col3.metric("Ausgewählter Asset", selected_market, "Aktiv")
        
        st.divider()
        st.subheader(f"📈 Candlestick Chart — {selected_market}")

        fig_candle = go.Figure(data=[go.Candlestick(
            x=list(data["times"]),
            open=list(data["opens"]),
            high=list(data["highs"]),
            low=list(data["lows"]),
            close=list(data["closes"])
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

        st.plotly_chart(
            fig_candle, 
            use_container_width=True, 
            config={
                'scrollZoom': True, 
                'displayModeBar': True,
                'modeBarButtonsToRemove': ['zoom2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
            },
            key=f"candlestick_live_{st.session_state.chart_counter}"
        )
        st.caption("ℹ️ **Live-Feed Aktiv:** Der Chart aktualisiert sich sekündlich. Klicken & Ziehen verschiebt den Chart butterweich.")

    render_live_candlestick()

else:
    current_price = data["closes"][-1]
    price_diff = current_price - data["opens"][0]
    diff_percent = (price_diff / data["opens"][0]) * 100

    col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
    col2.metric("Marktstatus", status_text, status_flag)
    col3.metric("Ausgewählter Asset", selected_market, "Aktiv")
    
    st.divider()
    st.subheader(f"🧊 3D Volatility Surface — {selected_market}")
    
    # Vollständig tiefschwarzer Hintergrund mit RESTYLE (Kamera bleibt absolut frei & ungesperrt)
    raw_html = """
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
        <div class="market-badge">MARKET_NAME: $PRICE_VAL (PCT_VAL)</div>
        <div id="plotly-div"></div>
        <script>
            const n = 40;
            let x = [], y = [];
            for(let i=0; i<n; i++) {
                x.push(-3 + (i / (n-1)) * 6);
                y.push(-3 + (i / (n-1)) * 6);
            }
            
            let X = [], Y = [], Z0 = [];
            for (let i = 0; i < n; i++) {
                let rowX = [], rowY = [], rowZ = [];
                for (let j = 0; j < n; j++) {
                    let xi = x[j];
                    let yj = y[i];
                    rowX.push(xi);
                    rowY.push(yj);
                    let skew = 0.3 * xi;
                    let smile = 0.28 * (xi * xi) + 0.18 * (yj * yj);
                    rowZ.push(Math.max(0.2, 1.4 + smile - skew));
                }
                X.push(rowX);
                Y.push(rowY);
                Z0.push(rowZ);
            }

            const data = [{
                z: Z0,
                x: X,
                y: Y,
                type: 'surface',
                colorscale: 'Viridis'
            }];

            const layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                autosize: true,
                margin: {l: 0, r: 0, b: 0, t: 0},
                scene: {
                    bgcolor: '#000000',
                    xaxis: {title: 'Strike Price (Skew)', backgroundcolor: '#000000', gridcolor: '#222', zerolinecolor: '#444'},
                    yaxis: {title: 'Time to Maturity', backgroundcolor: '#000000', gridcolor: '#222', zerolinecolor: '#444'},
                    zaxis: {title: 'Implied Volatility', range: [0.2, 3.2], backgroundcolor: '#000000', gridcolor: '#222', zerolinecolor: '#444'},
                    camera: { eye: {x: 1.6, y: -1.6, z: 1.3} }
                }
            };

            Plotly.newPlot('plotly-div', data, layout, {responsive: true, scrollZoom: true, displayModeBar: true});

            let frame = 0;
            function runAnimation() {
                frame += 0.05;
                let Z = [];
                for (let i = 0; i < n; i++) {
                    let rowZ = [];
                    for (let j = 0; j < n; j++) {
                        let xi = X[i][j];
                        let yj = Y[i][j];
                        let skew = 0.3 * xi;
                        let smile = 0.28 * (xi * xi) + 0.18 * (yj * yj);
                        let wave = 0.4 * Math.sin(xi * 0.9 - frame) * Math.cos(yj * 0.7 + frame);
                        let z = 1.4 + smile - skew + wave;
                        rowZ.push(Math.max(0.2, z));
                    }
                    Z.push(rowZ);
                }
                
                // Restyle aktualisiert NUR die Daten (Z), sodass die Kamera-Position des Users 100% frei bleibt!
                Plotly.restyle('plotly-div', {z: [Z]}, [0]);
                
                setTimeout(runAnimation, 40);
            }

            requestAnimationFrame(runAnimation);
        </script>
    </body>
    </html>
    """
    
    html_code = (
        raw_html
        .replace("MARKET_NAME", selected_market)
        .replace("$PRICE_VAL", f"${current_price:,.2f}")
        .replace("PCT_VAL", f"{diff_percent:+.2f}%")
    )
    
    components.html(html_code, height=600)
    st.caption("ℹ️ **Tiefschwarzes 3D-Modell (Kamera frei):** Die Kamera rastet nicht mehr ein – du kannst das Modell jederzeit frei drehen und zoomen.")
