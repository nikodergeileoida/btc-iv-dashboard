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
view_mode = st.sidebar.radio("Modus wählen:", ["📈 TradingView Live-Terminal", "🧊 Quanten-Membran (Matt & Butter-Smooth)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

# Ticker-Mapping für yfinance & TradingView
if asset_class == "Kryptowährungen":
    market_map = {"BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "SOLUSDT": "SOL-USD", "BNBUSDT": "BNB-USD", "XRPUSDT": "XRP-USD"}
elif asset_class == "US-Märkte":
    market_map = {"S&P 500 (SPY)": "SPY", "Nasdaq (QQQ)": "QQQ", "Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA", "NVIDIA (NVDA)": "NVIDIA"}
elif asset_class == "Deutsche Märkte (Xetra)":
    market_map = {"DAX Index": "^GDAXI", "SAP SE": "SAP.DE", "Siemens": "SIE.DE", "Allianz": "ALV.DE"}
else:
    market_map = {"Gold (XAUUSD)": "GC=F", "Silver": "SI=F", "Crude Oil": "CL=F", "EUR/USD": "EURUSD=X"}

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", list(market_map.keys()))
ticker_symbol = market_map[selected_market]

# Echte Daten von Yahoo Finance laden (für die Volatilitäts-Kopplung der 3D-Ansicht)
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

# 4. Ansichten (TradingView Chart vs. 3D Quanten-Membran)
if "TradingView" in view_mode:
    st.subheader(f"📈 TradingView Live-Terminal — {selected_market}")

    tv_symbol_map = {
        "BTC-USD": "BINANCE:BTCUSDT",
        "ETH-USD": "BINANCE:ETHUSDT",
        "SOL-USD": "BINANCE:SOLUSDT",
        "BNB-USD": "BINANCE:BNBUSDT",
        "XRP-USD": "BINANCE:XRPUSDT",
        "SPY": "AMEX:SPY",
        "QQQ": "NASDAQ:QQQ",
        "AAPL": "NASDAQ:AAPL",
        "TSLA": "NASDAQ:TSLA",
        "NVIDIA": "NASDAQ:NVDA",
        "^GDAXI": "XETR:DAX",
        "SAP.DE": "XETR:SAP",
        "SIE.DE": "XETR:SIE",
        "ALV.DE": "XETR:ALV",
        "GC=F": "COMEX:GC1!",
        "SI=F": "NYMEX:SI1!",
        "CL=F": "NYMEX:CL1!",
        "EURUSD=X": "FX_IDC:EURUSD"
    }
    
    tv_symbol = tv_symbol_map.get(ticker_symbol, "BINANCE:BTCUSDT")

    # Perfekt auf Screenshot-Größe optimiert (kein nerviges Scrollen mehr)
    tv_widget_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }}
            .tradingview-widget-container {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "de",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "hide_legend": false,
            "save_image": false,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
          }}
          </script>
        </div>
    </body>
    </html>
    """
    
    components.html(tv_widget_html, height=620, scrolling=False)

else:
    st.subheader(f"🧊 Quanten-Membran (Matt & Butter-Smooth) — {selected_market}")
    
    if df_data is not None and len(df_data) > 1:
        try:
            volatility_factor = float((df_data['High'].max() - df_data['Low'].min()) / base_price * 50)
            volatility_factor = max(0.5, min(volatility_factor, 3.0))
        except Exception:
            volatility_factor = 1.0
    else:
        volatility_factor = 1.0

    raw_surface_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body { margin: 0; background: #000000; overflow: hidden; }
            #plotly-div { width: 100%; height: 600px; }
            .market-badge {
                position: absolute; top: 10px; left: 15px; z-index: 100;
                font-family: Arial Black, sans-serif; font-size: 15px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="market-badge">MARKET_PLACEHOLDER: $PRICE_PLACEHOLDER (Vol: VOL_PLACEHOLDER)</div>
        <div id="plotly-div"></div>
        <script>
            const n = 50;
            const vol = VOL_PLACEHOLDER_NUM;

            function getSurface(frame) {
                let x = [], y = [], z = [];
                for (let i = 0; i < n; i++) {
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (n - 1)) * 5 - 2.5;
                    for (let j = 0; j < n; j++) {
                        let v = (j / (n - 1)) * 5 - 2.5;
                        let r = Math.sqrt(u*u + v*v);
                        
                        let wave = Math.sin(r * 2 - frame) * Math.cos(u * 0.8 + frame * 0.4);
                        let pz = Math.abs(wave) * vol * 1.2 + 0.05; 
                        
                        rowX.push(u);
                        rowY.push(v);
                        rowZ.push(pz);
                    }
                    x.push(rowX);
                    y.push(rowY);
                    z.push(rowZ);
                }
                return { x: x, y: y, z: z };
            }

            let initialData = getSurface(0);

            const data = [{
                type: 'surface',
                x: initialData.x,
                y: initialData.y,
                z: initialData.z,
                colorscale: [
                    [0, '#4b0082'],
                    [0.3, '#9400d3'],
                    [0.6, '#ff8c00'],
                    [1, '#ffff00']
                ],
                showscale: false,
                lighting: { ambient: 0.6, diffuse: 0.8, specular: 0.05, roughness: 0.95 }
            }];

            const layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                autosize: true,
                margin: {l: 0, r: 0, b: 0, t: 0},
                scene: {
                    bgcolor: '#000000',
                    xaxis: {showgrid: true, zeroline: true, title: 'Strike Price', gridcolor: '#333', zerolinecolor: '#555'},
                    yaxis: {showgrid: true, zeroline: true, title: 'Time', gridcolor: '#333', zerolinecolor: '#555'},
                    zaxis: {showgrid: true, zeroline: true, title: 'Volatility', range: [0, 3.5], gridcolor: '#333', zerolinecolor: '#555'},
                    camera: { eye: {x: 1.6, y: -1.6, z: 1.2} }
                }
            };

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {responsive: true, scrollZoom: true});

            let frame = 0;
            function animate() {
                frame += 0.02;
                let currentData = getSurface(frame);
                Plotly.restyle(plotDiv, {
                    x: [currentData.x],
                    y: [currentData.y],
                    z: [currentData.z]
                }, [0]);
                requestAnimationFrame(animate);
            }
            requestAnimationFrame(animate);
        </script>
    </body>
    </html>
    """.replace("MARKET_PLACEHOLDER", selected_market).replace("PRICE_PLACEHOLDER", f"{base_price:,.2f}").replace("VOL_PLACEHOLDER_NUM", str(volatility_factor)).replace("VOL_PLACEHOLDER", f"{volatility_factor:.2f}")

    components.html(raw_surface_html, height=620)
    st.caption(f"ℹ️ **Quanten-Membran:** Exakte Höhe für **{selected_market}** ohne Scrollen.")
