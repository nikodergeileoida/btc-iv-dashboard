import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
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
st.sidebar.markdown("### 👁️ Ansicht & Engine")
view_mode = st.sidebar.radio("Modus wählen:", [
    "📈 TradingView Live-Terminal", 
    "🕯️ Eigene Kerzen (Custom Python Engine)",
    "🧊 Quanten-Membran (Matt)", 
    "⚡ Beide nebeneinander (Split-View)"
])

# Standardwerte definieren, damit es zu keinem NameError kommt
smoothing = 1
price_offset = 0.0

custom_mode = "Eigene Kerzen" in view_mode or "Split-View" in view_mode
if custom_mode:
    st.sidebar.markdown("### 🛠️ Kerzen-Manipulation")
    smoothing = st.sidebar.slider("Glättungs-Faktor (Smoothing)", 1, 5, 1)
    price_offset = st.sidebar.number_input("Preis-Offset ($)", value=0.0, step=0.5)

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

df_raw, base_price = fetch_market_data(ticker_symbol)

# Eigene Kerzen verarbeiten / manipulieren
if df_raw is not None and not df_raw.empty:
    df_data = df_raw.copy()
    if smoothing > 1:
        df_data['Open'] = df_data['Open'].rolling(window=smoothing).mean()
        df_data['High'] = df_data['High'].rolling(window=smoothing).max()
        df_data['Low'] = df_data['Low'].rolling(window=smoothing).min()
        df_data['Close'] = df_data['Close'].rolling(window=smoothing).mean()
        df_data.dropna(inplace=True)
    
    # Offset anwenden
    df_data['Open'] += price_offset
    df_data['High'] += price_offset
    df_data['Low'] += price_offset
    df_data['Close'] += price_offset
else:
    df_data = None

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

# Hilfsfunktion für TradingView Original-Widget
def get_tradingview_html(symbol):
    tv_symbol_map = {
        "BTC-USD": "BINANCE:BTCUSDT", "ETH-USD": "BINANCE:ETHUSDT", "SOL-USD": "BINANCE:SOLUSDT",
        "BNB-USD": "BINANCE:BNBUSDT", "XRP-USD": "BINANCE:XRPUSDT", "SPY": "AMEX:SPY",
        "QQQ": "NASDAQ:QQQ", "AAPL": "NASDAQ:AAPL", "TSLA": "NASDAQ:TSLA", "NVIDIA": "NASDAQ:NVDA",
        "^GDAXI": "XETR:DAX", "SAP.DE": "XETR:SAP", "SIE.DE": "XETR:SIE", "ALV.DE": "XETR:ALV",
        "GC=F": "COMEX:GC1!", "SI=F": "NYMEX:SI1!", "CL=F": "NYMEX:CL1!", "EURUSD=X": "FX_IDC:EURUSD"
    }
    tv_symbol = tv_symbol_map.get(symbol, "BINANCE:BTCUSDT")
    return f"""
    <!DOCTYPE html>
    <html>
    <head><style>html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }} .tradingview-widget-container {{ width: 100%; height: 100%; }}</style></head>
    <body>
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {{
            "autosize": true, "symbol": "{tv_symbol}", "interval": "D", "timezone": "Etc/UTC",
            "theme": "dark", "style": "1", "locale": "de", "enable_publishing": false,
            "hide_top_toolbar": false, "hide_legend": false, "save_image": false, "calendar": false, "support_host": "https://www.tradingview.com"
          }}
          </script>
        </div>
    </body>
    </html>
    """

# Funktion für Eigene Kerzen (Plotly Pro-Chart)
def render_custom_candles(df, title_text):
    if df is None or df.empty:
        st.warning("Keine Kerzen-Daten verfügbar.")
        return
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='#00F5D4', 
        decreasing_line_color='#F72585'  
    )])
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        title=dict(text=title_text, font=dict(size=14, color='orange'))
    )
    st.plotly_chart(fig, use_container_width=True)

# Hilfsfunktion für Quanten-Membran (3D)
def get_quantum_html(market_name, price, vol_num, vol_str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body {{ margin: 0; background: #000000; overflow: hidden; }}
            #plotly-div {{ width: 100%; height: 580px; }}
            .controls-overlay {{
                position: absolute; top: 10px; left: 15px; z-index: 100;
                display: flex; gap: 10px; align-items: center;
            }}
            .market-badge {{
                font-family: Arial Black, sans-serif; font-size: 13px; color: orange;
                background: rgba(0,0,0,0.9); padding: 5px 10px; border: 1px solid #333; border-radius: 4px;
            }}
            .fs-btn {{
                font-family: Arial, sans-serif; font-size: 12px; color: #fff;
                background: rgba(30,30,30,0.9); padding: 6px 10px; border: 1px solid #555; border-radius: 4px;
                cursor: pointer; transition: background 0.2s;
            }}
            .fs-btn:hover {{ background: rgba(50,50,50,1); border-color: orange; }}
        </style>
    </head>
    <body>
        <div class="controls-overlay">
            <div class="market-badge">{market_name}: ${price} (Vol: {vol_str})</div>
            <button class="fs-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
        </div>
        <div id="plotly-div"></div>
        <script>
            function toggleFullscreen() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{}});
                }} else {{
                    if (document.exitFullscreen) {{ document.exitFullscreen(); }}
                }}
            }}

            const n = 50;
            const vol = {vol_num};

            function getSurface(frame) {{
                let x = [], y = [], z = [];
                for (let i = 0; i < n; i++) {{
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (n - 1)) * 5 - 2.5;
                    for (let j = 0; j < n; j++) {{
                        let v = (j / (n - 1)) * 5 - 2.5;
                        let r = Math.sqrt(u*u + v*v);
                        let wave = Math.sin(r * 2 - frame) * Math.cos(u * 0.8 + frame * 0.4);
                        let pz = Math.abs(wave) * vol * 1.2 + 0.05; 
                        rowX.push(u); rowY.push(v); rowZ.push(pz);
                    }}
                    x.push(rowX); y.push(rowY); z.push(rowZ);
                }}
                return {{ x: x, y: y, z: z }};
            }}

            let initialData = getSurface(0);
            const data = [{{
                type: 'surface',
                x: initialData.x, y: initialData.y, z: initialData.z,
                colorscale: [[0, '#4b0082'], [0.3, '#9400d3'], [0.6, '#ff8c00'], [1, '#ffff00']],
                showscale: false,
                lighting: {{ ambient: 0.6, diffuse: 0.8, specular: 0.05, roughness: 0.95 }}
            }}];

            const layout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#000000', plot_bgcolor: '#000000',
                autosize: true, margin: {{l: 0, r: 0, b: 0, t: 0}},
                scene: {{
                    bgcolor: '#000000',
                    xaxis: {{showgrid: true, zeroline: true, title: 'Strike', gridcolor: '#333', zerolinecolor: '#555'}},
                    yaxis: {{showgrid: true, zeroline: true, title: 'Time', gridcolor: '#333', zerolinecolor: '#555'}},
                    zaxis: {{showgrid: true, zeroline: true, title: 'Volatility', range: [0, 3.5], gridcolor: '#333', zerolinecolor: '#555'}},
                    camera: {{ eye: {{x: 1.6, y: -1.6, z: 1.2}} }}
                }}
            }};

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {{responsive: true, scrollZoom: true}});

            let frame = 0;
            function animate() {{
                frame += 0.02;
                let currentData = getSurface(frame);
                Plotly.restyle(plotDiv, {{ x: [currentData.x], y: [currentData.y], z: [currentData.z] }}, [0]);
                requestAnimationFrame(animate);
            }}
            requestAnimationFrame(animate);
        </script>
    </body>
    </html>
    """

# Volatilitätsfaktor für 3D berechnen
if df_raw is not None and len(df_raw) > 1:
    try:
        volatility_factor = float((df_raw['High'].max() - df_raw['Low'].min()) / base_price * 50)
        volatility_factor = max(0.5, min(volatility_factor, 3.0))
    except Exception:
        volatility_factor = 1.0
else:
    volatility_factor = 1.0

# 4. Ansichten Rendering
if "TradingView Live-Terminal" in view_mode:
    st.subheader(f"📈 TradingView Live-Terminal — {selected_market}")
    components.html(get_tradingview_html(ticker_symbol), height=620, scrolling=False)

elif "Eigene Kerzen" in view_mode:
    st.subheader(f"🕯️ Eigene Kerzen (Custom Python Engine) — {selected_market}")
    render_custom_candles(df_data, f"Custom OHLC Stream — {selected_market}")

elif "Quanten-Membran" in view_mode:
    st.subheader(f"🧊 Quanten-Membran (Matt) — {selected_market}")
    html_content = get_quantum_html(selected_market, f"{base_price:,.2f}", volatility_factor, f"{volatility_factor:.2f}")
    components.html(html_content, height=620)

else:  # Split-View (Beide nebeneinander: Eigene Kerzen + 3D Membran)
    st.subheader(f"⚡ Dual Screen: Eigene Kerzen & Quanten-Membran — {selected_market}")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**🕯️ Eigene Kerzen (Custom)**")
        render_custom_candles(df_data, f"Custom Stream — {selected_market}")
        
    with col_b:
        st.markdown("**🧊 Quanten-Membran (3D)**")
        html_content = get_quantum_html(selected_market, f"{base_price:,.2f}", volatility_factor, f"{volatility_factor:.2f}")
        components.html(html_content, height=580)
